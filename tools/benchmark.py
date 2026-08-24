import json
import statistics
import sys
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, ".")

from satprep.core.ability import AbilityEstimator
from satprep.core.blueprint import BlueprintModel
from satprep.core.framework import SECTION_RW
from satprep.core.rng import derive_seed


def bench_blueprints(n=200):
    model = BlueprintModel(kappa=400.0)
    times = []
    for i in range(n):
        t0 = time.perf_counter()
        model.draw(27, section=SECTION_RW, seed=i)
        times.append((time.perf_counter() - t0) * 1000)
    return times


def bench_fit(n_items=100, n_runs=200):
    est = AbilityEstimator()
    import random
    rng = random.Random(7)
    items = [(rng.uniform(0.8, 1.6), rng.uniform(-2, 2)) for _ in range(n_items)]
    u = [1 if rng.random() < 0.6 else 0 for _ in range(n_items)]
    times = []
    for _ in range(n_runs):
        t0 = time.perf_counter()
        est.fit(items, u)
        times.append((time.perf_counter() - t0) * 1000)
    return times


class MicroServer:
    def __init__(self):
        import socket
        from satprep.api.server import AppState, Handler
        from http.server import ThreadingHTTPServer
        self.app = AppState(db_path=":memory:")
        Handler.app = self.app
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        sock.close()
        self.server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
        self.base = f"http://127.0.0.1:{port}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.app.close()


def http_call(base, method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + path, data=data, method=method)
    if data:
        req.add_header("Content-Type", "application/json")
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=30) as r:
        r.read()
    return (time.perf_counter() - t0) * 1000


def bench_http_burst(base, workers=20, per_worker=15):
    latencies = []
    errors = []

    def worker(w):
        for _ in range(per_worker):
            try:
                ms = http_call(base, "GET", "/api/meta/framework")
                latencies.append(ms)
            except Exception as e:
                errors.append(str(e))

    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(worker, range(workers)))
    return latencies, errors


def bench_practice_burst(base, workers=8, length=5):
    latencies = []
    errors = []

    def worker(w):
        try:
            data = json.dumps({"name": f"perf-{w}"}).encode()
            req = urllib.request.Request(base + "/api/users", data=data,
                                         method="POST")
            req.add_header("Content-Type", "application/json")
            created = json.loads(urllib.request.urlopen(req, timeout=30).read())
            uid = created["user"]["user_id"]

            start_body = json.dumps({"user_id": uid, "section": "math",
                                     "length": length}).encode()
            req = urllib.request.Request(base + "/api/practice",
                                         data=start_body, method="POST")
            req.add_header("Content-Type", "application/json")
            sess = json.loads(urllib.request.urlopen(req, timeout=30).read())
            sid = sess["session_id"]

            for i in range(length):
                if i:
                    req = urllib.request.Request(
                        base + f"/api/sessions/{sid}/next", method="GET")
                    urllib.request.urlopen(req, timeout=30).read()
                t0 = time.perf_counter()
                ans = json.dumps({"choice_index": 1}).encode()
                req = urllib.request.Request(
                    base + f"/api/sessions/{sid}/answer", data=ans,
                    method="POST")
                req.add_header("Content-Type", "application/json")
                urllib.request.urlopen(req, timeout=30).read()
                latencies.append((time.perf_counter() - t0) * 1000)
        except Exception as e:
            errors.append(str(e))

    t_start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(worker, range(workers)))
    wall = (time.perf_counter() - t_start) * 1000
    return latencies, errors, wall


def summarize(name, times):
    if not times:
        print(f"{name:38} NO SAMPLES")
        return
    times_sorted = sorted(times)
    p50 = times_sorted[len(times_sorted) // 2]
    p95 = times_sorted[int(len(times_sorted) * 0.95)]
    print(f"{name:38} n={len(times):4}  "
          f"mean={statistics.mean(times):7.2f}ms  "
          f"p50={p50:7.2f}ms  p95={p95:7.2f}ms  max={max(times):7.2f}ms")


if __name__ == "__main__":
    print("== core model latency ==")
    summarize("blueprint.draw (RW module, 27q)", bench_blueprints())
    summarize("ability.fit (100 items)", bench_fit(100))
    summarize("ability.fit (300 items)", bench_fit(300))

    print()
    print("== http server ==")
    srv = MicroServer()
    try:
        read_lat, read_err = bench_http_burst(srv.base, workers=20, per_worker=15)
        summarize(f"GET /api/meta/framework x{len(read_lat)} (20 thr)",
                  read_lat)
        print(f"{'  errors':38} {len(read_err)}")

        wlat, werr, wall = bench_practice_burst(srv.base, workers=8, length=5)
        summarize("POST answer (40 answers, 8 users)", wlat)
        print(f"{'  wall clock for 8 full sessions':38} {wall:7.0f}ms   "
              f"errors: {len(werr)}")
        for e in (read_err + werr)[:5]:
            print(f"  sample error: {e}")
    finally:
        srv.close()

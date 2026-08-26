# TutorSat: Architecture

> **Disclaimer.** Independent educational project. Not affiliated with, endorsed by, or
> connected to College Board in any way. SAT® is a registered trademark of College Board.
> No College Board question content is included or reproduced; all questions are
> originally authored templates and all framework percentages are author-encoded
> approximations of publicly documented digital SAT specifications.

## 1. Stack decision (and why)

| Layer      | Choice                                   | Justification |
|------------|------------------------------------------|---------------|
| Core models| Python 3.10+, **stdlib only**            | The statistical core must be auditable; pure stdlib (`math`, `random`, `hashlib`) keeps it dependency-free and deterministic. |
| Tests      | `unittest` (stdlib)                      | Zero-install test runner: `python -m unittest discover -s tests`. |
| Persistence| SQLite via stdlib `sqlite3`              | Single-file DB, real SQL, trivially portable to Postgres later (see §7). |
| API        | stdlib `http.server.ThreadingHTTPServer` | JSON-over-HTTP without any framework dependency; one process serves API + static frontend. |
| Frontend   | Vanilla HTML/CSS/JS (no build step)      | The brief favors correctness of the core over UI polish; a build chain adds risk, not value, here. |

**Major deviation from "suggested stack": none.** This follows the "stdlib-preferred"
option exactly. If you prefer a TS/Node stack, only `api/server.py` and `web/app.js`
would change: core modules have no I/O and no framework coupling.

## 2. Repository layout

```
sat-adaptive-prep-engine/
├── ARCHITECTURE.md              # this file
├── README.md                    # setup, live site, disclaimers
├── DESIGN.md                    # UI design system: tokens, bracket/tick grammar, motion rules
├── run.py                       # entry point: starts API + static server on :8765
│
├── tools/
│   ├── content_audit.py         # generates N items per skill×tier; reports uniqueness + structural validity
│   └── benchmark.py             # model latency + HTTP load benchmarks (numbers recorded below)
│
├── satprep/
│   ├── __init__.py
│   ├── core/                    # ── STAGE-2 CORE MODELS (pure math, no I/O) ──
│   │   ├── __init__.py
│   │   ├── framework.py         # structured digital-SAT reference data: sections → domains → skills + weights + difficulty profiles (author-encoded)
│   │   ├── rng.py               # deterministic seed derivation (string → int seed → random.Random streams)
│   │   ├── blueprint.py         # MODEL 1: statistical blueprint sampler over the framework tree, fixed module lengths
│   │   └── ability.py           # MODEL 2: per-skill ability estimator (item-response-theory based) driving adaptive selection
│   │
│   ├── questions/               # ── QUESTION GENERATION LAYER ──
│   │   ├── __init__.py
│   │   ├── base.py              # Question dataclass (text, choices, answer index, explanation, a/b params, skill, difficulty)
│   │   ├── math_gen.py          # parametrized original Math generators per skill × difficulty band (algebra, advanced math, data, geometry/trig)
│   │   ├── rw_gen.py            # parametrized original R&W generators per skill × difficulty band (original micro-passages/sentences, never CB content)
│   │   └── bank.py             # slot-filling facade: blueprint cell → generator → concrete Question; max-information ordering
│   │
│   ├── engine/                  # ── ORCHESTRATION ──
│   │   ├── __init__.py
│   │   ├── session.py           # practice session: request → blueprint → adaptive item serving → θ updates → summary
│   │   └── mocktest.py          # full-length timed mock: module 1 per section → performance branch → easy/medium/hard-leaning module 2
│   │
│   ├── scoring/
│   │   ├── __init__.py
│   │   └── scale.py             # θ → estimated section score band (piecewise-linear calibration, documented heuristic)
│   │
│   ├── storage/
│   │   ├── __init__.py
│   │   └── db.py                # SQLite persistence: users, theta_state, sessions, responses, generated items
│   │
│   └── api/
│       ├── __init__.py
│       └── server.py            # ThreadingHTTPServer: JSON routes under /api/*, static files from web/, single DB lock
│
├── web/                         # ── FRONTEND (no build step) ──
│   ├── index.html               # SPA shell: practice / dashboard / mock views
│   ├── styles.css               # styling
│   └── app.js                   # fetch-based client, view router, canvas charts for θ trends
│
└── tests/                       # ── unittest suites ──
    ├── __init__.py
    ├── test_rng_seeding.py      # determinism + stream independence of seed derivation
    ├── test_blueprint.py        # MODEL 1: exact lengths, reproducibility, prior fidelity, posterior shift, apportionment correctness
    ├── test_ability.py          # MODEL 2: monotonicity, symmetry, convergence, recovery-by-simulation, information function shape
    ├── test_bank_generators.py  # every framework skill fillable; answers correct by construction; unique choices
    ├── test_session_engine.py   # practice sessions, adaptive ordering, branching thresholds, mock assembly, scoring sanity
    ├── test_hardening.py        # Phase 2 edge cases: extreme θ, seed-reuse regression, concurrent writes + double-submit race, missed-log, domain breakdowns, bank dedup
    └── test_api_db.py           # store round-trips + HTTP round-trips against a live server thread
```

## 2.1 Phase 2 notes (full-propagation & hardening)

- **Bank dedup**: `QuestionBank.fill_blueprint` carries a per-session `avoid` set;
  generators are reseeded deterministically (bounded attempts) rather than repeating
  a prompt within one session. Finite R&W template pools therefore never show
  duplicates inside a session unless the pool is genuinely smaller than the request.
- **Content depth**: all 29 skill generators audited via `tools/content_audit.py`
  (40 draws × skill × tier). Math uniqueness 62–100%, zero structural defects
  (choices always 4 unique, answer index always valid). Authored-pool sizes for
  Reading & Writing were expanded ~2×; remaining repetition across *sessions* is an
  accepted, documented tradeoff of original-authored content.
- **Concurrency**: `AppState.lock` now guards every mutating route including mock
  answers (a double-submit race was found and fixed in Phase 2). SQLite writes are
  serialized behind one connection lock; reads run on `ThreadingHTTPServer` threads.
- **Measured performance** (`tools/benchmark.py`, Windows dev box):
  - `BlueprintModel.draw` (27-q RW module): mean **0.08 ms**, p95 0.12 ms
  - `AbilityEstimator.fit` MAP: mean **0.50 ms** @100 items, **1.56 ms** @300 items
  - HTTP burst, 20 threads × 15 GETs: 0 errors, p50 8.8 ms, p95 79 ms, max ~1.3 s
    (thread-spawn/GIL tail: honest limitation of stdlib ThreadingHTTPServer)
  - 8 concurrent users × full 5-question practice sessions: 40/40 answers OK,
    answer POST p50 11.6 ms / p95 36 ms
  Conclusion: the statistical core is never the bottleneck; the deployment target
  is local/classroom single-process use, not horizontal multi-user production.
- **Session resumability policy**: active sessions/mocks live in server memory;
  completed summaries and every response persist to SQLite. A server restart ends
  in-flight sessions deliberately (documented in README); a client refresh resumes
  cleanly because `/next` is idempotent while a question is pending.

## 3. Data flow

```
                 framework.py (static weights)
                        │  composition prior
                        ▼
 user request ──► blueprint.py ──► Blueprint (exact counts per domain×skill×difficulty×module)
                        │                    │
                        │                    ▼
 current θ (per skill) ─┼────► bank.py ──► Questions fill slots (max-information first)
                        │                    │
                        ▼                    ▼
                 ability.py ◄──── responses (u ∈ {0,1}, a, b per answered item)
                        │
                        ▼
             updated θ̂ ± sd  ──► storage/db.py ──► dashboard / score band / next-item selection
```

## 4. Model 1: Blueprint composition

A statistical sampler over the framework tree decides what each session
contains.

- **State space**: leaves of the framework tree = `(section, domain, skill, difficulty)` cells.
  Framework percentages define weights, normalized over whichever subset a session needs.
- **Sampling**: a Bayesian categorical model blends published proportions with
  observed session history, so draws stay near the documented mix while
  responding to usage.
- **Fixed counts**: fractional expectations are apportioned to integers so counts
  sum to *exactly* N (27/module R&W, 22/module Math).
- Everything seeded through `rng.derive_seed` ⇒ byte-reproducible blueprints.

## 5. Model 2: Ability estimation & adaptive selection

- Each learner carries one ability estimate per skill, updated after every
  response under a standard item-response-theory response model.
- Estimation is exact and fast (closed-form gradients, safeguarded iterative
  solve), with a prior that keeps estimates finite for all-correct/all-wrong runs.
- Item selection serves the unanswered item that is most informative at the
  learner's current estimate, concentrating difficulty near their level.
- Module-2 branching mirrors digital-SAT adaptivity: module-1 percent-correct maps
  to an easy-/balanced-/hard-leaning difficulty profile for module 2.
- Item parameters start from a neutral prior and are re-estimated from real
  response data once items accumulate enough responses (see
  `satprep/calibration/`).

## 6. Stage-1 assumptions (explicitly stated, not blocking)

1. **Framework numbers are author-encoded approximations** of publicly documented specs
   (e.g., R&W ≈ CS 28% / II 26% / SEC 26% / EI 20%; Math ≈ Algebra 35% / Advanced 35% /
   PSDA 15% / Geo-Trig 15%). Skill-level splits within domains are reasonable estimates.
2. **Difficulty mix priors are assumptions** (documented in `core/framework.py`).
   Real mixes are proprietary.
3. **Score scaling** θ→200–800 is a documented piecewise-linear heuristic, not College
   Board's equating.
4. **Accounts**: local profiles are anonymous localStorage ids by default.
   Optional Google Sign-In is implemented (`api/google_auth.py`): with
   `GOOGLE_CLIENT_ID` set, ID tokens are verified server-side (RS256 against
   Google's JWKS via pure big-integer RSA, plus iss/aud/exp/sub enforcement)
   and subjects map to stable `g-*` accounts; without it the feature is inert.
5. **R&W items are generated from original micro-passages/sentence frames** written for
   this repo; they exercise the named skills but are stylistically simpler than exam items.
6. Concurrency: one process, one SQLite connection guarded by a lock: sufficient for local use.

## 7. Scaling path

**Deployment constraint (read first):** the classic surface keeps active
sessions and mocks in process memory, so it is **single-instance**: one process
per SQLite file, behind a TLS reverse proxy. Do not run stateless replicas
behind a load balancer; the app will appear healthy while users lose in-flight
tests. Step-by-step deployment guides live in `DEPLOYMENT.md` (Dockerfile,
docker-compose, systemd unit, and Caddy/nginx configs are bundled in `deploy/`).

**Stateless escape hatch:** for ephemeral-disk hosts, `/api/x/*` implements the
client-held-state variant (`engine/stateless.py`): a signed JSON blob rides
every request, the server is a pure function of (state, request), and nothing
touches disk. Feasible only because θ estimation is order-invariant and item
generation fully seeded - both tested properties of the core. Caps: 300
sessions / 5000 responses per blob; tamper detection warns via `meta.tampered`
instead of blocking. Secret: `SATPREP_STATELESS_SECRET`.

- Postgres: swap `storage/db.py` (thin DAO surface already isolated). This is
  also the prerequisite for multi-replica deployments.
- Multi-user/auth: Google Sign-In ships in the box (see assumption 4); a full
  token-authenticated multi-user deployment would add session middleware around
  the existing per-user learners and stores. Engine layers unchanged.
- Question bank at scale: `bank.py` is a facade over generators; a cached pre-generated
  bank with dedup hashing can replace on-demand generation behind the same interface.

# DEPLOYMENT.md: taking the engine to a real server

This guide turns the repo into a running deployment. Supported paths:

| Path | Best for | Cost | TLS |
|------|----------|------|-----|
| A. Docker Compose | Any VPS; easiest updates and rollback | VPS cost | Add Caddy/nginx in front (configs included) or terminate at your edge |
| B. Bare metal + systemd | Servers without Docker | VPS cost | Caddy (automatic) or nginx + certbot |
| C. Dockerfile platforms (Fly.io, Railway, Render, Cloud Run) | Fastest first deploy | Free tiers vary, see caveats | Provided by the platform |
| D. Free-forever stacks (no card) | Students/hobbyists: PythonAnywhere alone, or Cloudflare Pages frontend (recommended) + free backend | $0 | Included (`*.pages.dev`, `*.web.app`, `*.pythonanywhere.com`) |
| E. Stateless API on ephemeral hosts | Render free / Cloud Run / any spin-down host with no writable disk | $0 tiers | Platform-provided |

## 0. What you are deploying

One process, zero Python dependencies, one SQLite file:

```
browser ──TLS──► reverse proxy ──► python run.py (ThreadingHTTPServer)
                                        │
                                        └── /data/satprep.db (SQLite)
```

Honest capacity notes, measured in `ARCHITECTURE.md`:

- The statistical core is effectively free (sub-millisecond draws and fits).
- The stdlib HTTP layer handled 300 concurrent requests with zero errors in
  benchmarks, but shows latency tail under synthetic bursts. This is a great
  single-server deployment for an individual, family, or classroom.
- **Single-instance only**: practice sessions and mocks live in process memory.
  Do not run multiple replicas behind a load balancer. Scaling past one node
  means moving session state out of memory first (see ARCHITECTURE.md §7).
- Anyone who can reach the site can create profiles and answer questions. If
  that is not acceptable for your deployment, use the proxy-level access
  control shown below, or rely on Google Sign-In being present (note: it is
  frictionless identity, not an authorization gate).

## 1. Pre-flight decisions

1. **Domain + DNS**: point `satprep.example.com` at your server.
2. **Data location**: where should `satprep.db` live? Pick a persistent path
   (`/var/lib/satprep` or a mounted volume). Everything the app remembers is
   in that one file.
3. **Google Sign-In?** Optional. If yes, add your final origin(s) to the OAuth
   client's *Authorized JavaScript origins* (`https://satprep.example.com`,
   plus `http://localhost:8765` for development). Only the client ID is needed
   on the server; there is no client secret in this flow.

## 2. Path A: Docker Compose (recommended)

```bash
git clone <your-fork-url> satprep && cd satprep

# optional Google Sign-In:
echo "GOOGLE_CLIENT_ID=xxxx.apps.googleusercontent.com" > .env

docker compose up -d --build
curl http://127.0.0.1:8765/api/health     # {"status": "ok"}
```

Notes:

- The container binds to `127.0.0.1:8765`, so only the host (and your proxy)
  can reach it. To expose directly instead, change the mapping to
  `"8765:8765"` and put your own TLS in between.
- SQLite lives in `./data/satprep.db` on the host: back up by copying that
  file.
- Updates: `git pull && docker compose up -d --build`.

### Adding TLS with the bundled Caddy config

Install Caddy on the host, then:

```bash
sudo cp deploy/Caddyfile /etc/caddy/Caddyfile   # edit the domain name first
sudo systemctl reload caddy
```

Caddy obtains/renews certificates automatically and proxies to
`127.0.0.1:8765`. An equivalent `deploy/nginx.conf.example` is included.

## 3. Path B: bare metal + systemd

```bash
sudo useradd --system satprep
sudo mkdir -p /opt/satprep /var/lib/satprep
sudo rsync -a ./ /opt/satprep/ --exclude data --exclude .git
sudo chown -R satprep:satprep /opt/satprep /var/lib/satprep

# optional sign-in:
echo 'GOOGLE_CLIENT_ID=xxxx.apps.googleusercontent.com' \
  | sudo tee /etc/satprep.env

sudo cp deploy/satprep.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now satprep
systemctl status satprep
journalctl -u satprep -f          # logs
```

The unit runs the app on loopback with `ProtectSystem=strict`; only
`/var/lib/satprep` is writable. Put Caddy or nginx (configs in `deploy/`) in
front for TLS.

Python version: any 3.10+ interpreter works; there are no packages to install.

## 4. Path C: Dockerfile platforms

The repo root contains a plain `Dockerfile`, so Fly.io, Railway, Render,
Google Cloud Run, and similar platforms detect it automatically.

- Set `GOOGLE_CLIENT_ID` in the platform's environment settings.
- Mount a persistent volume at `/data` if the platform supports it (Fly
  volumes do; some free tiers have ephemeral disks that will wipe progress
  data on redeploy). On ephemeral platforms, either accept the data loss or
  swap `storage/db.py` for Postgres (the DAO surface is small, see
  ARCHITECTURE.md §7).

Free-tier caveats, checked honestly: Render free services spin down after
inactivity **and** wipe their disk on restart, which destroys progress data;
Railway's free tier is a one-time trial credit; Fly.io retired its free
allowance for new users. For a genuinely $0, always-on deployment use Path D.

## 4b. Path D: free-forever stacks ($0, no credit card)

The repo ships a WSGI entrypoint (`wsgi.py`) exposing the full application
(API + static frontend) to any WSGI host. That unlocks the truly-free options
below. Both keep SQLite on a persistent disk; both give you HTTPS on the
provider's domain.

Pick by upkeep tolerance (frontend URL is cosmetic and swappable later):

| Combo | Frontend | Backend | Upkeep | Card |
|-------|----------|---------|--------|------|
| D2-a | Cloudflare Pages `.pages.dev` | PythonAnywhere free | one click / ~3 months | no |
| D2-b | Cloudflare Pages `.pages.dev` | Oracle Always Free VM (D1-alt) | none, ever | signup only |
| D1 | none (single origin on PA) | PythonAnywhere free | one click / ~3 months | no |

### D1: PythonAnywhere hosts everything (simplest)

One service, one origin, no CORS, no build step.

1. Create a free account at pythonanywhere.com; your site will live at
   `https://YOURNAME.pythonanywhere.com`.
2. In a Bash console: `git clone <your-fork-url> ~/satprep`
3. Web tab > Add new web app > Manual configuration > Python 3.10.
4. Set the source directory to `/home/YOURNAME/satprep`.
5. Edit the WSGI configuration file and replace its contents with:

   ```python
   import os, sys
   sys.path.insert(0, "/home/YOURNAME/satprep")
   os.chdir("/home/YOURNAME/satprep")

   # Optional Google Sign-In:
   # os.environ["GOOGLE_CLIENT_ID"] = "xxxx.apps.googleusercontent.com"

   from wsgi import app as application
   ```

6. Click Reload. Done: `https://YOURNAME.pythonanywhere.com` serves the app.

Notes:
- No virtualenv required; there are zero dependencies.
- The database is `/home/YOURNAME/satprep/satprep.db`; back it up from the
  Files tab or a scheduled console task.
- Free web apps require a one-click "extend" on the dashboard every 3 months.
  If you forget: the site suspends, but files and the database are retained;
  one click revives everything. Set a recurring reminder (~10 weeks) if you
  will not visit regularly, or choose the unattended path below.
- Google Sign-In verification fetches Google's JWKS over the network; outbound
  HTTPS from free accounts goes through a whitelist proxy that includes
  googleapis.com domains. Local profiles work regardless.

### D1-alt: unattended free backend (Oracle Cloud Always Free)

If periodic clicks are a non-starter, Oracle's Always Free tier gives you a
small VM that runs indefinitely with no human input (a card is required only
to create the account):

1. Create the VM (Ubuntu image; an `VM.Standard.A1.Flex` shape with 1-4 OCPUs
   falls inside Always Free) and download the SSH key.
2. Open ingress for TCP 80 and 443 in the VCN security list (this is separate
   from the OS firewall and is the step people most often miss).
   Alternative: skip port-opening entirely with a Cloudflare Tunnel - install
   `cloudflared` on the VM, `cloudflared tunnel create satprep`, route your
   hostname to `http://localhost:80`, and run it as a systemd service. Traffic
   then flows outbound through Cloudflare with TLS at their edge.
3. Reserve a public IP and point your domain's A record at it (skip if using
   the Tunnel; point a CNAME at the tunnel hostname instead).
4. Install Docker + Caddy (`apt install docker.io docker-compose-plugin caddy`),
   then run the Path A commands verbatim: clone, optional `.env`,
   `docker compose up -d --build`, install the bundled `deploy/Caddyfile`
   with your domain.

After setup there is nothing to click: certificates renew themselves, the
container restarts on reboot (`restart: unless-stopped`), and backups remain
your only recurring duty.

### D2: Static-host frontend (Cloudflare Pages recommended) + free backend

If you want a cleaner public URL than `YOURNAME.pythonanywhere.com`, serve the
static frontend from Cloudflare Pages and keep the Python backend hidden as
the API engine room. Users see `https://YOURPROJECT.pages.dev`; browsers call
the backend cross-origin via the CORS support built into the server. Firebase
Hosting (`.web.app`) is a drop-in alternative at step 4.

1. Deploy the backend exactly as in D1.
2. Allow your frontend origin for CORS. Append to the PA WSGI file:

   ```python
   os.environ["SATPREP_ALLOWED_ORIGINS"] = "https://satprep.pages.dev"
   ```

3. Build the frontend folder:

   ```bash
   mkdir site && cp -r web/* site/
   echo 'window.SATPREP_API_BASE = "https://YOURNAME.pythonanywhere.com";' \
     > site/config.js
   ```

   (`config.js` overrides the default shipped copy; API calls then target the
   backend origin.)

4. Deploy the folder - pick whichever static host you prefer:

   **Cloudflare Pages (zero tooling, recommended):**
   dash.cloudflare.com > Workers & Pages > Create > Pages > Upload assets >
   drag the `site/` folder. Live at `https://PROJECT.pages.dev`. For
   push-to-deploy instead: connect the Git repo, set output directory to
   `site` and leave the build command empty.

   **Firebase Hosting:**

   ```bash
   npm install -g firebase-tools
   firebase login
   firebase init hosting     # public directory: site; single-page app: no
   firebase deploy           # -> https://PROJECT.web.app
   ```

   GitHub Pages also works by pushing `site/` to a `gh-pages` branch.

5. If using Google Sign-In, add the **frontend** origin to the OAuth client's
   Authorized JavaScript origins; the backend verifies tokens, so it needs no
   origin setting beyond the CORS entry above.

#### Why not go all-in on Cloudflare?

Workers (always-on, free) plus D1 (SQLite-as-a-service) looks like a perfect
match for this codebase, but Workers run JavaScript: shipping there means
porting the entire statistical core and all 29 question generators to
TypeScript and maintaining that fork forever. Cloudflare's Python Workers are
beta (Pyodide-based) and cannot reach D1 natively. Until a rewrite is a goal
in itself, pair Cloudflare Pages (frontend) with an always-on Python backend
from D1/D1-alt.

### D3: Oracle Cloud Always Free VPS

Oracle's Always Free tier includes small VMs that are yours forever (card
required only at signup). Run Path A unchanged: docker compose + bundled
Caddy config on your domain. This is the strongest free option if you want
full control and already have a domain.

## 4c. Path E: ephemeral hosts via the stateless API

Path E pairs naturally with any static host from Path D2: for example,
**Firebase Hosting (`*.web.app`) frontend + Render Free backend** is a fully
supported $0 combination - set `SATPREP_ALLOWED_ORIGINS` to the `.web.app`
origin on the backend, point `config.js` at the Render URL, and deploy per
both sections below.

For hosts with no writable disk (Render free, Cloud Run, Vercel functions),
the server exposes a second, database-free surface under `/api/x/*` built on
the client-held-state architecture: the client stores one signed JSON blob in
`localStorage` and sends it with every request; the server recomputes
everything (blueprints from seeds, θ from the response log) and returns an
updated blob. Nothing touches disk.

Setup:

1. Choose a long random secret and set it so blobs are HMAC-signed:
   `SATPREP_STATELESS_SECRET=<64+ random chars>` (or `--stateless-secret`).
   Unsigned mode works but is discouraged publicly.
2. Set `SATPREP_ALLOWED_ORIGINS` to your frontend origin as in Path D.
3. Point `config.js` at the host; the frontend's API base applies unchanged.

Routes mirror v1: `POST /api/x/practice/start`, `/api/x/session/{next,answer,
summary}`, `/api/x/mocks/{start,state,answer}`, `/api/x/dashboard`, plus
`GET /api/x/capabilities`. Every mutating response carries `{state, meta}`;
persist `state` after each call.

Honest constraints:

- The blob rides every request; fine at practice volumes, hard-capped at 300
  sessions / 5000 responses (server replies 413 beyond that rather than
  truncating silently).
- History lives per-browser. Cross-device continuity needs a sync layer
  (Google Drive scope is the planned option); Google Sign-In alone does not
  move the blob.
- Tamper detection is warn-not-block by design: a mismatched signature sets
  `meta.tampered = true` on the response so UIs can flag modified histories
  without locking anyone out.
- The bundled SPA auto-detects the stateless surface via
  `GET /api/x/capabilities` and switches its practice/mock/dashboard calls to
  `/api/x/*`, persisting the signed blob in `localStorage`
  (`satprep_x_blob`). A "Reset saved progress" action in the About dialog
  erases it.

## 5. Configuration reference

| Setting | Flag | Env var | Default |
|---------|------|---------|---------|
| Listen host | `--host` | none | `127.0.0.1` |
| Listen port | `--port` | none | `8765` |
| Database file | `--db` | none | `./satprep.db` |
| Google client ID | `--google-client-id` | `GOOGLE_CLIENT_ID` | unset |
| CORS origins (split deploys) | `--allowed-origins` | `SATPREP_ALLOWED_ORIGINS` | empty (CORS off) |
| DB path for WSGI entrypoint | none | `SATPREP_DB` | `./satprep.db` |

Behind a reverse proxy keep `--host 127.0.0.1`; never expose the raw process
directly to the internet. On WSGI hosts (Path D) there is no flag parsing:
configure everything through the environment variables above, set inside the
WSGI file if the host has no env editor.

## 6. Backups and restore

Everything persists to one SQLite file. Safe backup on a live server:

```bash
sqlite3 /var/lib/satprep/satprep.db ".backup '/backups/satprep-$(date +%F).db'"
```

(Or stop the service/container briefly and copy the file.) Restore = stop,
replace the file, start. A nightly cron of the `.backup` command plus
off-machine copy is plenty for this workload.

Schema migrations: v1 creates tables with `CREATE TABLE IF NOT EXISTS` only;
upgrades so far are additive. Still: take a backup before upgrading.

## 7. Security checklist before going public

- [ ] TLS enabled (Caddy automatic, certbot for nginx) and HTTP redirects to HTTPS
- [ ] App bound to `127.0.0.1`; only the proxy is internet-facing
- [ ] Decision made about open registration (proxy basic-auth / IP allowlist /
      accept-open)
- [ ] Google authorized origins updated to the deployed URL (if using Sign-In)
- [ ] Optional proxy rate limiting enabled (e.g., Caddy `rate_limit` plugin or
      nginx `limit_req`)
- [ ] Backup cron configured and restore tested once
- [ ] `X-Content-Type-Options`/HSTS headers set (bundled configs include them)

## 8. Troubleshooting

| Symptom | Likely cause / fix |
|---------|--------------------|
| Health check fails after start | Port already in use: change `--port`, or another instance holds 8765 |
| `database is locked` in logs | Two processes pointed at the same DB file; run exactly one instance per file |
| Google button does not appear | `GOOGLE_CLIENT_ID` not visible to the process (check `EnvironmentFile` / compose env) |
| Google button appears, sign-in fails with origin error | Deployed URL missing from OAuth client's Authorized JavaScript origins |
| Data vanished after platform redeploy | Ephemeral filesystem; mount `/data` or move to Postgres |
| Browser console shows CORS errors on the split setup | Frontend origin missing from `SATPREP_ALLOWED_ORIGINS`, or backend reloaded after editing the WSGI file without clicking Reload |
| PythonAnywhere app stops working after ~3 months | Free web apps need a dashboard click to extend; site pauses but data is retained, see Path D1 note (or switch to D1-alt for unattended hosting) |
| Oracle VM unreachable from internet | Ports 80/443 not opened in the VCN security list (distinct from OS firewall); see D1-alt step 2 |

"use strict";

const state = {
  user: null,
  framework: null,
  view: "home",
  thetaMap: {},
  googleClientId: null,
  x: false,
};

const mockUI = {
  moduleStarts: {},
  introSeen: {},
};

const $view = document.getElementById("view");
const $nav = document.getElementById("nav");
const $chip = document.getElementById("user-chip-slot");
const $calibration = document.getElementById("calibration");

function esc(value) {
  return String(value).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

const KA_BASE_MATH =
  "https://www.khanacademy.org/test-prep/v2-sat-math/x0fcc98a58ba3bea7:";
const KA_BASE_RW =
  "https://www.khanacademy.org/test-prep/sat-reading-and-writing/x0d47bcec73eb6c4b:";

const MATH_DOMAIN_SLUGS = {
  algebra: "algebra",
  psda: "problem-solving-and-data-analysis",
  advanced_math: "advanced-math",
  geometry_trig: "geometry-and-trigonometry",
};

const RW_GROUP_SLUGS = {
  info_ideas: "information-and-ideas",
  craft_structure: "craft-and-structure",
  expression_ideas: "expression-of-ideas-and-standard-english-conventions",
  std_conventions: "expression-of-ideas-and-standard-english-conventions",
};

const TIER_SUFFIX = { easy: "easier", medium: "medium", hard: "harder" };
const TIER_PREFIX = {
  easy: "foundations", medium: "medium", hard: "advanced",
};

const DEFAULT_LINKS = {};
for (const [dom, slug] of Object.entries(MATH_DOMAIN_SLUGS)) {
  for (const tier of ["easy", "medium", "hard"]) {
    DEFAULT_LINKS[`math|${dom}|${tier}`] =
      `${KA_BASE_MATH}${slug}-${TIER_SUFFIX[tier]}`;
  }
}
for (const [dom, slug] of Object.entries(RW_GROUP_SLUGS)) {
  for (const tier of ["easy", "medium", "hard"]) {
    DEFAULT_LINKS[`rw|${dom}|${tier}`] =
      `${KA_BASE_RW}${TIER_PREFIX[tier]}-${slug}`;
  }
}

function practiceLink(row) {
  const overrides = window.SATPREP_LINKS || {};
  const key = `${row.section}|${row.domain_id}|${row.tier}`;
  return overrides[key] || DEFAULT_LINKS[key] || null;
}

const API_BASE = (window.SATPREP_API_BASE || "").replace(/\/+$/, "");

const X_BLOB_KEY = "satprep_x_blob";
const ACCT_KEY = "satprep_accounts";
let tamperShown = false;

function getAccounts() {
  try {
    return JSON.parse(localStorage.getItem(ACCT_KEY)) || [];
  } catch (e) {
    return [];
  }
}

function saveAccounts(list) {
  localStorage.setItem(ACCT_KEY, JSON.stringify(list));
}

function upsertAccount(id, name, provider) {
  const list = getAccounts().filter((a) => a.id !== id);
  list.push({ id, name: name || "Student", provider,
              used: Date.now(), added: Date.now() });
  saveAccounts(list);
}

function removeAccountEntry(id) {
  saveAccounts(getAccounts().filter((a) => a.id !== id));
}

function sortedAccounts() {
  return getAccounts().slice().sort((a, b) => {
    const au = a.provider === "google" ? 0 : 1;
    const bu = b.provider === "google" ? 0 : 1;
    return (au - bu) || (b.used - a.used);
  });
}

function findAccount(id) {
  return getAccounts().find((a) => a.id === id) || null;
}

function guestCount() {
  return getAccounts().filter((a) => a.provider !== "google").length;
}

function xBlobKey(id) {
  return "satprep_x_blob_" + (id || localStorage.getItem("satprep_uid")
                              || "local");
}

function migrateLegacyBlob() {
  const legacy = localStorage.getItem(X_BLOB_KEY);
  if (!legacy) return;
  localStorage.removeItem(X_BLOB_KEY);
  let blob = null;
  try { blob = JSON.parse(legacy); } catch (e) { return; }
  const owner = (blob && blob.user_id) || "local";
  const key = "satprep_x_blob_" + owner;
  if (!localStorage.getItem(key)) localStorage.setItem(key, legacy);
  if (!getAccounts().some((a) => a.id === owner)) {
    upsertAccount(owner,
      (localStorage.getItem("satprep_name") &&
       owner === "local") ? localStorage.getItem("satprep_name")
        : "Guest", owner.startsWith("g-") ? "google" : "local");
  }
}

function loadXBlob(forId) {
  const raw = localStorage.getItem(xBlobKey(forId));
  try {
    return raw ? JSON.parse(raw) : null;
  } catch (e) {
    return null;
  }
}

function saveXBlob(blob) {
  if (!blob) return;
  const id = blob.user_id || localStorage.getItem("satprep_uid") || "local";
  localStorage.setItem(xBlobKey(id), JSON.stringify(blob));
}

function noteTamper(meta) {
  if (meta && meta.tampered && !tamperShown) {
    tamperShown = true;
    let banner = document.getElementById("tamper-banner");
    if (!banner) {
      banner = document.createElement("div");
      banner.id = "tamper-banner";
      banner.className = "error-box";
      banner.style.position = "sticky";
      banner.style.top = "0";
      banner.style.zIndex = "60";
      document.body.prepend(banner);
    }
    banner.textContent = "This history was modified outside the app. " +
      "Scores may not reflect actual practice. Editing your save file is " +
      "permitted: it is personal practice data, not an official record.";
  }
}

async function xApi(path, body) {
  const merged = { ...(body || {}) };
  const blob = loadXBlob();
  if (blob) merged.state = blob;
  const res = await api("POST", path, merged);
  if (res.state !== undefined) saveXBlob(res.state);
  noteTamper(res.meta);
  return res;
}

async function api(method, path, body) {
  const options = { method, headers: {} };
  if (body !== undefined) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }
  const res = await fetch(API_BASE + path, options);
  let data = {};
  try { data = await res.json(); } catch (e) { /* empty body */ }
  if (!res.ok) {
    throw new Error(data.error || `${res.status} ${res.statusText}`);
  }
  return data;
}

function setView(view) {
  if (state.view === "mock" && view !== "mock") {
    clearInterval(window.mockTimerHandle);
  }
  state.view = view;
  render();
}

/* ---------------- calibration strip ---------------- */

function fmtTheta(theta, sd) {
  const t = (theta >= 0 ? "+" : "−") + Math.abs(theta).toFixed(2);
  return sd != null ? `${t} ± ${sd.toFixed(2)}` : t;
}

function calItem(label, valueHtml, optional) {
  return `<span class="cal-item${optional ? " cal-optional" : ""}">` +
    `${label}&nbsp;<b>${valueHtml}</b></span>`;
}

function thetaMapStats() {
  const rows = Object.values(state.thetaMap).filter((r) => r.attempts > 0);
  if (!rows.length) return null;
  const attempts = rows.reduce((s, r) => s + r.attempts, 0);
  const mean = rows.reduce((s, r) => s + r.theta * r.attempts, 0) / attempts;
  return { attempts, mean };
}

function calTicksTrack(filled, total) {
  // Resolved design decision (Phase 2 §1): the calibration strip's tick row is
  // functional, not decorative. It renders answered-item progress for the ACTIVE
  // session only, filling left to right; ticks compress inside a fixed-width
  // track as counts grow (capped by CSS overflow, never scrolled mid-read).
  // On screens with no live session the row is omitted entirely rather than
  // rendered empty, honoring the "nothing decorative" rule.
  if (!total) return "";
  const cells = [];
  for (let i = 0; i < total; i++) {
    cells.push(`<i class="${i < filled ? "on" : ""}"></i>`);
  }
  return `<span class="cal-ticks" aria-hidden="true">${cells.join("")}</span>`;
}

function renderCalibration(pulseTheta) {
  let html = "";

  if (state.view === "practice") {
    const ps = window.practiceState;
    if (ps) {
      html += calTicksTrack(ps.answered, ps.total_questions);
      html += calItem("SEED", esc(ps.seed));
      const q = window.practiceUI && window.practiceUI.current;
      if (q) {
        const row = state.thetaMap[q.skill_id];
        const thetaHtml =
          `<span class="theta-val${pulseTheta ? " pulse" : ""}">` +
          `${row ? esc(fmtTheta(row.theta, row.posterior_sd)) : "-"}</span>`;
        html += calItem("SKILL", esc(skillName(q.skill_id)), true);
        html += calItem("θ", thetaHtml);
        html += calItem("ITEM", `${ps.answered}/${ps.total_questions}`, true);
      }
    }
  } else if (state.view === "mock" && window.mockState && !window.mockState.complete) {
    const spot = mockCurrentModule();
    if (spot) {
      const answeredInModule =
        spot.mod.questions.filter((x) => x.answered).length;
      html += calTicksTrack(answeredInModule, spot.mod.questions.length);
      html += calItem("SECTION", sectionName(spot.secId).toUpperCase(), true);
      html += calItem("MODULE", `${spot.mod.index}/2`);
      html += `<span class="cal-spacer"></span>`;
      html += `<span class="cal-item"><span id="module-timer">--:--</span></span>`;
    }
    if (window.mockState.seed) {
      html += calItem("SEED", esc(window.mockState.seed), true);
    }
  } else {
    const stats = thetaMapStats();
    if (stats) {
      html += calItem("MEAN θ", fmtTheta(stats.mean));
      html += calItem("RESPONSES", String(stats.attempts));
      const measured = Object.values(state.thetaMap)
        .filter((r) => r.attempts > 0).length;
      html += calItem("SKILLS MEASURED", String(measured), true);
    } else {
      html += calItem("CALIBRATION", "no data: answer items to begin");
    }
  }

  $calibration.innerHTML = html;
}

/* ---------------- chrome ---------------- */

function renderNav() {
  const items = [
    ["home", "Home"],
    ["practice-setup", "Practice"],
    ["mock", "Full Mock"],
    ["dashboard", "Dashboard"],
  ];
  $nav.innerHTML = items.map(([id, label]) =>
    `<button class="nav-btn${state.view === id ? " active" : ""}"
      data-view="${id}" ${state.user ? "" : 'disabled title="Create a profile first"'}>${label}</button>`
  ).join("");
  $nav.querySelectorAll(".nav-btn").forEach((b) =>
    b.addEventListener("click", () => setView(b.dataset.view)));
}

function renderChip() {
  if (!state.user) {
    $chip.innerHTML = "";
    return;
  }
  const label = state.user.provider === "google" ? "sign out" : "switch user";
  $chip.innerHTML =
    `<span class="name" title="${esc(state.user.name)}">${esc(state.user.name)}</span>` +
    `<button id="logout-btn">${label}</button>`;
  document.getElementById("logout-btn").addEventListener("click", () => {
    openAccountPanel();
  });
}

function showError(message) {
  const box = document.createElement("div");
  box.className = "error-box";
  box.textContent = `Error: ${message}`;
  $view.prepend(box);
  setTimeout(() => box.remove(), 6000);
}

function showNotice(message) {
  const box = document.createElement("div");
  box.className = "empty-note";
  box.style.borderColor = "var(--signal)";
  box.style.color = "var(--signal)";
  box.textContent = message;
  $view.prepend(box);
  setTimeout(() => box.remove(), 5000);
}

function render() {
  renderNav();
  renderChip();
  renderCalibration(false);
  if (!state.user) return renderOnboarding();
  switch (state.view) {
    case "practice-setup": return renderPracticeSetup();
    case "practice": return renderPractice();
    case "mock": return renderMock();
    case "dashboard": return renderDashboard();
    default: return renderHome();
  }
}

/* ---------------- shared helpers ---------------- */

function skillName(skillId) {
  for (const sec of state.framework.sections)
    for (const dom of sec.domains)
      for (const sk of dom.skills)
        if (sk.skill_id === skillId) return sk.name;
  return skillId;
}

function sectionName(secId) {
  return secId === "rw" ? "Reading & Writing" : "Math";
}

function domainShort(domainId) {
  const map = {
    algebra: "Algebra",
    psda: "Problem Solving & Data",
    advanced_math: "Advanced Math",
    geometry_trig: "Geometry & Trig",
    craft_structure: "Craft & Structure",
    info_ideas: "Information & Ideas",
    std_conventions: "Conventions",
    expression_ideas: "Expression of Ideas",
  };
  return map[domainId] || domainId;
}

function profileLabel(profile) {
  return { easy_leaning: "Easier", balanced: "Standard",
           hard_leaning: "Harder" }[profile] || profile;
}

function scaleBandHTML(low, high, compact) {
  const ticks = [];
  for (let v = 200; v <= 800; v += 100) {
    ticks.push(`<i style="left:${((v - 200) / 600) * 100}%"></i>`);
  }
  const left = ((low - 200) / 600) * 100;
  const width = ((high - low) / 600) * 100;
  return `
    <div class="scale${compact ? " compact" : ""}">
      <span class="endpt">200</span>
      <div class="axis">${ticks.join("")}
        <div class="range-mark" style="left:${left}%;width:${width}%"></div>
      </div>
      <span class="endpt">800</span>
    </div>
    <div class="scale-caption"><span class="mono">${low}–${high}</span>${compact ? "" : " estimated band"}</div>`;
}

function sparklineSVG(history, width = 130, height = 30) {
  if (!history || history.length < 2) {
    return "";
  }
  const pts = history.map((t, i) => {
    const x = (i / (history.length - 1)) * (width - 2) + 1;
    const y = height - 2 -
      ((Math.max(-2.5, Math.min(2.5, t)) + 2.5) / 5) * (height - 4);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");
  return `<svg class="sparkline" width="${width}" height="${height}">
    <polyline points="${pts}" fill="none" style="stroke:var(--signal)" stroke-width="1.5"/>
  </svg>`;
}

/* ---------------- onboarding ---------------- */

function renderOnboarding() {
  $view.innerHTML = `
    <div class="panel">
      <p class="panel-kicker">Adaptive testing instrument</p>
      <h2>TutorSat</h2>
      <p>This engine builds every session from two statistical models:
      a Dirichlet\u2013multinomial blueprint over the digital-SAT framework
      and a per-skill 2-parameter-logistic IRT ability tracker that adapts
      question selection to you in real time.</p>
      <div class="field">
        <label for="name-input">Your name</label>
        <input type="text" id="name-input" placeholder="e.g. Alex" maxlength="60">
      </div>
      <div class="btn-row"><button class="btn-commit" id="create-user">Create profile</button></div>
      ${state.googleClientId ? `
        <div class="or-divider"><span>or</span></div>
        <div class="gsi-slot" id="gsi-slot"></div>` : ""}
      <p class="muted mono" style="font-size:.7rem;margin-top:16px;">
        Independent project \u00b7 not affiliated with College Board \u00b7 SAT\u00ae is a College Board trademark</p>
    </div>`;
  document.getElementById("create-user").addEventListener("click", async () => {
    const name = document.getElementById("name-input").value.trim() || "Student";
    try {
      if (state.x) {
        if (!state.user && guestCount() > 0) {
          throw new Error("A guest profile already exists on this browser. " +
            "Open ACCOUNT to switch to it, or delete it first.");
        }
        state.user = { user_id: "local", name };
        localStorage.setItem("satprep_uid", "local");
        localStorage.setItem("satprep_name", name);
        const blob = loadXBlob();
        if (blob) {
          blob.user_id = "local";
          saveXBlob(blob);
        }
        upsertAccount("local", name, "local");
        await loadThetaMap();
        setView("home");
        return;
      }
      if (guestCount() > 0 && !state.user) {
        throw new Error("A guest profile already exists on this browser. " +
          "Open ACCOUNT to switch to it, or delete it first.");
      }
      const data = await api("POST", "/api/users", { name });
      upsertAccount(data.user.user_id,
        data.user.name || name, "local");
      setUser(data.user);
      setView("home");
    } catch (err) {
      showError(err.message);
    }
  });
  if (state.x) {
    const nameLabel = document.querySelector('label[for="name-input"]');
    if (nameLabel) {
      nameLabel.textContent = "Your name (profile stays in this browser)";
    }
  }
  if (state.googleClientId) renderGoogleButton();
}

async function setUser(user) {
  state.user = user;
  localStorage.setItem("satprep_uid", user.user_id);
  upsertAccount(user.user_id, user.name || "Student",
    user.provider === "google" || user.user_id.startsWith("g-")
      ? "google" : "local");
  await loadThetaMap();
  render();
}

let gsiPromise = null;

function loadGsiScript() {
  if (window.google && window.google.accounts) return Promise.resolve();
  if (gsiPromise) return gsiPromise;
  gsiPromise = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.onload = resolve;
    script.onerror = () => reject(new Error("could not load Google Sign-In"));
    document.head.appendChild(script);
  });
  return gsiPromise;
}

function renderGoogleButton() {
  const slot = document.getElementById("gsi-slot");
  if (!slot) return;
  loadGsiScript().then(() => {
    if (!slot.isConnected || !window.google?.accounts?.id) return;
    window.google.accounts.id.initialize({
      client_id: state.googleClientId,
      callback: handleGoogleCredential,
      auto_select: false,
    });
    window.google.accounts.id.renderButton(slot, {
      theme: "outline",
      size: "large",
      shape: "rectangular",
      text: "signin_with",
      width: 280,
    });
  }).catch((err) => showError(err.message));
}

function askMergeChoice(sessions) {
  return new Promise((resolve) => {
    $view.innerHTML = `
      <div class="panel">
        <p class="panel-kicker">Google sign-in</p>
        <h2>Link your local progress?</h2>
        <p>This browser holds <span class="mono">${sessions}</span> session(s)
        of unclaimed practice history. Linking moves it under your Google
        account so it follows you across devices.</p>
        <div class="btn-row">
          <button type="button" class="btn-commit" id="merge-yes">Yes, link it</button>
          <button type="button" class="btn-quiet" id="merge-no">No, start fresh</button>
        </div>
      </div>`;
    document.getElementById("merge-yes").onclick = () => resolve(true);
    document.getElementById("merge-no").onclick = () => resolve(false);
  });
}

async function handleGoogleCredential(response) {
  const prevUid = localStorage.getItem("satprep_uid");
  try {
    let merged = null;
    let userPayload = null;
    if (prevUid && prevUid.startsWith("u-")) {
      const probe = await api("POST", "/api/auth/link/probe",
        { local_user_id: prevUid });
      if (probe.user_exists && probe.sessions > 0 &&
          await askMergeChoice(probe.sessions)) {
        const linkResult = await api("POST", "/api/auth/link",
          { credential: response.credential, local_user_id: prevUid });
        userPayload = linkResult.user;
        merged = linkResult.moved_sessions;
      }
    }
    if (!userPayload) {
      const data = await api("POST", "/api/auth/google",
        { credential: response.credential });
      userPayload = data.user;
    }
    await setUser({ ...userPayload, provider: "google" });
    setView("home");
    if (merged != null && merged > 0) {
      showError(`Linked ${merged} session(s) to your Google account.`);
      const box = $view.querySelector(".error-box");
      if (box) {
        box.style.borderColor = "var(--signal)";
        box.style.color = "var(--signal)";
      }
    }
  } catch (err) {
    showError(err.message);
  }
}

async function loadThetaMap() {
  if (state.x) {
    state.thetaMap = {};
    const blob = loadXBlob();
    for (const [sid, v] of Object.entries((blob && blob.theta) || {})) {
      state.thetaMap[sid] = {
        skill_id: sid, theta: v.est, posterior_sd: v.sd,
        attempts: v.n, correct: v.correct, history: v.history || [],
      };
    }
    return;
  }
  try {
    const data = await api("GET", `/api/users/${state.user.user_id}`);
    state.thetaMap = {};
    for (const row of data.theta || []) {
      state.thetaMap[row.skill_id] = row;
    }
  } catch (e) {
    state.thetaMap = {};
  }
}

/* ---------------- home ---------------- */

function modePanel(id, kicker, title, blurb, readoutSlot, goLabel, extra) {
  return `
    <button class="panel mode-panel" id="${id}">
      <p class="panel-kicker">${kicker}</p>
      <h2>${title}</h2>
      <p class="muted mode-blurb">${blurb}</p>
      <p class="readout-line" id="${readoutSlot}">reading calibration…</p>
      ${extra || ""}
      <span class="mode-go">${goLabel} &#8594;</span>
    </button>`;
}

function renderHome() {
  $view.innerHTML = `
    <div class="panel-grid">
      ${modePanel("go-practice", "Mode 01", "Adaptive Practice",
        "Blueprint-mixed sessions · information-maximizing items",
        "home-practice-readout", "Start adaptive practice")}
      ${modePanel("go-mock", "Mode 02", "Timed Full Mock",
        "Two sections · timed modules · branching difficulty",
        "home-mock-readout", "Begin full mock")}
      ${modePanel("go-dash", "Mode 03", "Dashboard",
        "Ability trends · score bands · missed-item log",
        "home-dash-readout", "Open dashboard",
        `<span id="home-spark"></span>`)}
    </div>

    <div class="panel" style="margin-top:18px;">
      <p class="panel-kicker">Mechanism</p>
      <h2>How adaptivity works here</h2>
      <p class="how-copy">Each answered item updates your per-skill ability estimate
      (<code>θ</code>) with a Bayesian 2-parameter-logistic model,
      <code>P(correct) = σ(a(θ−b))</code>. The next item is the unanswered one with
      highest <code>Fisher information</code> at your current θ: questions
      concentrate where they tell us the most about you. In full mocks, module 2
      difficulty branches on module-1 performance, mirroring the real digital SAT.
      Every blueprint is drawn from a seeded
      <code>Dirichlet–multinomial</code>, so any session reproduces exactly from its seed.</p>
    </div>`;

  document.getElementById("go-practice").onclick = () => setView("practice-setup");
  document.getElementById("go-mock").onclick = () => startMockFlow();
  document.getElementById("go-dash").onclick = () => setView("dashboard");
  hydrateHome();
}

async function hydrateHome() {
  let data;
  try {
    data = await api("GET", `/api/dashboard/${state.user.user_id}`);
  } catch (e) {
    return;
  }

  const stats = thetaMapStats();
  const practiceReadout = document.getElementById("home-practice-readout");
  if (practiceReadout) {
    practiceReadout.innerHTML = stats
      ? `MEAN θ <b>${fmtTheta(stats.mean)}</b> · <b>${stats.attempts}</b> responses`
      : `no measurements yet`;
  }

  const mockReadout = document.getElementById("home-mock-readout");
  if (mockReadout) {
    const lastMock = (data.sessions || []).find(
      (s) => s.kind === "mock" && s.status === "complete" &&
             s.summary && s.summary.sections);
    if (lastMock) {
      const secs = lastMock.summary.sections;
      const bandText = ["rw", "math"]
        .map((k) => secs[k] && secs[k].score_estimate)
        .filter(Boolean)
        .map(([lo, hi]) => `${lo}–${hi}`)
        .join(" / ");
      mockReadout.innerHTML = `LAST MOCK BAND <b>${esc(bandText || "-")}</b>`;
    } else {
      mockReadout.textContent = "no completed mocks yet";
    }
  }

  const dashReadout = document.getElementById("home-dash-readout");
  const sparkSlot = document.getElementById("home-spark");
  const topSkill = [...(data.theta || [])]
    .sort((a, b) => b.attempts - a.attempts)[0];
  if (dashReadout && topSkill) {
    dashReadout.innerHTML = `θ TREND · <b>${esc(topSkill.skill_name)}</b>`;
  }
  if (sparkSlot && topSkill && topSkill.history && topSkill.history.length > 1) {
    sparkSlot.innerHTML = sparklineSVG(topSkill.history);
  }
}

/* ---------------- practice setup ---------------- */

let practiceConfig = { section: "mixed", length: 10, skills: new Set() };

function skillList() {
  const out = [];
  for (const sec of state.framework.sections) {
    for (const dom of sec.domains) {
      for (const sk of dom.skills) {
        out.push({ ...sk, section: sec.section_id });
      }
    }
  }
  return out;
}

function renderPracticeSetup() {
  const skills = skillList();
  $view.innerHTML = `
    <div class="panel">
      <p class="panel-kicker">Session parameters</p>
      <h2>Adaptive practice</h2>
      <div class="field">
        <label for="cfg-section">Section</label>
        <select id="cfg-section">
          <option value="mixed">Mixed (both sections)</option>
          <option value="rw">Reading and Writing</option>
          <option value="math">Math</option>
        </select>
      </div>
      <div class="field">
        <label for="cfg-length">Number of questions ·
          <span class="mono" id="len-label">${practiceConfig.length}</span></label>
        <input type="range" id="cfg-length" min="4" max="30" step="1"
               value="${practiceConfig.length}">
      </div>
      <div class="field">
        <label>Focus skills: optional; empty draws the full blueprint mix</label>
        <div class="skill-toggle-list" id="skill-list"></div>
      </div>
      <div class="btn-row">
        <button class="btn-commit" id="start-practice">Generate session</button>
      </div>
      <p class="muted mono" style="font-size:.72rem;margin-top:14px;">
        Sessions are seeded: the same seed reproduces the same blueprint and questions.</p>
    </div>`;

  const list = document.getElementById("skill-list");
  list.innerHTML = skills.map((s) => `
    <button type="button" class="skill-toggle"
      aria-pressed="${practiceConfig.skills.has(s.skill_id)}"
      data-skill="${s.skill_id}">
      <span class="tickbox" aria-hidden="true"></span>${esc(s.name)}
      <span class="mono muted" style="margin-left:auto;font-size:.66rem;">${esc(s.section.toUpperCase())}</span>
    </button>`).join("");
  list.querySelectorAll(".skill-toggle").forEach((btn) => {
    btn.addEventListener("click", () => {
      const sid = btn.dataset.skill;
      const on = btn.getAttribute("aria-pressed") !== "true";
      btn.setAttribute("aria-pressed", String(on));
      if (on) practiceConfig.skills.add(sid);
      else practiceConfig.skills.delete(sid);
    });
  });

  const sectionSel = document.getElementById("cfg-section");
  sectionSel.value = practiceConfig.section;
  sectionSel.addEventListener("change", (e) => {
    practiceConfig.section = e.target.value;
  });
  document.getElementById("cfg-length").addEventListener("input", (e) => {
    practiceConfig.length = parseInt(e.target.value, 10);
    document.getElementById("len-label").textContent = e.target.value;
  });

  document.getElementById("start-practice").addEventListener("click", async () => {
    try {
      const body = {
        section: practiceConfig.section === "mixed" ? null : practiceConfig.section,
        length: practiceConfig.length,
        skills: practiceConfig.skills.size ? [...practiceConfig.skills] : null,
      };
      if (state.x) {
        const p = await xApi("/api/x/practice/start", body);
        window.practiceState = {
          session_id: p.session_id, seed: p.seed,
          total_questions: p.total_questions, answered: p.answered,
          finished: p.finished, question: p.question, summary: null,
        };
        syncThetaFromBlob(p.state);
        window.practiceUI = { current: null };
      } else {
        Object.assign(body, { user_id: state.user.user_id });
        window.practiceState = await api("POST", "/api/practice", body);
        window.practiceUI = { current: null };
      }
      setView("practice");
    } catch (err) {
      showError(err.message);
    }
  });
}

function syncThetaFromBlob(blob) {
  for (const [sid, v] of Object.entries((blob && blob.theta) || {})) {
    state.thetaMap[sid] = {
      skill_id: sid, theta: v.est, posterior_sd: v.sd,
      attempts: v.n, correct: v.correct, history: v.history || [],
    };
  }
}

/* ---------------- practice run ---------------- */

function choiceLetters(i) { return "ABCD"[i]; }

function renderPractice() {
  const ps = window.practiceState;
  if (!ps || !ps.question) {
    if (ps && ps.finished && ps.summary) return showPracticeSummary(ps.summary);
    setView("practice-setup");
    return;
  }
  window.practiceUI.current = ps.question;
  drawPracticeQuestion(null, null);
}

function drawPracticeQuestion(selected, result) {
  const ps = window.practiceState;
  const q = window.practiceUI.current;
  const answered = result ? result.answered : ps.answered;
  const total = ps.total_questions;

  let answersHtml = q.choices.map((c, i) => {
    let stateClass = "";
    let tabState = "";
    if (result) {
      if (c === result.correct_choice) stateClass = "state-correct";
      else if (i === selected) stateClass = "state-incorrect";
    } else if (i === selected) {
      stateClass = "selected";
    }
    return `
      <button type="button" class="answer-row ${stateClass}"
        data-index="${i}" aria-pressed="${i === selected}"
        ${result ? "disabled" : ""}>
        <span class="answer-tab">${choiceLetters(i)}</span>
        <span>${esc(c)}</span>
      </button>`;
  }).join("");

  let verdictHtml = "";
  if (result) {
    verdictHtml = `
      <div class="verdict ${result.correct ? "" : "no"}">
        <span class="verdict-label">${result.correct ? "Correct" :
          "Incorrect: see below"}</span>
        <p class="explanation">${esc(result.explanation)}</p>
        <span class="mono theta-line">${thetaMove(result.theta_before,
          result.theta_after)} · ${esc(skillName(result.skill_id))}</span>
      </div>`;
  }

  $view.innerHTML = `
    <div class="panel">
      <div class="progress-note">
        <span>ITEM ${answered + (result ? 0 : 1)} OF ${total}</span>
        <span class="cal-optional">SEED <span class="mono">${esc(ps.seed)}</span></span>
      </div>
      <div class="tickbar" aria-hidden="true">
        ${Array.from({ length: total }, (_, i) =>
          `<i class="${i < answered ? "on" : ""}"></i>`).join("")}
      </div>
      <div class="q-meta">
        <span class="q-skill">${esc(skillName(q.skill_id))}</span>
        <span>${esc(q.difficulty.toUpperCase())}</span>
      </div>
      <div class="prompt">${esc(q.prompt)}</div>
      <div class="answers" id="answer-sheet">${answersHtml}</div>
      ${verdictHtml}
      <div class="btn-row">
        ${result
          ? `<button type="button" class="btn-commit" id="next-q">${
              ps.finished ? "See summary" : "Next question"}</button>`
          : `<button type="button" class="btn-commit" id="submit-q"
              ${selected === null ? "disabled" : ""}>Submit answer</button>`}
      </div>
    </div>`;

  renderCalibration(!!result);

  if (!result) {
    $view.querySelectorAll(".answer-row").forEach((b) =>
      b.addEventListener("click", () =>
        drawPracticeQuestion(parseInt(b.dataset.index, 10), null)));
    document.getElementById("submit-q").addEventListener("click",
      submitPracticeAnswer);
  } else {
    document.getElementById("next-q").addEventListener("click", advancePractice);
  }
}

async function submitPracticeAnswer() {
  const rows = [...$view.querySelectorAll(".answer-row")];
  const selected = rows.findIndex((b) => b.classList.contains("selected"));
  if (selected < 0) return;
  try {
    const ps = window.practiceState;
    let result;
    if (state.x) {
      result = await xApi("/api/x/session/answer",
        { session_id: ps.session_id, choice_index: selected });
      syncThetaFromBlob(result.state);
    } else {
      result = await api("POST",
        `/api/sessions/${ps.session_id}/answer`, { choice_index: selected });
    }
    ps.answered = result.answered;
    ps.finished = result.finished;
    ps.summary = result.summary || ps.summary;
    if (!state.x) {
      const row = state.thetaMap[result.skill_id];
      if (row) {
        row.theta = result.theta_after;
        if (row.attempts != null) row.attempts += 1;
      }
    } else {
      renderCalibration(true);
    }
    drawPracticeQuestion(selected, result);
  } catch (err) {
    showError(err.message);
  }
}

async function advancePractice() {
  try {
    const ps = window.practiceState;
    if (ps.finished) {
      showPracticeSummary(ps.summary);
      return;
    }
    let next;
    if (state.x) {
      next = await xApi("/api/x/session/next", { session_id: ps.session_id });
    } else {
      next = await api("GET", `/api/sessions/${ps.session_id}/next`);
    }
    ps.question = next.question;
    ps.answered = next.answered;
    ps.finished = next.finished;
    if (next.finished) {
      showPracticeSummary(next.summary);
      return;
    }
    window.practiceUI.current = next.question;
    drawPracticeQuestion(null, null);
  } catch (err) {
    showError(err.message);
  }
}

function showPracticeSummary(summary) {
  const rows = Object.entries(summary.per_skill).map(([sid, s]) => `
    <tr>
      <td>${esc(skillName(sid))}</td>
      <td class="num">${s.attempts}</td>
      <td class="num">${s.correct}</td>
      <td class="num">${Math.round(100 * s.correct / s.attempts)}%</td>
      <td class="num">θ ${fmtTheta(s.theta, s.posterior_sd)}</td>
    </tr>`).join("");
  $view.innerHTML = `
    <div class="panel">
      <p class="panel-kicker">Session readout</p>
      <h2>Session summary</h2>
      <div class="readouts">
        <div class="readout"><div class="value">${summary.correct}/${summary.answered}</div>
          <div class="label">Correct</div></div>
        <div class="readout"><div class="value">${Math.round(100 * summary.accuracy)}%</div>
          <div class="label">Accuracy</div></div>
        <div class="readout"><div class="value">${esc(summary.seed)}</div>
          <div class="label">Seed · reproducible</div></div>
      </div>
      <table class="data">
        <thead><tr><th>Skill</th><th>Tried</th><th>Correct</th><th>Accuracy</th><th>θ estimate</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
      <div class="btn-row">
        <button type="button" class="btn-commit" id="again-btn">New session</button>
        <button type="button" class="btn-quiet" id="dash-btn">Dashboard</button>
      </div>
    </div>`;
  renderCalibration(false);
  document.getElementById("again-btn").onclick = () => setView("practice-setup");
  document.getElementById("dash-btn").onclick = () => setView("dashboard");
}

/* ---------------- full mock ---------------- */

let mockState = null;
let mockTimerHandle = null;

async function startMockFlow() {
  try {
    if (state.x) {
      mockState = await xApi("/api/x/mocks/start",
        { sections: ["rw", "math"] });
      syncThetaFromBlob(mockState.state);
    } else {
      const payload = await api("POST", "/api/mocks",
        { user_id: state.user.user_id });
      mockState = payload;
    }
    mockUI.moduleStarts = {};
    mockUI.introSeen = {};
    setView("mock");
  } catch (err) {
    showError(err.message);
  }
}

function mockCurrentModule() {
  for (const secId of Object.keys(mockState.sections)) {
    const sec = mockState.sections[secId];
    for (const mod of sec.modules) {
      if (mod.unlocked && mod.questions.some((q) => !q.answered)) {
        return { secId, mod };
      }
    }
  }
  return null;
}

function renderMock() {
  if (!mockState) {
    $view.innerHTML = `
      <div class="panel">
        <p class="panel-kicker">Mode 02</p>
        <h2>Timed full mock</h2>
        <p>A complete test: Reading &amp; Writing (2 × 27 questions, 32 min/module)
        and Math (2 × 22 questions, 35 min/module). Module 2 difficulty branches
        on your module 1 performance.</p>
        <div class="btn-row">
          <button type="button" class="btn-commit" id="begin-mock">Begin full mock</button>
        </div></div>`;
    document.getElementById("begin-mock").onclick = startMockFlow;
    renderCalibration(false);
    return;
  }

  const spot = mockCurrentModule();
  clearInterval(mockTimerHandle);
  if (!spot) {
    renderCalibration(false);
    showMockReport(null);
    return;
  }

  const { secId, mod } = spot;
  const introKey = `${secId}:${mod.index}`;

  if (mod.index === 2 && !mockUI.introSeen[introKey]) {
    mockUI.introSeen[introKey] = true;
    renderCalibration(false);
    renderModuleInterstitial(secId, mod);
    return;
  }

  const qIndex = mod.questions.findIndex((q) => !q.answered);
  const q = mod.questions[qIndex];
  const answeredInModule = mod.questions.filter((x) => x.answered).length;

  $view.innerHTML = `
    <div class="panel">
      <div class="progress-note">
        <span>${sectionName(secId).toUpperCase()} · MODULE ${mod.index} ·
          ITEM ${qIndex + 1} OF ${mod.questions.length}</span>
        <span class="cal-optional">${answeredInModule}/${mod.questions.length} SUBMITTED</span>
      </div>
      <div class="tickbar" aria-hidden="true">
        ${mod.questions.map((x) =>
          `<i class="${x.answered ? "on" : ""}"></i>`).join("")}
      </div>
      <div class="q-meta">
        <span class="q-skill">${esc(skillName(q.skill_id))}</span>
        <span>${esc(q.difficulty.toUpperCase())}</span>
      </div>
      <div class="prompt">${esc(q.prompt)}</div>
      <div class="answers" id="answer-sheet">
        ${q.choices.map((c, i) => `
          <button type="button" class="answer-row" data-index="${i}">
            <span class="answer-tab">${choiceLetters(i)}</span>
            <span>${esc(c)}</span>
          </button>`).join("")}
      </div>
      <div class="btn-row">
        <button type="button" class="btn-commit" id="submit-mock" disabled>Submit answer</button>
      </div>
    </div>`;

  const moduleKey = `${secId}:${mod.index}`;
  if (!mockUI.moduleStarts[moduleKey]) {
    mockUI.moduleStarts[moduleKey] = Date.now();
  }
  const elapsed = (Date.now() - mockUI.moduleStarts[moduleKey]) / 1000;
  startModuleTimer(mockState.sections[secId].minutes_per_module * 60, elapsed);

  $view.querySelectorAll(".answer-row").forEach((b) => {
    b.addEventListener("click", () => {
      $view.querySelectorAll(".answer-row").forEach((x) =>
        x.classList.remove("selected"));
      b.classList.add("selected");
      document.getElementById("submit-mock").disabled = false;
    });
  });
  document.getElementById("submit-mock").addEventListener("click", async () => {
    const sel = $view.querySelector(".answer-row.selected");
    if (!sel) return;
    try {
      if (state.x) {
        await xApi(`/api/x/mocks/answer`,
          { mock_id: mockState.mock_id, question_id: q.question_id,
            choice_index: parseInt(sel.dataset.index, 10) });
      } else {
        await api(`POST`, `/api/mocks/${mockState.mock_id}/answer`,
          { question_id: q.question_id,
            choice_index: parseInt(sel.dataset.index, 10) });
      }
      const fresh = state.x
        ? await xApi(`/api/x/mocks/state`, { mock_id: mockState.mock_id })
        : await api("GET", `/api/mocks/${mockState.mock_id}`);
      mockState = fresh;
      renderMock();
    } catch (err) {
      showError(err.message);
    }
  });
}

function renderModuleInterstitial(secId, mod) {
  $view.innerHTML = `
    <div class="panel interstitial">
      <p class="panel-kicker">Module transition · ${esc(sectionName(secId))}</p>
      <h2>Module 2 assembled</h2>
      <div class="branch-readout">
        MODULE 2 DIFFICULTY:&nbsp;&nbsp;<span class="branch-value">${esc(profileLabel(mod.profile).toUpperCase())}</span><br>
        <span class="muted">CALIBRATED FROM MODULE 1 PERFORMANCE</span><br>
        BLUEPRINT PROFILE:&nbsp;&nbsp;<span class="mono">${esc(mod.profile.replace("_", " "))}</span>
      </div>
      <p class="muted" style="font-size:.86rem;">
        As on the digital SAT, the difficulty of your second module was selected by
        your first-module performance. This is the adaptive mechanism working :
        it is shown, not hidden.</p>
      <div class="btn-row">
        <button type="button" class="btn-commit" id="continue-mod2">Continue to module 2</button>
      </div>
    </div>`;
  document.getElementById("continue-mod2").onclick = () => renderMock();
}

function startModuleTimer(totalSeconds, elapsedSeconds) {
  const el = document.getElementById("module-timer");
  if (!el) return;
  const t0 = Date.now() / 1000 - elapsedSeconds;
  const tick = () => {
    const live = document.getElementById("module-timer") || el;
    const s = Math.max(0, Math.round(totalSeconds - (Date.now() / 1000 - t0)));
    const mm = String(Math.floor(s / 60)).padStart(2, "0");
    const ss = String(s % 60).padStart(2, "0");
    live.textContent = `${mm}:${ss}`;
    live.classList.toggle("timer-low", s <= 300);
    if (s === 0) {
      live.textContent = "TIME EXPIRED: FINISH MODULE";
      clearInterval(mockTimerHandle);
    }
  };
  tick();
  mockTimerHandle = setInterval(tick, 500);
}

async function fetchMockReport() {
  if (state.x) {
    const payload = await xApi("/api/x/mocks/state",
      { mock_id: mockState.mock_id });
    mockState = payload;
    return mockState.report;
  }
  const report = await api("GET", `/api/mocks/${mockState.mock_id}/report`);
  mockState.report = report;
  return report;
}

async function showMockReport(report) {
  if (!report) {
    try { report = await fetchMockReport(); }
    catch (e) {
      $view.innerHTML = `<div class="panel"><p class="muted">No report available yet.</p></div>`;
      return;
    }
  }
  const sectionBlocks = Object.entries(report.sections).map(([secId, rep]) => {
    const mods = rep.modules.map((m) => `
      <tr>
        <td>MODULE ${m.module}</td>
        <td><span class="mono">${esc(profileLabel(m.profile).toUpperCase())}</span></td>
        <td class="num">${m.correct}/${m.total}</td>
        <td class="num">${m.total ? Math.round(100 * m.correct / m.total) : 0}%</td>
      </tr>`).join("");
    const domains = (rep.domains || []).map((d) => `
      <tr>
        <td>${esc(d.name)}</td>
        <td class="num">${d.correct}/${d.total}</td>
        <td class="num">${d.total ? Math.round(100 * d.correct / d.total) : 0}%</td>
      </tr>`).join("");
    const band = rep.score_estimate
      ? scaleBandHTML(rep.score_estimate[0], rep.score_estimate[1])
      : `<p class="muted">-</p>`;
    return `
      <div class="panel">
        <p class="panel-kicker">${esc(sectionName(secId))}</p>
        <h2 style="margin-bottom:2px;">Estimated band</h2>
        ${band}
        <table class="data">
          <thead><tr><th></th><th>Profile</th><th>Score</th><th>%</th></tr></thead>
          <tbody>${mods}</tbody>
        </table>
        ${domains ? `
        <p class="panel-kicker" style="margin-top:16px;">Where the band came from</p>
        <table class="data">
          <thead><tr><th>Domain</th><th>Correct</th><th>%</th></tr></thead>
          <tbody>${domains}</tbody>
        </table>` : ""}
      </div>`;
  }).join("");
  $view.innerHTML = `
    <div class="panel">
      <p class="panel-kicker">Final readout</p>
      <h2>Mock test report</h2>
      <p class="muted" style="font-size:.84rem;">
        Bands are heuristic estimates from your IRT ability estimates: not official
        scores and not College Board equating.</p>
    </div>
    <div class="panel-grid">${sectionBlocks}</div>
    <div class="btn-row" style="margin-top:20px;">
      <button type="button" class="btn-commit" id="new-mock">New mock</button>
      <button type="button" class="btn-quiet" id="to-dash">Dashboard</button>
    </div>`;
  document.getElementById("new-mock").onclick = () => {
    mockState = null;
    startMockFlow();
  };
  document.getElementById("to-dash").onclick = () => setView("dashboard");
}

/* ---------------- dashboard ---------------- */

async function renderDashboard() {
  let data;
  try {
    if (state.x) {
      data = await xApi("/api/x/dashboard");
    } else {
      data = await api("GET", `/api/dashboard/${state.user.user_id}`);
    }
  } catch (err) {
    showError(err.message);
    return;
  }

  if (!state.x) {
    for (const row of data.theta || []) {
      state.thetaMap[row.skill_id] = row;
    }
  } else {
    syncThetaFromBlob(loadXBlob());
  }

  const scoreCards = Object.entries(data.scores).map(([secId, s]) => `
    <div class="panel">
      <p class="panel-kicker">${esc(sectionName(secId))}</p>
      ${scaleBandHTML(s.low, s.high)}
    </div>`).join("");

  const completedMocks = (data.sessions || [])
    .filter((s) => s.kind === "mock" && s.status === "complete" &&
                   s.summary && s.summary.sections)
    .slice(0, 6);
  const bandHistory = completedMocks.map((s) => {
    const when = new Date(s.created_at * 1000);
    const stamp = `${when.toLocaleDateString()} ${when.toLocaleTimeString([], {
      hour: "2-digit", minute: "2-digit"})}`;
    const rows = ["rw", "math"].map((k) => {
      const est = s.summary.sections[k] && s.summary.sections[k].score_estimate;
      if (!est) return "";
      return `
        <div class="band-history-row">
          <span class="band-history-label mono">${esc(k.toUpperCase())}</span>
          <div class="band-history-scale">${scaleBandHTML(est[0], est[1], true)}</div>
        </div>`;
    }).join("");
    return `
      <details class="review-row band-history-item" open>
        <summary><span class="skill-tag">MOCK</span>
          <span class="snippet mono">${esc(stamp)} · seed ${esc(s.seed || "")}</span></summary>
        <div class="review-body">${rows}</div>
      </details>`;
  }).join("");

  const thetaSorted = [...(data.theta || [])].sort((a, b) => b.attempts - a.attempts);
  const thetaRows = thetaSorted.map((t) => {
    const pctPos = Math.max(2, Math.min(98, ((t.theta + 3) / 6) * 100));
    return `
      <tr>
        <td>${esc(t.skill_name)}</td>
        <td class="num">${t.attempts}</td>
        <td class="num">${t.correct}</td>
        <td style="min-width:110px;"><div class="theta-bar">
          <div style="left:${Math.max(0, pctPos - 12)}%;width:12%;"></div></div></td>
        <td class="num">θ ${fmtTheta(t.theta, t.posterior_sd)}</td>
      </tr>`;
  }).join("");

  const sessionsRows = (data.sessions || []).map((s) => `
    <tr>
      <td>${esc(s.kind.toUpperCase())}</td>
      <td>${s.section ? esc(sectionName(s.section)) : "-"}</td>
      <td>${esc(s.status.toUpperCase())}</td>
      <td class="num">${s.summary ? `${s.summary.correct}/${s.summary.answered}` : "-"}</td>
      <td class="num">${new Date(s.created_at * 1000).toLocaleString()}</td>
    </tr>`).join("");

  const missedRows = (data.missed || []).slice(0, 25).map((m) => {
    const qq = m.question;
    const snippet = qq.prompt.replace(/\s+/g, " ").slice(0, 90);
    const yours = m.choice_index != null && qq.choices[m.choice_index]
      ? qq.choices[m.choice_index] : "(no answer)";
    const right = qq.choices[qq.answer_index];
    return `
      <details class="review-row">
        <summary>
          <span class="skill-tag">${esc(skillName(qq.skill_id))}</span>
          <span class="snippet">${esc(snippet)}…</span>
        </summary>
        <div class="review-body">
          <p class="prompt-snippet">${esc(qq.prompt)}</p>
          <p>Your answer: <span class="your-answer">${esc(yours)}</span></p>
          <p>Correct: <span class="correct-answer">${esc(right)}</span></p>
          <p class="muted">${esc(qq.explanation)}</p>
        </div>
      </details>`;
  }).join("");

  const weakSpots = data.weak_spots || [];
  let weakHtml = "";
  if (!weakSpots.length) {
    weakHtml = `<p class="empty-note">NO RESPONSES YET :  START ADAPTIVE PRACTICE TO BEGIN CALIBRATION</p>`;
  } else if (weakSpots.every((w) => w.status === "strong")) {
    weakHtml = `<p class="empty-note">NO WEAK SPOTS DETECTED :  KEEP THE STREAK GOING</p>`;
  } else {
    const rows = weakSpots.slice(0, 8).map((w, i) => {
      const badge = w.status === "struggling"
        ? '<span class="skill-tag">STRUGGLING</span>'
        : w.status === "developing"
          ? '<span class="mono muted" style="font-size:.64rem;letter-spacing:.08em;">DEVELOPING</span>'
          : '<span class="mono" style="font-size:.64rem;color:var(--signal);letter-spacing:.08em;">STRONG</span>';
      const link = practiceLink(w);
      const linkBtn = (i < 3 && w.status !== "strong" && link)
        ? `<a class="btn-quiet" style="padding:5px 12px;font-size:.66rem;text-decoration:none;"
             href="${esc(link)}" target="_blank" rel="noopener noreferrer">${esc(w.tier_label)}: ${esc(domainShort(w.domain_id))} &#8599;</a>`
        : "";
      return `
        <div class="acct-row">
          ${badge}
          <span class="snippet">
            <span class="mono">${esc(w.tier_label.toUpperCase())}</span>
            &middot; ${esc(w.domain_name)}
          </span>
          <span class="mono muted" style="margin-left:auto;font-size:.72rem;">
            ${w.correct}/${w.attempted}
          </span>
          ${linkBtn}
        </div>`;
    }).join("");
    weakHtml = `<div class="review-log">${rows}</div>
      <p class="muted mono" style="font-size:.68rem;margin-top:8px;">
        Suggested practice links open Khan Academy units matched to the tier
        where misses concentrate. Top three shown by importance.</p>`;
  }

  $view.innerHTML = `
    <div class="panel">
      <p class="panel-kicker">Diagnosis</p>
      <h2>Weak spots</h2>
      ${weakHtml}
    </div>
    <div class="panel">
      <p class="panel-kicker">Calibrated progress</p>
      <h2>Estimated score bands</h2>
      ${scoreCards
        ? `<div class="panel-grid">${scoreCards}</div>`
        : `<p class="empty-note">NO CALIBRATION YET: COMPLETE A FULL MOCK TO ESTABLISH A BAND</p>`}
      <p class="muted mono" style="font-size:.7rem;margin-top:10px;">
        Heuristic mapping from IRT ability to the 200–800 scale. Not an official score.</p>
    </div>
    ${bandHistory ? `
    <div class="panel">
      <p class="panel-kicker">Range over time</p>
      <h2>Band history</h2>
      <div class="review-log">${bandHistory}</div>
    </div>` : ""}
    <div class="panel">
      <p class="panel-kicker">Ability estimates</p>
      <h2>θ by skill</h2>
      ${thetaRows ? `<table class="data">
        <thead><tr><th>Skill</th><th>Tried</th><th>Correct</th><th>Ability</th><th>θ ± sd</th></tr></thead>
        <tbody>${thetaRows}</tbody></table>`
        : `<p class="empty-note">NO RESPONSES YET: START ADAPTIVE PRACTICE TO BEGIN CALIBRATION</p>`}
    </div>
    <div class="panel">
      <p class="panel-kicker">Measurement history</p>
      <h2>θ trend per skill</h2>
      <canvas id="theta-chart" class="chart"></canvas>
    </div>
    <div class="panel">
      <p class="panel-kicker">Review log</p>
      <h2>Missed questions</h2>
      ${missedRows
        ? `<div class="review-log">${missedRows}</div>`
        : (data.theta && data.theta.some((t) => t.attempts > 0)
          ? `<p class="empty-note">NOTHING MISSED ON RECORDED ITEMS</p>`
          : `<p class="empty-note">NO RESPONSES LOGGED YET: THE REVIEW LOG FILLS AS YOU ANSWER</p>`)}
    </div>
    <div class="panel">
      <p class="panel-kicker">Session log</p>
      <h2>Recent sessions</h2>
      ${sessionsRows ? `<table class="data">
        <thead><tr><th>Type</th><th>Section</th><th>Status</th><th>Result</th><th>When</th></tr></thead>
        <tbody>${sessionsRows}</tbody></table>`
        : `<p class="empty-note">NO SESSIONS LOGGED: HOME LISTS ALL THREE MODES</p>`}
    </div>`;

  renderCalibration(false);
  requestAnimationFrame(() => drawThetaChart(thetaSorted.slice(0, 6)));
}

function drawThetaChart(skills) {
  const canvas = document.getElementById("theta-chart");
  if (!canvas) return;
  const cs = getComputedStyle(document.documentElement);
  const cSignal = cs.getPropertyValue("--signal").trim() || "#2B6E5E";
  const cInk = cs.getPropertyValue("--ink").trim() || "#14181C";
  const cGraphite = cs.getPropertyValue("--graphite").trim() || "#5B6470";
  const bases = [cSignal, cInk, cGraphite];

  const dpr = window.devicePixelRatio || 1;
  const W = canvas.width = canvas.offsetWidth * dpr;
  const H = canvas.height = 230 * dpr;
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, W, H);
  const pad = 34 * dpr;
  const yMin = -2.5, yMax = 2.5;

  ctx.globalAlpha = 0.25;
  ctx.strokeStyle = cGraphite;
  ctx.lineWidth = 1;
  ctx.beginPath();
  for (const gy of [-2, -1, 0, 1, 2]) {
    const y = H - pad - ((gy - yMin) / (yMax - yMin)) * (H - 2 * pad);
    ctx.moveTo(pad, y);
    ctx.lineTo(W - pad / 2, y);
  }
  ctx.stroke();
  ctx.globalAlpha = 1;

  ctx.fillStyle = cGraphite;
  ctx.font = `${11 * dpr}px "IBM Plex Mono", monospace`;
  for (const gy of [-2, 0, 2]) {
    const y = H - pad - ((gy - yMin) / (yMax - yMin)) * (H - 2 * pad);
    ctx.fillText(String(gy), 8 * dpr, y + 4 * dpr);
  }

  if (!skills.length) {
    ctx.fillText("NO MEASUREMENTS YET: θ TREND APPEARS AFTER FIRST SESSION",
      pad, H / 2);
    return;
  }

  const maxLen = Math.max(...skills.map((s) => s.history.length));
  skills.forEach((s, si) => {
    if (!s.history || !s.history.length) return;
    ctx.globalAlpha = si < 3 ? 1 : (si < 5 ? 0.7 : 0.5);
    ctx.strokeStyle = bases[si % bases.length];
    ctx.lineWidth = 1.5 * dpr;
    ctx.beginPath();
    s.history.forEach((theta, i) => {
      const x = pad + (i / Math.max(1, maxLen - 1)) * (W - pad * 1.5);
      const y = H - pad - ((theta - yMin) / (yMax - yMin)) * (H - 2 * pad);
      if (i) ctx.lineTo(x, y); else ctx.moveTo(x, y);
    });
    ctx.stroke();
  });
  ctx.globalAlpha = 1;

  ctx.font = `${11 * dpr}px "IBM Plex Mono", monospace`;
  skills.forEach((s, si) => {
    ctx.fillStyle = bases[si % bases.length];
    ctx.globalAlpha = si < 3 ? 1 : 0.7;
    ctx.fillText(s.skill_name.slice(0, 22), pad + si * 128 * dpr, H - 8 * dpr);
  });
  ctx.globalAlpha = 1;
}

/* ---------------- theme ---------------- */

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  localStorage.setItem("satprep_theme", theme);
  const btn = document.getElementById("theme-toggle");
  if (btn) {
    btn.textContent = theme === "dark" ? "LIGHT" : "DARK";
    btn.setAttribute("aria-pressed", String(theme === "dark"));
    btn.title = `Switch to ${theme === "dark" ? "light" : "dark"} theme`;
  }
}

function initTheme() {
  const saved = localStorage.getItem("satprep_theme");
  const prefersDark = window.matchMedia &&
    window.matchMedia("(prefers-color-scheme: dark)").matches;
  applyTheme(saved || (prefersDark ? "dark" : "light"));
}

/* ---------------- about dialog ---------------- */

let aboutLastFocus = null;

function openAbout() {
  aboutLastFocus = document.activeElement;
  const backdrop = document.getElementById("about-backdrop");
  backdrop.hidden = false;
  document.getElementById("about-close").focus();
}

function closeAbout() {
  document.getElementById("about-backdrop").hidden = true;
  if (aboutLastFocus && aboutLastFocus.focus) aboutLastFocus.focus();
}

/* ---------------- account switcher ---------------- */

let acctLastFocus = null;

function openAccountPanel() {
  acctLastFocus = document.activeElement;
  renderAccountList();
  document.getElementById("acct-backdrop").hidden = false;
  document.getElementById("acct-close").focus();
}

function closeAccountPanel() {
  const backdrop = document.getElementById("acct-backdrop");
  if (!backdrop.hidden) {
    backdrop.hidden = true;
    if (acctLastFocus && acctLastFocus.focus) acctLastFocus.focus();
  }
}

function renderAccountList() {
  const listEl = document.getElementById("acct-list");
  const accounts = sortedAccounts();
  const activeId = state.user ? state.user.user_id
    : localStorage.getItem("satprep_uid");
  if (!accounts.length) {
    listEl.innerHTML =
      '<p class="muted mono" style="font-size:.72rem;">No profiles yet.</p>';
  } else {
    listEl.innerHTML = accounts.map((a) => `
      <div class="acct-row">
        <span class="skill-tag">${a.provider === "google" ? "GOOGLE"
          : "GUEST"}</span>
        <span class="snippet">${esc(a.name)}
          <span class="mono muted" style="font-size:.68rem;">${esc(a.id)}</span>
        </span>
        <span style="margin-left:auto;display:flex;gap:8px;">
          ${a.id === activeId
            ? '<span class="branch-value" style="font-size:.62rem;">ACTIVE</span>'
            : `<button type="button" class="btn-quiet" style="padding:5px 12px;font-size:.66rem;" data-switch="${esc(a.id)}">Switch</button>`}
          <button type="button" class="btn-quiet" style="padding:5px 12px;font-size:.66rem;color:var(--alert);border-color:var(--alert);"
            data-del="${esc(a.id)}">Delete</button>
        </span>
      </div>`).join("");
  }
  listEl.querySelectorAll("[data-switch]").forEach((b) =>
    b.addEventListener("click", () => switchToAccount(b.dataset.switch)));
  listEl.querySelectorAll("[data-del]").forEach((b) =>
    b.addEventListener("click", async () => {
      const id = b.dataset.del;
      if (b.dataset.armed !== "1") {
        b.dataset.armed = "1";
        b.textContent = "Confirm?";
        setTimeout(() => {
          b.dataset.armed = "0";
          b.textContent = "Delete";
        }, 4000);
        return;
      }
      await deleteAccount(id);
      renderAccountList();
    }));
  const guestBtn = document.getElementById("acct-add-guest");
  const hasGuest = guestCount() > 0;
  guestBtn.disabled = hasGuest;
  guestBtn.title = hasGuest
    ? "Only one guest profile is allowed per browser"
    : "";
  const googleBtn = document.getElementById("acct-google");
  googleBtn.hidden = !state.googleClientId;
  document.getElementById("acct-note").textContent = state.x
    ? "Each account's progress lives in this browser's save files."
    : "Each account's progress lives on the server.";
}

async function switchToAccount(id) {
  const acct = findAccount(id);
  localStorage.setItem("satprep_uid", id);
  state.user = { user_id: id, name: (acct && acct.name) || "Student",
                 provider: id.startsWith("g-") ? "google" : undefined };
  await loadThetaMap();
  window.practiceState = null;
  mockState = null;
  clearInterval(window.mockTimerHandle);
  closeAccountPanel();
  render();
}

async function deleteAccount(id) {
  if (state.x) {
    localStorage.removeItem(xBlobKey(id));
  } else {
    try {
      await api("DELETE", `/api/users/${id}`);
    } catch (e) { /* already gone */ }
  }
  removeAccountEntry(id);
  if (state.user && state.user.user_id === id) {
    localStorage.removeItem("satprep_uid");
    state.user = null;
    state.thetaMap = {};
    setView("home");
  }
}

function wireChrome() {
  document.getElementById("brand-about").addEventListener("click", openAbout);
  document.getElementById("about-open").addEventListener("click", openAbout);  document.getElementById("about-close").addEventListener("click", closeAbout);
  document.getElementById("about-backdrop").addEventListener("click", (e) => {
    if (e.target === e.currentTarget) closeAbout();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" &&
        !document.getElementById("about-backdrop").hidden) {
      closeAbout();
    }
    if (e.key === "Escape" &&
        !document.getElementById("acct-backdrop").hidden) {
      closeAccountPanel();
    }
  });
  document.getElementById("theme-toggle").addEventListener("click", () => {
    const next = document.documentElement.dataset.theme === "dark"
      ? "light" : "dark";
    applyTheme(next);
    render();
  });
  const acctBackdrop = document.getElementById("acct-backdrop");
  document.getElementById("acct-close").addEventListener("click",
    closeAccountPanel);
  acctBackdrop.addEventListener("click", (e) => {
    if (e.target === acctBackdrop) closeAccountPanel();
  });
  document.getElementById("acct-add-guest").addEventListener("click", () => {
    closeAccountPanel();
    state.user = null;
    setView("home");
  });
  document.getElementById("acct-google").addEventListener("click", async () => {
    try {
      await loadGsiScript();
      window.google.accounts.id.initialize({
        client_id: state.googleClientId,
        callback: handleGoogleCredential,
        auto_select: false,
      });
      window.google.accounts.id.prompt();
    } catch (err) {
      showError(err.message);
    }
  });
  document.getElementById("acct-export").addEventListener("click",
    async () => {
      try {
        let bundle;
        if (state.x) {
          const blob = loadXBlob();
          if (!blob) throw new Error("No progress file yet.");
          bundle = { kind: "satprep-progress", mode: "x",
                     exported_at: new Date().toISOString(),
                     payload: { v: blob.v, user_id: blob.user_id,
                                theta: blob.theta,
                                sessions: blob.sessions } };
        } else {
          const uid = state.user ? state.user.user_id
            : localStorage.getItem("satprep_uid");
          if (!uid) throw new Error("No active account.");
          bundle = await api("GET", `/api/export/${uid}`);
        }
        const a = document.createElement("a");
        a.href = URL.createObjectURL(new Blob([JSON.stringify(bundle, null, 2)],
          { type: "application/json" }));
        a.download = `satprep-progress-${new Date().toISOString()
          .slice(0, 10)}.json`;
        a.click();
        URL.revokeObjectURL(a.href);
      } catch (err) {
        showError(err.message);
      }
    });
  document.getElementById("acct-import").addEventListener("click",
    () => document.getElementById("acct-import-file").click());
  document.getElementById("acct-import-file").addEventListener("change",
    (ev) => {
      const file = ev.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = async () => {
        ev.target.value = "";
        try {
          const parsed = JSON.parse(reader.result);
          if (parsed.kind !== "satprep-progress" || !parsed.payload) {
            throw new Error("Unrecognized progress file.");
          }
          if (state.x) {
            if (parsed.mode !== "x") {
              throw new Error("Server export detected. Import it while " +
                "signed in on that deployment instead.");
            }
            saveXBlob(parsed.payload);
            await loadThetaMap();
          } else {
            if (parsed.mode !== "db") {
              throw new Error("This is a browser save file; import it on " +
                "the device that exported it.");
            }
            await api("POST", "/api/import", parsed);
            await loadThetaMap();
          }
          showNotice("Import complete.");
        } catch (err) {
          showError(err.message);
        }
      };
      reader.readAsText(file);
    });
  const resetBtn = document.getElementById("about-reset");
  if (resetBtn) {
    resetBtn.addEventListener("click", async () => {
      if (resetBtn.dataset.armed !== "1") {
        resetBtn.dataset.armed = "1";
        resetBtn.textContent = "Confirm: erase all saved progress?";
        setTimeout(() => {
          resetBtn.dataset.armed = "0";
          resetBtn.textContent = "Reset saved progress";
        }, 4000);
        return;
      }
      const uid = state.user ? state.user.user_id
        : localStorage.getItem("satprep_uid");
      if (state.x) {
        localStorage.removeItem(xBlobKey(uid));
        removeAccountEntry(uid);
      } else if (uid) {
        try {
          await api("DELETE", `/api/users/${uid}`);
          removeAccountEntry(uid);
        } catch (e) { /* account already gone */ }
      }
      localStorage.removeItem("satprep_uid");
      state.user = null;
      state.thetaMap = {};
      closeAbout();
      setView("home");
    });
  }
}

/* ---------------- boot ---------------- */

async function boot() {
  initTheme();
  wireChrome();
  migrateLegacyBlob();
  try {
    const cap = await api("GET", "/api/x/capabilities");
    state.x = !!cap.stateless;
  } catch (e) {
    state.x = false;
  }
  const resetBtn = document.getElementById("about-reset");
  if (resetBtn) resetBtn.hidden = !state.x;
  try {
    const config = await api("GET", "/api/meta/config");
    state.googleClientId = config.google_client_id || null;
  } catch (e) {
    state.googleClientId = null;
  }
  const xBlob = state.x ? loadXBlob() : null;
  if (state.x && xBlob) {
    const uid = xBlob.user_id || "local";
    const acct = findAccount(uid);
    state.user = { user_id: uid,
      name: (acct && acct.name)
        || localStorage.getItem("satprep_name") || "Student" };
    localStorage.setItem("satprep_uid", uid);
    await loadThetaMap();
  } else if (!state.x) {
    const uid = localStorage.getItem("satprep_uid");
    if (uid) {
      try {
        const data = await api("GET", `/api/users/${uid}`);
        state.user = data.user;
        upsertAccount(data.user.user_id, data.user.name,
          uid.startsWith("g-") ? "google" : "local");
        for (const row of data.theta || []) {
          state.thetaMap[row.skill_id] = row;
        }
      } catch (e) {
        localStorage.removeItem("satprep_uid");
      }
    }
  }
  try {
    state.framework = await api("GET", "/api/meta/framework");
  } catch (err) {
    $view.innerHTML =
      `<div class="error-box">Could not reach the API: ${esc(err.message)}</div>`;
    return;
  }
  render();
}

boot();

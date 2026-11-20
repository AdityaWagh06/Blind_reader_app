"use strict";

const $ = (sel) => document.querySelector(sel);
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const store = {
  get(k, d) { try { const v = localStorage.getItem(k); return v === null ? d : JSON.parse(v); } catch { return d; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* private mode */ } },
};

/* ===================== Routing ===================== */
function route() {
  const path = location.hash.replace(/^#/, "") || "/";
  const known = [...document.querySelectorAll(".view")].map((v) => v.dataset.view);
  const current = known.includes(path) ? path : "/";
  document.querySelectorAll(".view").forEach((v) => (v.hidden = v.dataset.view !== current));
  document.querySelectorAll("nav a").forEach((a) => { if (a.dataset.route === current) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current"); });
  document.title = { "/": "Blind Reader Assistant", "/evaluation": "Evaluation · Blind Reader", "/how-it-works": "How it works · Blind Reader" }[current];
  if (current === "/evaluation") renderEvaluation();
  if (current === "/how-it-works") renderHowItWorks();
  $("#main").focus({ preventScroll: true });
  window.scrollTo(0, 0);
}
window.addEventListener("hashchange", route);

/* ===================== Model status ===================== */
let modelsReady = false;
let modelNames = {};
async function pollStatus() {
  const pill = $("#model-status");
  try {
    const s = await (await fetch("/api/status")).json();
    modelNames = s.models;
    if (s.error) {
      pill.className = "status-pill failed";
      pill.querySelector(".label").textContent = "AI models failed to load";
      return;
    }
    if (s.ready) {
      modelsReady = true;
      pill.className = "status-pill ready";
      pill.querySelector(".label").textContent = "Ready";
      return;
    }
  } catch { /* server restarting */ }
  setTimeout(pollStatus, 2000);
}

/* ===================== Choosing a photo ===================== */
const fileInput = $("#file-input");
const cameraInput = $("#camera-input");
$("#pick-btn").addEventListener("click", (e) => { e.stopPropagation(); fileInput.click(); });
$("#camera-btn").addEventListener("click", (e) => { e.stopPropagation(); cameraInput.click(); });
$("#change-btn").addEventListener("click", () => fileInput.click());
const dropzone = $("#dropzone");
dropzone.addEventListener("click", () => fileInput.click());
dropzone.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); fileInput.click(); } });
[fileInput, cameraInput].forEach((inp) => inp.addEventListener("change", () => { if (inp.files[0]) handleFile(inp.files[0]); inp.value = ""; }));
["dragenter", "dragover"].forEach((ev) => dropzone.addEventListener(ev, (e) => { e.preventDefault(); dropzone.classList.add("dragging"); }));
["dragleave", "drop"].forEach((ev) => dropzone.addEventListener(ev, () => dropzone.classList.remove("dragging")));
dropzone.addEventListener("drop", (e) => { e.preventDefault(); const f = e.dataTransfer.files[0]; if (f) handleFile(f); });
document.addEventListener("paste", (e) => {
  const item = [...(e.clipboardData?.items || [])].find((i) => i.type.startsWith("image/"));
  if (item) { location.hash = "#/"; handleFile(item.getAsFile()); }
});

/* ===================== Describing ===================== */
let busy = false;
let stepTimer = null;

function show(id) {
  ["#empty-state", "#working", "#error", "#result"].forEach((s) => ($(s).hidden = s !== id));
  $("#result-card").setAttribute("aria-busy", String(id === "#working"));
}

function showError(message) {
  $("#error").innerHTML = `<strong>Something went wrong.</strong><br>${esc(message)}`;
  show("#error");
  speak(`Sorry. ${message}`);
}

function startSteps() {
  const items = [...document.querySelectorAll(".steps li")];
  items.forEach((li) => li.className = "");
  let i = 0;
  items[0].className = "active";
  // The server answers in one go; advance the visual steps at roughly the measured pace
  stepTimer = setInterval(() => {
    if (i < items.length - 1) { items[i].className = "done"; i += 1; items[i].className = "active"; }
  }, 6000);
}

// Phone photos are often over 10 MB, but the models only look at about 768 px,
// so large photos are shrunk (and turned upright) before upload
async function shrinkPhoto(file, maxSide = 2048) {
  try {
    const bmp = await createImageBitmap(file, { imageOrientation: "from-image" });
    const scale = Math.min(1, maxSide / Math.max(bmp.width, bmp.height));
    if (scale === 1 && file.size <= 4 * 1024 * 1024) return file;
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(bmp.width * scale);
    canvas.height = Math.round(bmp.height * scale);
    canvas.getContext("2d").drawImage(bmp, 0, 0, canvas.width, canvas.height);
    const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.92));
    return blob ? new File([blob], (file.name || "photo").replace(/\.\w+$/, "") + ".jpg", { type: "image/jpeg" }) : file;
  } catch {
    return file; // formats the browser cannot decode go to the server unchanged
  }
}

async function handleFile(file) {
  if (busy) return;
  if (!file.type.startsWith("image/")) { showError("Please choose an image file, such as a JPG or PNG photo."); return; }
  file = await shrinkPhoto(file);
  if (file.size > 10 * 1024 * 1024) { showError("This image is larger than 10 MB. Please choose a smaller photo."); return; }

  stopSpeaking();
  $("#preview-img").src = URL.createObjectURL(file);
  $("#preview-name").textContent = file.name || "Pasted image";
  $("#preview").hidden = false;
  dropzone.hidden = true;

  if (!modelsReady) {
    $("#working h2").textContent = "Getting the AI models ready…";
    show("#working");
    while (!modelsReady && !$("#model-status").classList.contains("failed")) await new Promise((r) => setTimeout(r, 1000));
  }
  $("#working h2").textContent = "Looking at your photo…";

  busy = true;
  show("#working");
  startSteps();
  // Single-column layout: the result card sits below the photo, so bring it into view
  if (matchMedia("(max-width: 900px)").matches) $("#result-card").scrollIntoView({ behavior: "smooth", block: "start" });
  speakIfAllowed("Describing your photo. This takes a few seconds.");
  const started = performance.now();
  try {
    const body = new FormData();
    body.append("image", file);
    const res = await fetch("/api/describe", { method: "POST", body });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || `The server answered ${res.status}.`);
    renderResult(data, (performance.now() - started) / 1000);
  } catch (err) {
    showError(err.message === "Failed to fetch" ? "Could not reach the app. Is the server still running?" : err.message);
  } finally {
    clearInterval(stepTimer);
    busy = false;
  }
}

let lastResult = null;
function renderResult(data, seconds) {
  lastResult = data;
  $("#summary").textContent = data.summary;
  $("#description").textContent = data.description;
  $("#unclear").hidden = !data.unclear;
  $("#retake-tip").textContent = data.retake_tip || "";
  $("#text-found").hidden = !data.text_lines.length;
  $("#text-lines").innerHTML = data.text_lines.map((l) => `<li>${esc(l)}</li>`).join("");
  $("#meta").textContent = `Described in ${seconds.toFixed(1)} s · Summary: ${modelNames.summary || "BLIP"} · Details: ${modelNames.description || "Florence-2"}`;
  show("#result");
  if ($("#autoplay").checked) speak(data.speech);
}

/* ===================== Reading aloud (Web Speech API, runs offline with the system voices) ===================== */
const synth = window.speechSynthesis;
let voice = null;
function pickVoice() {
  if (!synth) return;
  const voices = synth.getVoices();
  // Prefer voices that run on this device so the text is not sent to an online speech service
  voice = voices.find((v) => v.localService && v.lang.startsWith("en") && v.default)
       || voices.find((v) => v.localService && v.lang.startsWith("en"))
       || voices.find((v) => v.lang.startsWith("en")) || null;
}
if (synth) { pickVoice(); synth.addEventListener?.("voiceschanged", pickVoice); }

const playBtn = $("#play-btn");
function setPlaying(on) {
  playBtn.classList.toggle("playing", on);
  playBtn.setAttribute("aria-pressed", String(on));
  playBtn.querySelector("span").textContent = on ? "Pause" : (synth?.paused ? "Resume" : "Read aloud");
}
function speak(text) {
  if (!synth || !text) return;
  synth.cancel();
  const u = new SpeechSynthesisUtterance(text);
  if (voice) u.voice = voice;
  u.rate = Number($("#speed").value);
  u.onend = u.onerror = () => setPlaying(false);
  synth.speak(u);
  setPlaying(true);
}
function speakIfAllowed(text) { if ($("#autoplay").checked) speak(text); }
function stopSpeaking() { synth?.cancel(); setPlaying(false); }

playBtn.addEventListener("click", () => {
  if (!synth) { alert("This browser cannot read aloud. Try Chrome, Edge or Firefox."); return; }
  if (synth.speaking && !synth.paused) { synth.pause(); setPlaying(false); playBtn.querySelector("span").textContent = "Resume"; }
  else if (synth.paused) { synth.resume(); setPlaying(true); }
  else if (lastResult) speak(lastResult.speech);
});
$("#stop-btn").addEventListener("click", stopSpeaking);
$("#speed").addEventListener("change", () => { store.set("speed", $("#speed").value); if (synth?.speaking && lastResult) speak(lastResult.speech); });
$("#autoplay").addEventListener("change", () => store.set("autoplay", $("#autoplay").checked));
$("#copy-btn").addEventListener("click", async () => {
  if (!lastResult) return;
  const text = [lastResult.summary, lastResult.description, ...lastResult.text_lines].join("\n\n");
  try { await navigator.clipboard.writeText(text); $("#copy-btn").textContent = "Copied"; setTimeout(() => ($("#copy-btn").textContent = "Copy text"), 1500); }
  catch { /* clipboard blocked */ }
});
$("#speed").value = store.get("speed", "1");
$("#autoplay").checked = store.get("autoplay", true);

/* ===================== Evaluation page ===================== */
const pct = (x) => `${(x * 100).toFixed(1)}%`;
const fix = (x, d = 3) => Number(x).toFixed(d);
let evalLoaded = false;

async function renderEvaluation() {
  if (evalLoaded) return;
  const root = $("#eval-root");
  let r;
  try {
    const res = await fetch("/api/eval");
    if (!res.ok) throw new Error((await res.json()).detail);
    r = await res.json();
  } catch (e) {
    root.innerHTML = `<div class="card"><h2>Evaluation not available yet</h2><p class="muted">${esc(e.message)}</p></div>${metricGuide()}`;
    return;
  }
  evalLoaded = true;
  const names = Object.keys(r.models);
  const M = r.models;
  const base = M["Original BLIP"];
  const ours = M["Fine-tuned BLIP (ours)"];
  const flo = M["Florence-2 (short caption)"];
  const delta = (a, b, lowerBetter = false) => {
    const change = (a - b) / Math.abs(b || 1);
    const good = lowerBetter ? change < 0 : change > 0;
    return `<span class="delta ${good ? "up" : "down"}">${change > 0 ? "+" : ""}${(change * 100).toFixed(0)}% vs original</span>`;
  };

  const capMetrics = ["BLEU-1", "BLEU-4", "ROUGE-L", "CIDEr"];
  const bestOf = (m) => Math.max(...names.map((n) => M[n].caption[m]));
  const capRows = names.map((n) => `<tr><th scope="row">${esc(n)}</th>${capMetrics.map((m) => {
    const v = M[n].caption[m];
    return `<td class="num ${v === bestOf(m) ? "best" : ""}">${fix(v)}<div class="bar"><span style="width:${(v / bestOf(m)) * 100}%"></span></div></td>`;
  }).join("")}<td class="num">${M[n].avg_words.toFixed(1)}</td><td class="num">${M[n].seconds_per_photo.toFixed(1)} s</td></tr>`).join("");

  const matrix = (n) => {
    const q = M[n].quality_check;
    return `<div class="card"><h3>${esc(n)}</h3>
      <div class="matrix" role="table" aria-label="Confusion matrix for ${esc(n)}">
        <div class="h"></div><div class="h">Model: unreadable</div><div class="h">Model: readable</div>
        <div class="h">Human: unreadable</div><div class="ok"><b>${q.tp}</b>caught</div><div class="no"><b>${q.fn}</b>missed</div>
        <div class="h">Human: readable</div><div class="no"><b>${q.fp}</b>false alarm</div><div class="ok"><b>${q.tn}</b>correct</div>
      </div>
      <p class="small">Accuracy <b>${pct(q.accuracy)}</b> · Precision <b>${pct(q.precision)}</b> · Recall <b>${pct(q.recall)}</b> · F1 <b>${pct(q.f1)}</b></p></div>`;
  };

  const examples = r.examples.slice(0, 10).map((e) => `<tr><td>${esc(e.human)}</td>${names.map((n) => `<td>${esc(e[n])}</td>`).join("")}</tr>`).join("");

  root.innerHTML = `
    <div class="kpis">
      <div class="kpi"><div class="label">Test photos (never seen in training)</div><div class="value">${r.photos}</div><div class="small muted">${r.photos_marked_unreadable_by_humans} marked too blurry by humans</div></div>
      <div class="kpi"><div class="label">Held-out loss, fine-tuned (lower is better)</div><div class="value">${fix(ours.held_out_loss, 2)}</div>${delta(ours.held_out_loss, base.held_out_loss, true)}</div>
      <div class="kpi"><div class="label">CIDEr, fine-tuned (higher is better)</div><div class="value">${fix(ours.caption.CIDEr, 2)}</div>${delta(ours.caption.CIDEr, base.caption.CIDEr)}</div>
      <div class="kpi"><div class="label">"Too blurry" detection, F1 (as used in the app)</div><div class="value">${pct((r.calibration ? r.calibration.test_half : ours.quality_check).f1)}</div><div class="small muted">original model: ${pct(base.quality_check.f1)}</div></div>
    </div>

    <div class="section">
      <h2>1 · Caption quality</h2>
      <p class="intro">Each model wrote one short caption per test photo. Each caption was compared word by word with the human's caption for the same photo. The best score in each column is highlighted.</p>
      <div class="table-wrap"><table>
        <thead><tr><th>Model</th>${capMetrics.map((m) => `<th>${m}</th>`).join("")}<th>Avg words</th><th>Time / photo (CPU)</th></tr></thead>
        <tbody>${capRows}</tbody></table></div>
    </div>

    <div class="section">
      <h2>2 · How well the model knows the photo (held-out loss)</h2>
      <p class="intro">Instead of generating a caption, we ask: how surprised is the model by the human's real caption? Lower means the model's understanding is closer to the human's. This is the number training tries to reduce.</p>
      <div class="table-wrap"><table>
        <thead><tr><th>Model</th><th>Held-out loss</th><th>Perplexity</th><th>Meaning</th></tr></thead>
        <tbody>${["Original BLIP", "Fine-tuned BLIP (ours)"].map((n) => `<tr><th scope="row">${n}</th><td class="num">${fix(M[n].held_out_loss)}</td><td class="num">${fix(M[n].perplexity, 1)}</td><td>On average the model hesitates between about <b>${Math.round(M[n].perplexity)}</b> likely words at each step of the human caption.</td></tr>`).join("")}</tbody>
      </table></div>
    </div>

    <div class="section">
      <h2>3 · Detecting photos that are too blurry to describe</h2>
      <p class="intro">About 1 in 7 photos taken by blind people are too blurry, dark or badly framed to describe. Humans labelled those "Quality issues are too severe to recognize visual content". This is a yes/no decision, so it can be scored with classic accuracy.</p>
      <div class="matrix-grid">${names.map(matrix).join("")}</div>
    </div>

    ${r.calibration ? calibrationSection(r.calibration) : ""}

    <div class="section">
      <h2>5 · Side-by-side examples</h2>
      <p class="intro">The first test photos, exactly as each model captioned them. The full list for all ${r.photos} photos is in <code>eval/predictions.csv</code>.</p>
      <div class="table-wrap"><table>
        <thead><tr><th>Human caption</th>${names.map((n) => `<th>${esc(n)}</th>`).join("")}</tr></thead>
        <tbody>${examples}</tbody></table></div>
    </div>

    <div class="section">
      <h2>6 · What these results mean</h2>
      <div class="callout">${interpretation(base, ours, flo, r.calibration)}</div>
    </div>
    ${metricGuide()}
    <p class="small muted section">Data: ${esc(r.dataset)}. Reproduce with <code>python training/evaluate.py</code>.</p>`;
}

function calibrationSection(cal) {
  // Small dependency-free SVG line chart of precision / recall / F1 against the threshold
  const W = 640, H = 260, L = 44, B = 36, T = 14, R = 14;
  const x = (t) => L + ((t - 0.05) / 0.9) * (W - L - R);
  const y = (v) => T + (1 - v) * (H - T - B);
  const line = (key) => cal.curve.map((p, i) => `${i ? "L" : "M"}${x(p.threshold).toFixed(1)},${y(p[key]).toFixed(1)}`).join(" ");
  const series = [["precision", "var(--good)", "Precision"], ["recall", "#f59e0b", "Recall"], ["f1", "var(--brand)", "F1"]];
  const grid = [0, 0.25, 0.5, 0.75, 1].map((v) => `<line x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}" stroke="var(--border)"/><text x="${L - 8}" y="${y(v) + 4}" text-anchor="end" font-size="11" fill="var(--muted)">${v * 100}%</text>`).join("");
  const xt = [0.1, 0.3, 0.5, 0.7, 0.9].map((t) => `<text x="${x(t)}" y="${H - B + 18}" text-anchor="middle" font-size="11" fill="var(--muted)">${t}</text>`).join("");
  const old = cal.test_half_caption_rule, now = cal.test_half;
  const row = (label, q) => `<tr><th scope="row">${label}</th><td class="num">${q.tp}</td><td class="num">${q.fp}</td><td class="num">${q.fn}</td><td class="num">${pct(q.precision)}</td><td class="num">${pct(q.recall)}</td><td class="num"><b>${pct(q.f1)}</b></td></tr>`;
  return `<div class="section">
    <h2>4 · Calibrating the "too blurry" decision</h2>
    <p class="intro">Instead of trusting the model's first words, the app asks <b>how sure</b> the model is that a photo is unreadable (a probability from 0 to 1) and flags it only above a threshold. Too low a threshold gives many false alarms; too high misses blurry photos. We tried thresholds from 0.05 to 0.95 on <b>${cal.tuned_on} photos</b>, picked the one with the best F1 (<b>${cal.threshold}</b>), and report the result on the <b>other ${cal.reported_on} photos</b>, which were never used to pick it. That keeps the score honest.</p>
    <div class="card">
      <svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="Precision, recall and F1 for each threshold. The chosen threshold is ${cal.threshold}.">
        ${grid}${xt}
        <text x="${(W + L) / 2}" y="${H - 4}" text-anchor="middle" font-size="12" fill="var(--muted)">threshold (how sure the model must be)</text>
        <line x1="${x(cal.threshold)}" x2="${x(cal.threshold)}" y1="${T}" y2="${H - B}" stroke="var(--ink-2)" stroke-dasharray="4 4"/>
        <text x="${x(cal.threshold) + 6}" y="${T + 12}" font-size="12" fill="var(--ink-2)">chosen: ${cal.threshold}</text>
        ${series.map(([k, c]) => `<path d="${line(k)}" fill="none" stroke="${c}" stroke-width="3" stroke-linejoin="round"/>`).join("")}
      </svg>
      <p class="small">${series.map(([, c, n]) => `<span style="display:inline-flex;align-items:center;gap:.35rem;margin-right:1rem"><span style="width:14px;height:4px;border-radius:2px;background:${c}"></span>${n}</span>`).join("")}</p>
    </div>
    <div class="table-wrap section" style="margin-top:1rem"><table>
      <thead><tr><th>Rule (on the ${cal.reported_on} report photos)</th><th>Caught</th><th>False alarms</th><th>Missed</th><th>Precision</th><th>Recall</th><th>F1</th></tr></thead>
      <tbody>${row("Before: trust the caption's first words", old)}${row(`After: probability ≥ ${cal.threshold} (used by the app)`, now)}</tbody>
    </table></div>
  </div>`;
}

function interpretation(base, ours, flo, cal) {
  const lossDrop = ((base.held_out_loss - ours.held_out_loss) / base.held_out_loss) * 100;
  const q = ours.quality_check;
  const fixNote = cal
    ? `Calibrating the decision (section 4) changes this: on photos not used for tuning, F1 goes from ${pct(cal.test_half_caption_rule.f1)} to ${pct(cal.test_half.f1)}, with ${cal.test_half.fp} false alarms instead of ${cal.test_half_caption_rule.fp}.`
    : "";
  return `<p><b>Fine-tuning worked on what it was trained for.</b> On photos it never saw, the fine-tuned BLIP's held-out loss is ${lossDrop.toFixed(0)}% lower than the original's (${fix(base.held_out_loss, 2)} → ${fix(ours.held_out_loss, 2)}). Its captions match human wording better, with CIDEr going from ${fix(base.caption.CIDEr, 2)} to ${fix(ours.caption.CIDEr, 2)}, and it learned to flag unreadable photos: it catches ${q.tp} of ${q.tp + q.fn} (recall ${pct(q.recall)}), where the original model catches ${base.quality_check.tp}.</p>
  <p><b>Its first weak spot was false alarms.</b> Trusting its caption's first words, it called ${q.fp} readable photos "too blurry" (precision ${pct(q.precision)}). ${fixNote} The app also never stops at a warning: it suggests retaking the photo and still gives the full description from Florence-2.</p>
  <p><b>Florence-2 writes the detailed description</b> because it describes many more objects, positions and any text. Its short captions score ${fix(flo.caption.CIDEr, 2)} CIDEr here. Its long, detailed descriptions cannot be scored fairly against one-sentence human captions (see "Why the detailed description is not in this table" below).</p>`;
}

function metricGuide() {
  return `<div class="section">
    <h2>How each number is calculated</h2>
    <p class="intro">Image captioning has no single "accuracy %", because many different sentences can describe the same photo correctly. Researchers use several complementary scores. Here is what each one measures, in plain words.</p>
    <div class="explain">
      <div class="card"><h3>BLEU-1 and BLEU-4</h3>
        <p>Counts how many word sequences in the model's caption also appear in the human caption. BLEU-1 looks at single words, BLEU-4 at runs of up to 4 words in a row (much stricter). Captions that are too short get a penalty.</p>
        <div class="formula">precision_n = matching n-word chunks / n-word chunks in model caption
BLEU-4 = brevity_penalty × (p1 × p2 × p3 × p4)^(1/4)</div>
        <p><b>Example:</b> human "a cat on a red couch", model "a cat on a couch". All 5 model words appear in the human caption, so p1 = 5/5. But "a couch" never appears as a pair, so p2 = 3/4. Range 0–1, higher is better.</p></div>
      <div class="card"><h3>ROUGE-L</h3>
        <p>Finds the <b>longest common subsequence</b>: the longest list of words that appear in both captions in the same order, even with gaps. It is more forgiving than BLEU about extra words in between.</p>
        <div class="formula">R = LCS / human words,  P = LCS / model words
ROUGE-L = (1 + β²)·R·P / (R + β²·P)   (β = 1.2)</div>
        <p><b>Example:</b> "a cat on a red couch" vs "a cat on a couch" share "a cat on a couch" (5 words): R = 5/6, P = 5/5. Range 0–1.</p></div>
      <div class="card"><h3>CIDEr: the main captioning score</h3>
        <p>Like BLEU, but each word is weighted by how <b>informative</b> it is across all test photos (TF-IDF). Common words like "a" or "the" count very little. Specific words like "Pepsi", "remote" or "medicine" count a lot. It then measures how similar the weighted captions are (cosine similarity) for 1- to 4-word chunks and averages them.</p>
        <div class="formula">CIDEr = 10 × average over n=1..4 of cosine(TF-IDF(model), TF-IDF(human))</div>
        <p>It was designed for captioning and agrees best with human judgement. Range 0 to about 10. Published models reach about 1.0–1.4 on standard benchmarks with 5 human captions per photo. Ours are compared against only 1 human caption, so expect lower numbers.</p></div>
      <div class="card"><h3>Held-out loss and perplexity</h3>
        <p>We give the model the photo and the human's real caption and measure, word by word, how much probability it gave each correct next word. Loss is the average of −log(probability). It is the exact number training minimises, measured here on photos the model never trained on.</p>
        <div class="formula">loss = average over words of −ln P(correct word | photo, previous words)
perplexity = e^loss</div>
        <p><b>Perplexity</b> turns loss into something intuitive: the model is "as unsure as if choosing between that many equally likely words". Lower is better.</p></div>
      <div class="card"><h3>Accuracy, precision, recall, F1</h3>
        <p>Used for the yes/no "is this photo too blurry?" decision. <b>Precision:</b> when the model says "too blurry", how often is it right? <b>Recall:</b> of all photos that really are too blurry, how many did it catch? <b>F1</b> balances the two.</p>
        <div class="formula">accuracy  = (caught + correct) / all photos
precision = caught / (caught + false alarms)
recall    = caught / (caught + missed)
F1        = 2·P·R / (P + R)</div>
        <p>Accuracy alone can mislead: a model that <i>never</i> says "too blurry" still scores about 87% here because most photos are fine. That is why precision and recall matter.</p></div>
      <div class="card"><h3>Why the detailed description is not in this table</h3>
        <p>BLEU, ROUGE and CIDEr compare a caption against short human captions (about 10 words). Florence-2's detailed description is 60–100 words and mentions things the human never wrote, like "two white remote controls", so it would be <b>penalised for being more detailed</b>. Scoring long descriptions fairly needs either several long human descriptions per photo or human raters, which this dataset does not have.</p>
        <p>So we score Florence-2's <i>short</i> caption mode for a fair comparison and show its detailed output qualitatively in the app.</p></div>
    </div></div>`;
}

/* ===================== How it works page ===================== */
let howLoaded = false;
function renderHowItWorks() {
  if (howLoaded) return;
  howLoaded = true;
  $("#how-root").innerHTML = `
    <div class="pipeline" aria-label="Processing pipeline">
      <div class="stage"><div class="num">1</div><h3>Photo</h3><p>Uploaded, taken with the camera, dropped or pasted. It is sent only to the app's own server on this computer.</p></div>
      <div class="stage"><div class="num">2</div><h3>Summary + quality check</h3><p><b>BLIP fine-tuned on VizWiz</b> writes a one-line summary and estimates how likely the photo is too blurry. Above a calibrated threshold, the user is warned.</p></div>
      <div class="stage"><div class="num">3</div><h3>Detailed description</h3><p><b>Florence-2</b> describes everything: objects, people, colours, positions.</p></div>
      <div class="stage"><div class="num">4</div><h3>Text reading</h3><p>If the description mentions text, Florence-2's <b>OCR</b> reads it line by line.</p></div>
      <div class="stage"><div class="num">5</div><h3>Speech</h3><p>The browser reads it aloud with the computer's built-in voice, with pause and speed controls.</p></div>
    </div>

    <div class="section"><h2>The models</h2>
      <div class="table-wrap"><table>
        <thead><tr><th>Job</th><th>Model</th><th>Size</th><th>Why this one</th></tr></thead>
        <tbody>
          <tr><td>Summary & "too blurry" check</td><td><a href="https://huggingface.co/adityawagh07/blip-vizwiz">adityawagh07/blip-vizwiz</a><br><span class="small muted">our fine-tune of Salesforce/blip-image-captioning-base</span></td><td>~0.25B parameters</td><td>BLIP is a proven image-captioning model. We fine-tuned it on photos taken by blind people so it handles blur, odd angles and knows when it cannot see.</td></tr>
          <tr><td>Detailed description & text reading</td><td><a href="https://huggingface.co/florence-community/Florence-2-base">Microsoft Florence-2 base</a></td><td>~0.23B parameters</td><td>One small model that does detailed captions <i>and</i> OCR. MIT licensed, runs on a laptop CPU.</td></tr>
          <tr><td>Speech</td><td>Web Speech API (browser)</td><td>built in</td><td>Instant, offline system voices, with pause, resume and speed. No audio files to generate.</td></tr>
        </tbody></table></div>
    </div>

    <div class="section"><h2>How the fine-tuning was done</h2>
      <div class="explain">
        <div class="card"><h3>Data: VizWiz-Captions</h3>
          <p>Real photos taken by blind people with their phones, each described by a human (<a href="https://huggingface.co/datasets/lmms-lab/VizWiz-Caps">lmms-lab/VizWiz-Caps</a>). We used the 7,750 photos that have captions and split them, with a fixed random seed of 42, into:</p>
          <ul><li><b>7,362 for training</b>: the model learns from these.</li><li><b>388 held out</b>: never shown during training, used only to test.</li></ul>
          <p>Holding photos out is what makes the test honest. A model can memorise its training photos, so it must be scored on new ones.</p></div>
        <div class="card"><h3>Training run</h3>
          <ul>
            <li>Free Google Colab <b>Tesla T4 GPU</b>, 27.5 minutes</li>
            <li><b>3 epochs</b> (3 passes over the data) = 1,383 steps of 16 photos</li>
            <li>Learning rate 5e-5 with warm-up, weight decay 0.01, fp16 mixed precision</li>
            <li>Held-out loss checked after each epoch: <b>2.326 → 2.291 → 2.338</b></li>
            <li>Epoch 3 got worse (the model began memorising), so the <b>epoch-2 version was kept</b> automatically</li>
            <li>Published to the Hugging Face Hub and downloaded by this app</li>
          </ul>
          <p class="small muted">Code: <code>training/finetune_blip.py</code> and <code>training/finetune_blip_colab.ipynb</code></p></div>
        <div class="card"><h3>What "training" actually changes</h3>
          <p>For each photo, the model predicts the human's caption one word at a time. The <b>loss</b> measures how wrong those predictions were. Backpropagation then nudges the model's ~250 million numbers (weights) slightly so the next prediction is a little better. Repeated 1,383 times, the model adapts to blind users' photos.</p></div>
        <div class="card"><h3>What it learned, honestly</h3>
          <p><b>Better:</b> lower held-out loss, captions closer to human wording, and it now recognises unreadable photos.</p>
          <p><b>Trade-off we found and fixed:</b> about 1 in 7 training captions is the same sentence, "Quality issues are too severe…", so the model learned to say it even when only ~10% sure, and called sharp photos blurry. We now use the model's <i>probability</i> with a threshold calibrated on held-out photos (Evaluation page, section 4). The app also warns instead of refusing, and Florence-2 still describes the photo.</p></div>
      </div>
    </div>

    <div class="section"><h2>Technology stack</h2>
      <div class="table-wrap"><table><tbody>
        <tr><th scope="row">Models & inference</th><td>Python, PyTorch, Hugging Face Transformers</td></tr>
        <tr><th scope="row">Training</th><td>Hugging Face Trainer & Datasets, Google Colab T4, TensorBoard for live charts</td></tr>
        <tr><th scope="row">Evaluation</th><td>pycocoevalcap (BLEU, ROUGE-L, CIDEr), custom held-out loss and classification metrics: <code>training/evaluate.py</code></td></tr>
        <tr><th scope="row">Backend</th><td>FastAPI + Uvicorn: <code>app.py</code> serves the website and the <code>/api/describe</code> endpoint</td></tr>
        <tr><th scope="row">Frontend</th><td>Plain HTML, CSS and JavaScript (no framework, no build step), Web Speech API</td></tr>
        <tr><th scope="row">Model hosting</th><td>Hugging Face Hub (free): <a href="https://huggingface.co/adityawagh07/blip-vizwiz">adityawagh07/blip-vizwiz</a></td></tr>
        <tr><th scope="row">Code</th><td>GitHub: <a href="https://github.com/AdityaWagh06/Blind_reader_app">AdityaWagh06/Blind_reader_app</a></td></tr>
      </tbody></table></div>
    </div>

    <div class="section faq"><h2>Questions people ask</h2>
      <details><summary>Does it use ChatGPT or any paid API?</summary><p>No. All models are open-source and run on your own computer. The internet is only used once, to download the model weights from Hugging Face.</p></details>
      <details><summary>Is my photo uploaded anywhere?</summary><p>No. The browser sends it to the app's own server running on the same computer (127.0.0.1). It is processed in memory and not saved.</p></details>
      <details><summary>Why use two models instead of one?</summary><p>Each does what it is best at. Our fine-tuned BLIP is specialised for blind users' photos and spotting unreadable ones. Florence-2 gives much richer detail and can read text. Using both gives a quick summary, a safety warning and a detailed description.</p></details>
      <details><summary>Why did you fine-tune instead of training from scratch?</summary><p>Training a vision-language model from scratch needs millions of images and expensive hardware. Fine-tuning starts from BLIP, which already understands images, and adapts it with 7,362 specialised photos in under 30 minutes on a free GPU. This is called transfer learning.</p></details>
      <details><summary>How do you know the model is not just memorising?</summary><p>All test scores use 388 photos that were never shown during training. We also watched the held-out loss after every epoch and kept the best epoch, before the model started to overfit.</p></details>
      <details><summary>What is the biggest limitation?</summary><p>Detailed descriptions can occasionally contain small mistakes (for example a wrong colour or count), and the blurry-photo check still makes some mistakes in both directions. The Evaluation page shows exactly how many. Captions were scored against one human caption per photo, so absolute scores are lower than published benchmarks that use five.</p></details>
      <details><summary>What is calibration, and why did you need it?</summary><p>A model's single best answer can hide how unsure it is. Our model often answered "quality issues…" while being only about 10% sure, because that exact sentence was very common in training. Calibration means choosing, from data, how sure the model must be before we act on its answer. We picked the threshold on half of the held-out photos and measured it on the other half, so the reported improvement is not tuned on its own test data.</p></details>
      <details><summary>How fast is it?</summary><p>About 10–25 seconds per photo on a laptop CPU, mostly for the detailed description. With a GPU it takes 1–3 seconds.</p></details>
      <details><summary>How would you improve it next?</summary><p>Balance the training data so "too blurry" is predicted less often, train on all 5 human captions per VizWiz photo, use the larger Florence-2 model on a GPU, and run a study with blind users to rate the descriptions.</p></details>
    </div>`;
}

/* ===================== Start ===================== */
route();
pollStatus();

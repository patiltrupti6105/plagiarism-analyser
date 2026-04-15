/**
 * main.js — PlagiaGuard Frontend Controller
 *
 * Handles:
 *  - Drag-and-drop / click-to-upload for source + reference files
 *  - AJAX form submission to /analyze
 *  - Animated results rendering (score ring, flagged sentences, etc.)
 *  - Error toasts
 */

"use strict";

// ─────────────────────────────────────────────────────────────────────────────
// State
// ─────────────────────────────────────────────────────────────────────────────

const state = {
  sourceFile:     null,   // File object
  referenceFiles: [],     // Array<File>
  maxRefs:        5,
};


// ─────────────────────────────────────────────────────────────────────────────
// DOM References
// ─────────────────────────────────────────────────────────────────────────────

const $ = id => document.getElementById(id);

const sourceZone    = $("sourceZone");
const sourceInput   = $("sourceInput");
const sourcePreview = $("sourcePreview");

const refZone        = $("refZone");
const refInput       = $("refInput");
const refPreviewList = $("refPreviewList");

const analyzeBtn    = $("analyzeBtn");
const resetBtn      = $("resetBtn");
const loadingState  = $("loadingState");
const uploadSection = $("uploadSection");
const actionBar     = $("actionBar");
const resultsSection = $("resultsSection");
const reanalyzeBtn  = $("reanalyzeBtn");

const errorToast = $("errorToast");
const toastMsg   = $("toastMsg");


// ─────────────────────────────────────────────────────────────────────────────
// File Validation
// ─────────────────────────────────────────────────────────────────────────────

const ALLOWED = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"];
const ALLOWED_EXT = ["pdf", "docx", "txt"];

function isValidFile(file) {
  const ext = file.name.split(".").pop().toLowerCase();
  return ALLOWED_EXT.includes(ext) || ALLOWED.includes(file.type);
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}


// ─────────────────────────────────────────────────────────────────────────────
// Source File Handling
// ─────────────────────────────────────────────────────────────────────────────

function setupDropZone(zone, input, handler) {
  zone.addEventListener("click", () => input.click());

  zone.addEventListener("dragover", e => {
    e.preventDefault();
    zone.classList.add("dragover");
  });

  zone.addEventListener("dragleave", () => zone.classList.remove("dragover"));

  zone.addEventListener("drop", e => {
    e.preventDefault();
    zone.classList.remove("dragover");
    if (e.dataTransfer.files.length) handler(e.dataTransfer.files);
  });

  input.addEventListener("change", () => {
    if (input.files.length) handler(input.files);
    input.value = "";    // reset so same file can be re-selected
  });
}

function handleSourceFiles(files) {
  const file = files[0];
  if (!isValidFile(file)) {
    showToast("Invalid file type. Please upload PDF, DOCX, or TXT.");
    return;
  }
  if (file.size > 10 * 1024 * 1024) {
    showToast("File too large. Maximum size is 10 MB.");
    return;
  }

  state.sourceFile = file;
  sourcePreview.textContent = `${file.name}  (${formatSize(file.size)})`;
  sourcePreview.style.display = "flex";
  sourceZone.classList.add("has-file");

  // Hide drop hints
  sourceZone.querySelector(".drop-title").textContent = "Source document loaded";
  sourceZone.querySelector(".drop-sub").textContent   = "Click to replace";
  sourceZone.querySelector(".drop-icon").textContent  = "✓";
  sourceZone.querySelector(".drop-icon").style.color  = "var(--teal)";

  updateAnalyzeBtn();
}

function handleReferenceFiles(files) {
  const incoming = Array.from(files).filter(f => {
    if (!isValidFile(f)) { showToast(`Skipped: ${f.name} (invalid type)`); return false; }
    if (f.size > 10 * 1024 * 1024) { showToast(`Skipped: ${f.name} (too large)`); return false; }
    // Avoid duplicates
    if (state.referenceFiles.some(r => r.name === f.name && r.size === f.size)) return false;
    return true;
  });

  const remaining = state.maxRefs - state.referenceFiles.length;
  if (incoming.length > remaining) {
    showToast(`Max ${state.maxRefs} reference files. ${incoming.length - remaining} skipped.`);
  }
  state.referenceFiles.push(...incoming.slice(0, remaining));
  renderRefPreviews();
  updateAnalyzeBtn();
}

function renderRefPreviews() {
  refPreviewList.innerHTML = "";
  state.referenceFiles.forEach((f, i) => {
    const item = document.createElement("div");
    item.className = "ref-preview-item";
    item.innerHTML = `
      <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
        ${f.name} (${formatSize(f.size)})
      </span>
      <span class="ref-remove" data-index="${i}" title="Remove">✕</span>
    `;
    refPreviewList.appendChild(item);
  });

  refPreviewList.querySelectorAll(".ref-remove").forEach(btn => {
    btn.addEventListener("click", e => {
      e.stopPropagation();
      state.referenceFiles.splice(parseInt(btn.dataset.index), 1);
      renderRefPreviews();
      updateAnalyzeBtn();
    });
  });

  if (state.referenceFiles.length > 0) {
    refZone.classList.add("has-file");
    refZone.querySelector(".drop-title").textContent =
      `${state.referenceFiles.length} reference file${state.referenceFiles.length > 1 ? "s" : ""} loaded`;
    refZone.querySelector(".drop-sub").textContent = "Click or drop to add more";
  } else {
    refZone.classList.remove("has-file");
    refZone.querySelector(".drop-title").textContent = "Add reference files";
    refZone.querySelector(".drop-sub").textContent   = "Compare against known sources";
    refZone.querySelector(".drop-icon").textContent  = "⊕";
  }
}

setupDropZone(sourceZone, sourceInput, handleSourceFiles);
setupDropZone(refZone,    refInput,    handleReferenceFiles);


// ─────────────────────────────────────────────────────────────────────────────
// Analyze Button State
// ─────────────────────────────────────────────────────────────────────────────

function updateAnalyzeBtn() {
  const ready = state.sourceFile && state.referenceFiles.length > 0;
  analyzeBtn.disabled = !ready;
}


// ─────────────────────────────────────────────────────────────────────────────
// Reset
// ─────────────────────────────────────────────────────────────────────────────

function doReset() {
  state.sourceFile     = null;
  state.referenceFiles = [];

  sourcePreview.style.display = "none";
  sourcePreview.textContent   = "";
  sourceZone.classList.remove("has-file");
  sourceZone.querySelector(".drop-title").textContent = "Drop your document here";
  sourceZone.querySelector(".drop-sub").textContent   = "or click to browse";
  sourceZone.querySelector(".drop-icon").textContent  = "⬆";
  sourceZone.querySelector(".drop-icon").style.color  = "";

  refPreviewList.innerHTML = "";
  refZone.classList.remove("has-file");
  refZone.querySelector(".drop-title").textContent = "Add reference files";
  refZone.querySelector(".drop-sub").textContent   = "Compare against known sources";
  refZone.querySelector(".drop-icon").textContent  = "⊕";

  uploadSection.style.display  = "grid";
  actionBar.style.display      = "flex";
  loadingState.style.display   = "none";
  resultsSection.style.display = "none";
  updateAnalyzeBtn();
}

resetBtn.addEventListener("click", doReset);
reanalyzeBtn.addEventListener("click", doReset);


// ─────────────────────────────────────────────────────────────────────────────
// Analysis — API Call
// ─────────────────────────────────────────────────────────────────────────────

analyzeBtn.addEventListener("click", runAnalysis);

async function runAnalysis() {
  if (!state.sourceFile || state.referenceFiles.length === 0) return;

  // Show loading
  uploadSection.style.display = "none";
  actionBar.style.display     = "none";
  loadingState.style.display  = "block";
  animateLoadingSteps();

  // Build FormData
  const formData = new FormData();
  formData.append("source_file", state.sourceFile);
  state.referenceFiles.forEach(f => formData.append("reference_files", f));

  try {
    const res = await fetch("/analyze", { method: "POST", body: formData });
    const data = await res.json();

    if (!res.ok || data.error) {
      throw new Error(data.error || "Analysis failed. Please try again.");
    }

    loadingState.style.display = "none";
    renderResults(data);

  } catch (err) {
    loadingState.style.display = "none";
    uploadSection.style.display = "grid";
    actionBar.style.display    = "flex";
    showToast(err.message || "Network error. Please try again.");
  }
}


// ─────────────────────────────────────────────────────────────────────────────
// Loading Step Animator
// ─────────────────────────────────────────────────────────────────────────────

function animateLoadingSteps() {
  const steps = [$("step1"), $("step2"), $("step3"), $("step4")];
  let current = 0;

  // Reset all
  steps.forEach(s => s.className = "step");
  steps[0].classList.add("active");

  const interval = setInterval(() => {
    if (current < steps.length) {
      steps[current].classList.remove("active");
      steps[current].classList.add("done");
      current++;
      if (current < steps.length) steps[current].classList.add("active");
    } else {
      clearInterval(interval);
    }
  }, 900);
}


// ─────────────────────────────────────────────────────────────────────────────
// Results Renderer
// ─────────────────────────────────────────────────────────────────────────────

function renderResults(data) {
  const score       = data.plagiarism_percentage || 0;
  const original    = data.original_percentage  || 0;
  const risk        = data.risk_level           || "Low Risk";
  const flagged     = data.flagged_sentences    || [];
  const breakdown   = data.per_reference_breakdown || [];
  const reportFile  = data.report_filename;

  // ── Score Number ──
  const scoreNum = $("scoreNumber");
  animateCounter(scoreNum, score, "%");

  // ── Ring ──
  const ring = $("ringFill");
  const circumference = 502.6;
  const offset = circumference - (score / 100) * circumference;
  const riskClass = riskToClass(risk);
  ring.setAttribute("class", `ring-fill score-${riskClass}`);
  setTimeout(() => { ring.style.strokeDashoffset = offset; }, 100);
  scoreNum.className = `score-number risk-${riskClass}`;

  // ── Meta ──
  const originalEl = $("originalPct");
  originalEl.textContent = original + "%";
  originalEl.className = `meta-val risk-low`;

  const riskEl = $("riskLevel");
  riskEl.textContent = risk;
  riskEl.className   = `meta-val risk-${riskClass}`;

  $("flaggedCount").textContent = flagged.length;

  // ── Download ──
  if (reportFile) {
    $("downloadBtn").href = `/download/${encodeURIComponent(reportFile)}`;
  } else {
    $("downloadBtn").style.display = "none";
  }

  // ── Algorithm Breakdown ──
  const algoRows = $("algoRows");
  algoRows.innerHTML = "";
  if (breakdown.length > 0) {
    const ref = breakdown[0]; // Show first reference as representative
    renderAlgoRow(algoRows, "TF-IDF Cosine Similarity", ref.cosine_similarity, "bar-cosine");
    renderAlgoRow(algoRows, "Jaccard Shingling",        ref.jaccard_similarity, "bar-jaccard");
    renderAlgoRow(algoRows, "Blended Score",            ref.blended_score,      "bar-blended");
  }

  if (breakdown.length > 1) {
    const note = document.createElement("p");
    note.style.cssText = "font-size:0.72rem;color:var(--text-3);font-family:var(--mono);margin-top:10px";
    note.textContent = `Showing scores for Reference 1 of ${breakdown.length} references.`;
    algoRows.appendChild(note);
  }

  // ── Flagged Sentences ──
  const flaggedSection = $("flaggedSection");
  const flaggedList    = $("flaggedList");
  $("flaggedBadge").textContent = `${flagged.length} match${flagged.length !== 1 ? "es" : ""}`;

  if (flagged.length > 0) {
    flaggedSection.style.display = "block";
    flaggedList.innerHTML = "";
    flagged.forEach((item, i) => renderFlaggedItem(flaggedList, item, i + 1));
  } else {
    flaggedSection.style.display = "none";
  }

  // Show results
  resultsSection.style.display = "block";
  resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
}


function renderAlgoRow(container, label, value, barClass) {
  const clamped = Math.min(Math.max(value, 0), 100);
  const div = document.createElement("div");
  div.className = "algo-row";
  div.innerHTML = `
    <div class="algo-row-header">
      <span class="algo-row-label">${label}</span>
      <span class="algo-row-val">${clamped.toFixed(1)}%</span>
    </div>
    <div class="algo-bar-track">
      <div class="algo-bar-fill ${barClass}" style="width:0%" data-target="${clamped}"></div>
    </div>
  `;
  container.appendChild(div);
  // Animate bars after append
  requestAnimationFrame(() => {
    setTimeout(() => {
      div.querySelector(".algo-bar-fill").style.width = clamped + "%";
    }, 150);
  });
}


function renderFlaggedItem(container, item, index) {
  const score   = item.similarity || 0;
  const bgColor = score >= 80 ? "#ff4f6d" : score >= 60 ? "#ffb84c" : "#6c63ff";

  const div = document.createElement("div");
  div.className = "flagged-item";
  div.style.borderLeftColor = bgColor;
  div.innerHTML = `
    <div class="flagged-item-header">
      <span class="flagged-badge" style="background:${bgColor}22;color:${bgColor};border:1px solid ${bgColor}44">
        ${score}% match
      </span>
      <span class="flagged-idx">Passage #${index}</span>
    </div>
    <p class="flagged-sentence">${escapeHtml(item.sentence)}</p>
    <p class="flagged-match-label">Matched Reference Text</p>
    <p class="flagged-match-text">${escapeHtml((item.matched_with || "").substring(0, 250))}${(item.matched_with || "").length > 250 ? "…" : ""}</p>
  `;
  container.appendChild(div);
}


// ─────────────────────────────────────────────────────────────────────────────
// Utilities
// ─────────────────────────────────────────────────────────────────────────────

function riskToClass(risk) {
  if (risk === "Low Risk")      return "low";
  if (risk === "Moderate Risk") return "moderate";
  if (risk === "High Risk")     return "high";
  return "critical";
}

function animateCounter(el, target, suffix = "") {
  const duration = 1400;
  const start    = performance.now();
  function tick(now) {
    const progress = Math.min((now - start) / duration, 1);
    const ease     = 1 - Math.pow(1 - progress, 4); // easeOutQuart
    el.textContent = Math.round(ease * target) + suffix;
    if (progress < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

let toastTimer = null;
function showToast(msg) {
  toastMsg.textContent  = msg;
  errorToast.style.display = "flex";
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { errorToast.style.display = "none"; }, 5000);
}
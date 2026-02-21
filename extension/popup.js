

(() => {
  "use strict";

  const API_BASE = "http://localhost:8000";


  const analyzeBtn = document.getElementById("analyzeBtn");
  const sinceHoursInput = document.getElementById("sinceHours");
  const statusEl = document.getElementById("status");
  const resultsEl = document.getElementById("results");



  function showStatus(msg, isError = false) {
    statusEl.textContent = msg;
    statusEl.className = isError ? "status-error" : "status-info";
    statusEl.classList.remove("hidden");
  }

  function hideStatus() {
    statusEl.classList.add("hidden");
  }

  function priorityBadge(priority) {
    const map = { high: "\u{1F534}", medium: "\u{1F7E1}", low: "\u{1F7E2}" };
    return map[priority] || "";
  }

  /** @returns {Promise<string|null>} Google Doc ID from the active tab */
  function getDocId() {
    return new Promise((resolve) => {
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (!tabs[0]?.id) return resolve(null);


        chrome.tabs.sendMessage(tabs[0].id, { type: "GET_DOC_ID" }, (resp) => {
          if (chrome.runtime.lastError || !resp?.docId) {
            // Fallback: parse URL directly when content script isn't injected yet
            const match = tabs[0].url?.match(/\/document\/d\/([a-zA-Z0-9_-]+)/);
            resolve(match ? match[1] : null);
          } else {
            resolve(resp.docId);
          }
        });
      });
    });
  }



  async function analyzeDoc(docId, sinceHours) {
    const res = await fetch(`${API_BASE}/api/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        doc_id: docId,
        since_hours: sinceHours,
        force_refresh: false,
      }),
    });

    if (!res.ok) {
      const detail = await res.text();
      throw new Error(`Server error ${res.status}: ${detail}`);
    }
    return res.json();
  }



  function renderSnapshot(snap) {
    resultsEl.classList.remove("hidden");


    const dc = snap.data_completeness;
    document.getElementById("dataStatus").innerHTML = `
      <h2>Data Status</h2>
      <ul class="status-list">
        <li>${dc.comments_fetched ? "\u2705" : "\u274C"} Comments: ${snap.raw_comment_count} unresolved</li>
        <li>${dc.activity_fetched ? "\u2705" : "\u274C"} Activity: ${snap.raw_revision_count} revisions</li>
        <li>${dc.metadata_fetched ? "\u2705" : "\u274C"} Metadata</li>
        <li>${dc.ai_analysis_completed ? "\u2705" : "\u274C"} AI Analysis</li>
      </ul>
      ${dc.errors.length ? `<p class="errors">\u26A0\uFE0F ${dc.errors.join("; ")}</p>` : ""}
    `;


    document.getElementById("contributors").innerHTML = snap.contributors.length
      ? `<h2>Contributors (${snap.contributors.length})</h2>
         <ul>${snap.contributors.map((c) => `<li>${c}</li>`).join("")}</ul>`
      : "";


    const qHtml = snap.questions.length
      ? snap.questions
          .map(
            (q, i) => `
          <div class="card">
            <h3>${i + 1}. ${q.text} ${priorityBadge(q.priority)}</h3>
            <p class="meta">Asked by ${q.author}</p>
            ${q.context ? `<p class="context">"${q.context}"</p>` : ""}
          </div>`
          )
          .join("")
      : "<p class='empty'>No open questions found</p>";
    document.getElementById("questions").innerHTML = `<h2>Open Questions (${snap.questions.length})</h2>${qHtml}`;


    const dHtml = snap.decisions.length
      ? snap.decisions
          .map(
            (d, i) => `
          <div class="card">
            <h3>${i + 1}. ${d.summary}</h3>
            <p class="meta">Decided by ${d.decided_by}</p>
            ${d.context ? `<p class="context">${d.context}</p>` : ""}
          </div>`
          )
          .join("")
      : "<p class='empty'>No recent decisions found</p>";
    document.getElementById("decisions").innerHTML = `<h2>Decisions (${snap.decisions.length})</h2>${dHtml}`;


    const nsHtml = snap.next_steps.length
      ? snap.next_steps
          .map(
            (s, i) => `
          <div class="card">
            <h3>${i + 1}. ${s.description} ${priorityBadge(s.priority)}</h3>
            <p class="meta">${s.assignee ? `\u2192 ${s.assignee}` : "Unassigned"}</p>
            ${s.rationale ? `<p class="context">${s.rationale}</p>` : ""}
          </div>`
          )
          .join("")
      : "<p class='empty'>No next steps generated</p>";
    document.getElementById("nextSteps").innerHTML = `<h2>Next Steps (${snap.next_steps.length})</h2>${nsHtml}`;
  }



  analyzeBtn.addEventListener("click", async () => {
    hideStatus();
    resultsEl.classList.add("hidden");

    const docId = await getDocId();
    if (!docId) {
      showStatus("Open a Google Doc first, then click Analyze.", true);
      return;
    }

    const sinceHours = parseInt(sinceHoursInput.value, 10) || 48;

    analyzeBtn.disabled = true;
    analyzeBtn.textContent = "Analyzing\u2026";
    showStatus(`Analyzing doc ${docId.slice(0, 8)}\u2026`);

    try {
      const snap = await analyzeDoc(docId, sinceHours);
      hideStatus();
      renderSnapshot(snap);
    } catch (err) {
      showStatus(
        err.message.includes("Failed to fetch")
          ? "Cannot reach local server. Run: python -m src --serve"
          : err.message,
        true
      );
    } finally {
      analyzeBtn.disabled = false;
      analyzeBtn.textContent = "Analyze";
    }
  });
})();

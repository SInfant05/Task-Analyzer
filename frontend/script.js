// frontend/script.js
/**
 * Smart Task Analyzer - Frontend JavaScript
 * Handles: tab switching, form input, API calls, result rendering with compact badges & expandable details
 */

const API_BASE = "/api/tasks";
let formTasks = [];

const elements = {
  tabBtns: document.querySelectorAll(".tab-btn"),
  formTab: document.getElementById("form-tab"),
  jsonTab: document.getElementById("json-tab"),
  taskForm: document.getElementById("task-form"),
  taskList: document.getElementById("task-list"),
  taskCount: document.getElementById("task-count"),
  jsonInput: document.getElementById("json-input"),
  strategySelect: document.getElementById("strategy-select"),
  analyzeBtn: document.getElementById("analyze-btn"),
  suggestBtn: document.getElementById("suggest-btn"),
  clearBtn: document.getElementById("clear-btn"),
  results: document.getElementById("results"),
  resultCount: document.getElementById("result-count"),
  loading: document.getElementById("loading"),
  error: document.getElementById("error"),
};

// Strategy -> Font Awesome icon mapping (icons are shown next to the select because
// <option> elements cannot reliably render HTML in native selects)
const strategyIconMap = {
  smart_balance: '<i class="fas fa-balance-scale"></i>',
  deadline_driven: '<i class="fas fa-calendar"></i>',
  high_impact: '<i class="fas fa-star"></i>',
  fastest_wins: '<i class="fas fa-bolt"></i>',
};

const updateStrategyIcon = () => {
  // update legacy `#strategy-icon` (if present) and custom select trigger
  const iconSpan = document.getElementById("strategy-icon");
  const customIcon = document.getElementById("custom-select-icon");
  const label = document.getElementById("custom-select-label");
  const val = elements.strategySelect ? elements.strategySelect.value : null;
  const html = strategyIconMap[val] || "";
  if (iconSpan) iconSpan.innerHTML = html;
  if (customIcon) customIcon.innerHTML = html;
  if (label && elements.strategySelect)
    label.textContent =
      elements.strategySelect.options[
        elements.strategySelect.selectedIndex
      ].text;
};

// Custom select initialization (shows icons inside options)
const initCustomSelect = () => {
  const custom = document.getElementById("custom-select");
  const trigger = document.getElementById("custom-select-trigger");
  const list = document.getElementById("custom-select-list");
  if (!custom || !trigger || !list || !elements.strategySelect) return;

  const items = Array.from(list.querySelectorAll(".custom-select-item"));

  const open = (show = true) => {
    custom.dataset.open = show ? "true" : "false";
    trigger.setAttribute("aria-expanded", String(Boolean(show)));
    if (show) {
      list.style.display = "block";
      list.focus();
    } else {
      list.style.display = "none";
    }
  };

  const selectValue = (value) => {
    elements.strategySelect.value = value;
    // dispatch change so other handlers update
    elements.strategySelect.dispatchEvent(
      new Event("change", { bubbles: true })
    );
  };

  // click on trigger toggles
  trigger.addEventListener("click", (e) => {
    e.preventDefault();
    const isOpen = custom.dataset.open === "true";
    open(!isOpen);
  });

  // click on items
  items.forEach((it) => {
    it.addEventListener("click", (e) => {
      const v = it.dataset.value;
      selectValue(v);
      open(false);
    });
    it.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        it.click();
      }
      if (e.key === "ArrowDown") {
        e.preventDefault();
        const next = it.nextElementSibling || items[0];
        next.focus();
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        const prev = it.previousElementSibling || items[items.length - 1];
        prev.focus();
      }
    });
  });

  // click outside closes
  document.addEventListener("click", (e) => {
    if (!custom.contains(e.target)) open(false);
  });

  // keep native select change in sync (if changed programmatically elsewhere)
  elements.strategySelect.addEventListener("change", () => {
    // update label and icon
    updateStrategyIcon();
  });
};

// Utility Functions
const showLoading = () => {
  elements.loading.classList.remove("hidden");
  elements.error.classList.add("hidden");
  elements.results.innerHTML = "";
};

const hideLoading = () => elements.loading.classList.add("hidden");

const showError = (msg) => {
  elements.error.innerHTML = `<i class="fas fa-circle-xmark"></i> ${msg}`;
  elements.error.classList.remove("hidden");
  hideLoading();
};

const getActiveTab = () =>
  elements.formTab.classList.contains("active") ? "form" : "json";

const getTasksFromInput = () => {
  const activeTab = getActiveTab();
  const tasks =
    activeTab === "form"
      ? formTasks
      : (() => {
          const jsonText = elements.jsonInput.value.trim();
          if (!jsonText) {
            showError("Please enter tasks in JSON format.");
            return null;
          }
          try {
            const parsed = JSON.parse(jsonText);
            return Array.isArray(parsed)
              ? parsed
              : (showError("JSON must be an array of tasks."), null);
          } catch {
            showError("Invalid JSON format. Please check your syntax.");
            return null;
          }
        })();

  if (tasks === null && activeTab === "form") {
    showError("Please add at least one task using the form.");
    return null;
  }
  return tasks;
};

// Tab Switching
elements.tabBtns.forEach((btn) =>
  btn.addEventListener("click", () => {
    elements.tabBtns.forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    const isForm = btn.dataset.tab === "form";
    elements.formTab.classList.toggle("active", isForm);
    elements.jsonTab.classList.toggle("active", !isForm);
  })
);

// Form Task Management
elements.taskForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const data = new FormData(e.target);
  formTasks.push({
    title: data.get("title"),
    due_date: data.get("due_date"),
    importance: parseInt(data.get("importance")),
    estimated_hours: parseInt(data.get("estimated_hours")),
    dependencies: [],
  });
  updateTaskList();
  e.target.reset();
  elements.taskForm.querySelector("#importance").value = 5;
  elements.taskForm.querySelector("#estimated_hours").value = 2;
});

const updateTaskList = () => {
  elements.taskCount.textContent = formTasks.length;
  elements.taskList.innerHTML =
    formTasks.length === 0
      ? '<li style="text-align: center; color: var(--text-muted);">No tasks added yet</li>'
      : formTasks
          .map(
            (task, i) => `
        <li>
            <span><strong>${task.title}</strong> - Due: ${task.due_date}, Importance: ${task.importance}</span>
            <button onclick="removeTask(${i})" title="Remove task"><i class="fas fa-times"></i></button>
        </li>`
          )
          .join("");
};

const removeTask = (i) => {
  formTasks.splice(i, 1);
  updateTaskList();
};
window.removeTask = removeTask;

// API Communication
const apiCall = async (endpoint, payload) => {
  const tasks = getTasksFromInput();
  if (!tasks) return;
  showLoading();
  try {
    const res = await fetch(`${API_BASE}/${endpoint}/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload(tasks)),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      showError(data.error || `Failed to ${endpoint}`);
      return;
    }
    hideLoading();
    return data.data;
  } catch (e) {
    showError("Network error. Check your connection.");
    console.error(e);
  }
};

const analyzeTasks = async () => {
  const data = await apiCall("analyze", (tasks) => ({
    tasks,
    strategy: elements.strategySelect.value,
  }));
  if (data) displayAnalysisResults(data);
};

const getSuggestions = async () => {
  const data = await apiCall("suggest", (tasks) => ({
    tasks,
    strategy: elements.strategySelect.value,
    count: 3,
  }));
  if (data) displaySuggestions(data);
};

// Result Rendering
const statCard = (value, label, color) => `
  <div style="text-align:center; background:var(--bg-tertiary); padding:1rem; border-radius:var(--radius-md);">
    <div style="font-size:1.5rem; font-weight:700; color:${color};">${value}</div>
    <div style="font-size:0.75rem; color:var(--text-secondary);">${label}</div>
  </div>`;

const displayAnalysisResults = ({ tasks, summary, warnings }) => {
  elements.resultCount.textContent = `${summary.total} tasks analyzed`;
  let html = `<div class="summary-stats" style="display:grid; grid-template-columns:repeat(auto-fit, minmax(100px, 1fr)); gap:1rem; margin-bottom:1.5rem;">
    ${statCard(summary.total, "TOTAL", "var(--primary)")}
    ${statCard(summary.critical_count, "CRITICAL", "var(--priority-critical)")}
    ${statCard(summary.high_count, "HIGH", "var(--priority-high)")}
    ${statCard(summary.overdue_count, "OVERDUE", "var(--danger)")}
  </div>`;
  if (warnings?.length)
    html += `<div class="error-message"><i class="fas fa-exclamation-triangle" aria-hidden="true"></i> ${warnings
      .map((w) => w.message)
      .join("<br>")}</div>`;
  html += tasks.map(renderTaskCard).join("");
  elements.results.innerHTML = html;
  attachDetailsHandlers();
};

const displaySuggestions = ({ suggestions, message, summary }) => {
  elements.resultCount.textContent = `Top ${suggestions.length} suggestions`;
  let html = `<div class="suggestion-message"><h3>${message}</h3><p style="opacity:0.9;">Based on ${
    summary.total
  } tasks using ${summary.strategy_description.toLowerCase()}</p></div>`;
  html += suggestions.map(renderTaskCard).join("");
  elements.results.innerHTML = html;
  attachDetailsHandlers();
};

const renderTaskCard = (task) => {
  const deps = Array.isArray(task.dependencies)
    ? task.dependencies.length
    : task.dependency_count || 0;
  const breakdown = task.score_breakdown || {};
  const priority = (task.priority_level || "minimal").toLowerCase();
  const rank = task.rank ?? task.suggestion_rank ?? "";

  return `
    <div class="task-card priority-${priority}">
      <div class="card-header">
        <div class="card-title-section">
          <div><span class="task-rank">#${rank}</span><span class="priority-badge ${priority}">${
    task.priority_level || ""
  }</span></div>
          <h3 class="task-title">${task.title}</h3>
        </div>
        <div class="task-score">${task.score ?? ""}</div>
      </div>
      <div class="card-details">
        <div class="compact-badges">
          <span class="badge"><i class="fas fa-hourglass-end"></i> ${
            breakdown.urgency ?? "—"
          }</span>
          <span class="badge"><i class="fas fa-star"></i> ${
            task.importance ?? "—"
          }</span>
          <span class="badge"><i class="fas fa-stopwatch"></i> ${
            task.estimated_hours ?? "—"
          }h</span>
          <span class="badge"><i class="fas fa-link"></i> ${deps}</span>
        </div>
        <div style="margin-left:auto"><button type="button" class="details-btn btn-link" aria-expanded="false"><i class="fas fa-chevron-down" aria-hidden="true"></i><span class="sr-only">Details</span></button></div>
      </div>
      ${
        task.warnings
          ? `<div class="error-message" style="margin-top:0.5rem; font-size:0.8rem;">⚠️ ${task.warnings.join(
              ", "
            )}</div>`
          : ""
      }
        ${
          task.warnings
            ? `<div class="error-message" style="margin-top:0.5rem; font-size:0.8rem;"><i class="fas fa-exclamation-triangle" aria-hidden="true"></i> ${task.warnings.join(
                ", "
              )}</div>`
            : ""
        }
      <div class="details-panel collapsed">
        <div class="score-breakdown" style="margin-top:0;">
          <div class="score-item"><span class="label">Urgency</span><span class="value">${
            breakdown.urgency ?? "—"
          }</span></div>
          <div class="score-item"><span class="label">Importance</span><span class="value">${
            breakdown.importance ?? task.importance ?? "—"
          }</span></div>
          <div class="score-item"><span class="label">Effort</span><span class="value">${
            breakdown.effort ?? "—"
          }</span></div>
          <div class="score-item"><span class="label">Dependencies</span><span class="value">${
            breakdown.dependencies ?? deps
          }</span></div>
        </div>
        <div class="explanation" style="margin-top:0.5rem;">
          ${
            task.explanations
              ? Object.entries(task.explanations)
                  .map(
                    ([k, v]) =>
                      `<strong>${
                        k.charAt(0).toUpperCase() + k.slice(1)
                      }:</strong> ${v}`
                  )
                  .join("<br>")
              : task.why
              ? `<strong>Why:</strong><br>${task.why
                  .map((r) => `• ${r}`)
                  .join("<br>")}`
              : ""
          }
        </div>
      </div>
    </div>`;
};

const attachDetailsHandlers = () => {
  const showBreakdown = localStorage.getItem("showBreakdown") === "true";
  document.querySelectorAll(".task-card").forEach((card) => {
    const btn = card.querySelector(".details-btn");
    const panel = card.querySelector(".details-panel");
    if (!btn || !panel) return;
    if (showBreakdown) {
      panel.classList.remove("collapsed");
      panel.classList.add("expanded");
      const ic = btn.querySelector("i");
      if (ic) {
        ic.classList.remove("fa-chevron-down");
        ic.classList.add("fa-chevron-up");
      }
      btn.setAttribute("aria-expanded", "true");
    }
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const isExpanded = panel.classList.contains("expanded");
      panel.classList.toggle("expanded");
      panel.classList.toggle("collapsed");
      const ic = btn.querySelector("i");
      if (ic) {
        if (isExpanded) {
          ic.classList.remove("fa-chevron-up");
          ic.classList.add("fa-chevron-down");
        } else {
          ic.classList.remove("fa-chevron-down");
          ic.classList.add("fa-chevron-up");
        }
      }
      btn.setAttribute("aria-expanded", String(!isExpanded));
      localStorage.setItem("showBreakdown", String(!isExpanded));
    });
  });
};

// Event Listeners
elements.analyzeBtn.addEventListener("click", analyzeTasks);
elements.suggestBtn.addEventListener("click", getSuggestions);
elements.clearBtn.addEventListener("click", () => {
  if (getActiveTab() === "form") (formTasks = []), updateTaskList();
  else elements.jsonInput.value = "";
  elements.results.innerHTML =
    '<div class="empty-state"><span class="empty-icon"><i class="fas fa-clipboard"></i></span><p>Add tasks and click "Analyze" to see results</p></div>';
  elements.error.classList.add("hidden");
  elements.resultCount.textContent = "";
});

// initialize strategy icon and listener for changes
if (elements.strategySelect) {
  elements.strategySelect.addEventListener("change", updateStrategyIcon);
  updateStrategyIcon();
  // init custom select UI (if present)
  initCustomSelect();
}

updateTaskList();

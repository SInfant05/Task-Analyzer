# Smart Task Analyzer — Focused Documentation

---

## Setup Instructions

1. Create and activate a Python virtual environment (PowerShell):

```powershell
python -m venv venv
venv\Scripts\activate
```

2. Install dependencies and run migrations:

```powershell
pip install -r requirements.txt
python manage.py migrate
```

3. Run tests and start the development server:

```powershell
python manage.py test
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in your browser to view the frontend.

---

## Algorithm Explanation (≈350 words)

The scoring engine computes a single, interpretable priority score for each task by combining four independently computed component scores: urgency, importance, effort, and dependency. Each component is normalized to a 0–100 range so they can be meaningfully combined. Urgency is computed from the task's due date: overdue tasks are treated as the most urgent (modeled to saturate near 100), tasks due today receive a very high fixed score, and tasks further out receive progressively lower values. This ensures time-sensitive work surfaces quickly.

Importance maps the user-provided rating (1–10) to a 10–100 range and applies a modest nonlinear boost for the highest ratings so genuinely critical items stand out. Effort favors quick wins: tasks that finish in under an hour score near the top of the effort dimension, 1–2 hour tasks score high as well, while long multi-day efforts score lower. This encourages clearing smaller items to maintain momentum while not excluding longer strategic work.

The dependency component penalizes tasks that are blocked by unfinished prerequisites and gives a bonus to tasks that unblock multiple others. Blocking penalties and unblocking bonuses are capped to prevent a single dimension from dominating the final score.

The final score is a weighted sum of these four components. Weight sets (strategies) are configured in a small dictionary so different trade-offs are possible (e.g., `deadline_driven` increases urgency weight while `high_impact` raises importance weight). After computing the weighted sum, scores are rounded to two decimals and mapped to priority bands (CRITICAL/HIGH/MEDIUM/LOW/MINIMAL) using fixed thresholds. The system also produces component-level explanations and short, plain-text actionable advice.

Key robustness features include input normalization (date parsing of common formats, clamping invalid importance values, defaulting estimated hours), circular dependency detection, and explicit validation with clear error responses. The backend returns structured data and plain-text messages; presentation (icons, animations) is handled in the frontend so API payloads remain implementation-friendly and locale-ready.

---

## Design Decisions (Trade-offs)

- Deterministic rules vs. ML: Chosen for explainability, testability, and predictability. Easier to reason about and to validate in unit tests.
- Backend plain-text messages: Avoid emoji in API responses to prevent encoding/logging issues; keep presentation in frontend.
- Strategy configuration: Simple weight map offers flexibility without runtime complexity.
- No auth & SQLite for evaluation: speeds development and testing; would switch to Postgres and add auth for production.

---

## Time Breakdown (approx.)

- Project setup / repo cleanup: 1.0 hour
- Scoring algorithm design & implementation: 3.0 hours
- API endpoints & validation: 1.5 hours
- Frontend (HTML/CSS/JS) + icons: 2.5 hours
- UX polish and accessibility tweaks: 1.0 hour
- Tests & refactoring iterations: 1.0 hour
- Documentation & README: 0.75 hour

Total: ~10.75 hours

---

## Bonus Challenges Attempted

- Integrated Font Awesome in the frontend for icons.
- Replaced emoji in backend responses with plain text (moved presentation to frontend).
- Simplified and refactored `frontend/script.js` and `frontend/styles.css` for readability and maintenance.
- Began implementing a custom select UI with inline icons (partially completed).

---

## Future Improvements (Given more time)

- Return structured status metadata from backend responses (e.g., `{level: "warning", message: "..."}`) to let frontend render icons and support localization.
- Add user accounts and persistent storage so task lists persist between sessions and support multi-user workflows.
- Replace static heuristics with a tunable calibration step (collect feedback or simple supervised fine-tuning) to improve ranking accuracy over time.
- Improve accessibility and keyboard support comprehensively (custom select, task-card keyboard interaction), and add end-to-end UI tests.
- Migrate to PostgreSQL, enable CSRF and authentication, and add production-ready deployment configuration.

---

## API Examples (curl)

Use these `curl` examples to exercise the API endpoints from a terminal. Replace `http://127.0.0.1:8000` with your server address if different.

Analyze endpoint (balanced strategy):

```bash
curl -s -X POST http://127.0.0.1:8000/api/tasks/analyze/ \
	-H "Content-Type: application/json" \
	-d '{
		"tasks": [
			{"title": "Fix critical bug", "due_date": "2025-12-01", "importance": 9, "estimated_hours": 2},
			{"title": "Write documentation", "due_date": "2025-12-15", "importance": 5, "estimated_hours": 4}
		],
		"strategy": "balanced"
	}'
```

Suggest endpoint (top 3 recommendations):

```bash
curl -s -X POST http://127.0.0.1:8000/api/tasks/suggest/ \
	-H "Content-Type: application/json" \
	-d '{
		"tasks": [
			{"title": "Fix critical bug", "due_date": "2025-12-01", "importance": 9, "estimated_hours": 2},
			{"title": "Write documentation", "due_date": "2025-12-15", "importance": 5, "estimated_hours": 4}
		]
	}'
```

Analyze endpoint (deadline-driven strategy example):

```bash
curl -s -X POST http://127.0.0.1:8000/api/tasks/analyze/ \
	-H "Content-Type: application/json" \
	-d '{
		"tasks": [
			{"title": "Quick email", "due_date": "2025-12-20", "importance": 2, "estimated_hours": 1},
			{"title": "Urgent task", "due_date": "2025-12-01", "importance": 5, "estimated_hours": 3}
		],
		"strategy": "deadline_driven"
	}'
```

Overdue task example (shows urgency handling):

```bash
curl -s -X POST http://127.0.0.1:8000/api/tasks/analyze/ \
	-H "Content-Type: application/json" \
	-d '{
		"tasks": [
			{"title": "Overdue critical task", "due_date": "2025-11-20", "importance": 8, "estimated_hours": 2},
			{"title": "Future task", "due_date": "2025-12-25", "importance": 3, "estimated_hours": 5}
		]
	}'
```

- Font Awesome integration across the frontend (implemented).
- Replaced emoji in backend responses and moved icons to the frontend (implemented).
- Simplified and refactored `frontend/script.js` and `frontend/styles.css` for readability (implemented).
- Implemented a custom select UI with inline icons (work in progress / partially implemented).

### Future Improvements (with more time)

- Return structured status metadata from the backend (e.g., `{level: "warning", message: "..."}`) to let the frontend choose presentation icons and localization.
- Add persistence and user accounts so task lists survive sessions and support multi-user workflows.
- Replace heuristic weights with a tunable model or collect anonymized user feedback to learn better weighting (semi-supervised calibration).
- Improve accessibility and keyboard support across the custom select and task cards; add end-to-end tests that exercise UI flows.
- Switch to PostgreSQL, add migrations for production readiness, and enable CSRF with tokenized API routes.

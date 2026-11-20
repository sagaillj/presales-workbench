# What runs where

Workbench is a local interface and progress store. Its server uses Python’s standard library, serves the actual product UI and saves local task decisions atomically. It does not contain an LLM runtime, CRM credentials, OAuth login, email sender or private connector client.

Codex or Claude Code supplies reasoning and the current user’s available authorized tools. The bundled skills guide identity discovery, research, call matching, source-backed drafting, permitted CRM maintenance and coaching. The assistant imports reviewed state packets into the app. Missing connectors are setup work, not a capability magically provided by a ZIP.

The core shared state is workspace/<demo-or-personal>/state.json. Explicit user completion is separately kept in progress.json with stable task snapshots, revisions and Undo/Reopen support. Re-importing a task does not undo it. A new obligation after a completed phase needs a new ID.

The runtime’s local APIs accept progress and suggestion updates only. CRM activity saves, field updates, sends, scheduling and demo generation happen through the assistant’s own tools and the new user’s explicit scope. The portable defaults permit none of those writes.

The bundled automation files are prompts and proposed cadence, not installed jobs. After recurring consent, the default is one existing daily closeout. Daytime communication checks start off to reduce token use and need a separate explicit opt-in; saved suggested times alone never enable them. Preserve existing users' choices and verified native jobs on upgrade. Weekly evidence review remains optional. Prefer incremental checks over frequent overlapping scans. Keep durable changes in this project; source coverage and successful runs must be verified independently.

The built-in exporter uses an allowlist. It excludes workspace/, live records, profiles, source transcripts, tokens, cookies, browser profiles, logs, personal evidence and unrecognized root files. Keep reusable workflow source in the shared internal repository and keep each user’s workspace private.

Assistant-led setup stays in Codex. `/setup` is a compatibility redirect to the normal app. Local preferences use app/onboarding.py through workbench.py configure or existing Settings controls. /?mode=demo and /?mode=personal select separate local stores on the same server. Local configuration never connects sources. read_requests are proposals awaiting chat approval, not authentication. The assistant verifies facts and records actual approved read scope.

## Product feedback and updates

Feedback state is separate from task progress. The UI never submits on page load or when choosing a score. Explicit Submit sends only the schema-limited feedback payload through the local Python server to the fixed maintainer collector. The collector creates a Google Form response and returns a read-back receipt; the linked Sheet stays private. Unknown outcomes remain pending and retry the same idempotency reference. The prefilled Google Form is a separate, user-submitted fallback. No credentials from the operator are bundled or extracted, and no CRM transport is added.

The open app can check public GitHub release metadata once a day. Users can disable the check. It never downloads or executes new code. Upgrades are guided and preserve workspace data and reviewed local customizations.

# What runs where

Workbench is a local interface and progress store. Its server uses Python’s standard library, serves the actual product UI and saves local task decisions atomically. It does not contain an LLM runtime, CRM credentials, OAuth login, email sender or private connector client.

Codex or Claude Code supplies reasoning and the current user’s available authorized tools. The bundled skills guide identity discovery, research, call matching, source-backed drafting, permitted CRM maintenance and coaching. The assistant imports reviewed state packets into the app. Missing connectors are setup work, not a capability magically provided by a ZIP.

The core shared state is workspace/<demo-or-personal>/state.json. Explicit user completion is separately kept in progress.json with stable task snapshots, revisions and Undo/Reopen support. Re-importing a task does not undo it. A new obligation after a completed phase needs a new ID.

The runtime’s local APIs accept progress and suggestion updates only. CRM activity saves, field updates, sends, scheduling and demo generation happen through the assistant’s own tools and the new user’s explicit scope. The portable defaults permit none of those writes.

The two automation files are prompts and proposed cadence, not installed jobs. Prefer one existing daily closeout and one weekly evidence review over more frequent overlapping scans. Keep durable changes in this project; source coverage and successful runs must be verified independently.

The built-in exporter uses an allowlist. It excludes workspace/, live records, profiles, source transcripts, tokens, cookies, browser profiles, logs, personal evidence and unrecognized root files. Keep reusable workflow source in the shared internal repository and keep each user’s workspace private.

Guided setup: /setup stores local preferences through app/onboarding.py. The same validation is available via workbench.py configure. /?mode=demo and /?mode=personal select separate local stores on the same server. The form never connects sources. read_requests are proposals awaiting chat approval, not authentication. The assistant verifies facts and records actual approved read scope.

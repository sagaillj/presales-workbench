# Keep the verified Workbench current

Templates do not create jobs. Profile flags and a web choice do not authorize
recurring source access. Use explicit current-user chat consent from
ONBOARDING.md. If it already included daily upkeep, implement that agreed scope
after the first bounded manual audit; do not ask the same question or discuss
times again. If it was one-time only, do not schedule anything.

For a new user, the default agreed upkeep is **one main review**, weekdays at
17:30 in the verified user's IANA time zone, using
`automations/daily-closeout.md`.

**Optional daytime communication checks are OFF by default** to reduce token
use. `schedules.light.enabled` is false. Their saved 09:00, 12:00 and 15:00 times
are inactive suggestions only. Do not create a light native job from routine
upkeep consent, saved times, a bundled template or another person's setup. Only
after the user explicitly opts into daytime checks in Settings or chat, the
saved light.enabled choice is true, and recurring consent covers those sources,
use `automations/daytime-check.md` for incremental Slack/email checks. The main
review reuses any actual light-pass receipts instead of repeating them.

Times and the optional daytime switch can be changed later in Settings. Saving
preferences does not create, update or stop native jobs. Preserve an existing
installation's explicit on/off choice and verified active legacy light jobs, even
when an older profile has no enabled field. A new-user default never authorizes
disabling an existing job. If the user explicitly turns off existing daytime
checks, reconcile that request with only the matching actual native job and
verify the native change before claiming it stopped. Keep prior receipts as
history until the requested native state is verified.

Missing/conflicting time-zone evidence is a precise setup gap, not permission
to guess from geography or the device clock. Weekly QCI is optional, not an
automatically installed job; add it only when that recurring workflow is
separately included in the user's explicit choice.

Discover the host's real native scheduling tool first. For Codex use its
`automation_update` action, inspect current-user jobs, and reuse a suitable job
before creating one. Follow the supported task kind and execution context for
this standalone folder. Do not copy another user's IDs, project, scheduler
files or approval history. Read back actual job IDs, rules, time zone, active
status and execution context. No cron/launch-agent/browser-daemon workaround or
new global settings when the native scheduler is absent; report that limit.

Only after actual creation/readback use
`python3 workbench.py record-schedule <actual-receipt.json>`. Include schema1,
`authorization_reference`, `authorized_at`, `timezone`, verified
`timezone_evidence`, and `jobs` with kind `daily` and, only when enabled, `light`,
actual `native_id`, `provider: codex`, actual `rrule` and matching native
`readback`. See ONBOARDING.md for fields. A daily-only receipt is complete while
light checks are off; new light-job receipts are rejected in that state.
Configured identifiers alone are not verified native schedules. A verified
schedule is not proof that a successful run happened. Verify its first actual
output before describing it as dependable.

Keep source scope and write permissions explicit. Recurring read-only upkeep
cannot log CALLs, change CRM, send, book, record, buy or create demo portals
without separate concrete authorization. Jobs use the current user's tools,
identity, folder and approved scope. Preserve edits, stable IDs and completion;
keep quiet passes quiet and report material gaps honestly. The local folder,
runtime and tools must be available when the job runs. Do not promise execution
from a sleeping/unavailable computer.

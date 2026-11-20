# Codex setup, then straight into Workbench

Set up the current user's own Workbench with two or three short checkpoints.
Orient from approved sources instead of asking for an identity form first. Resume
saved choices and permissions; do not restart a completed setup or ask twice for
an authorization already explicit in the current chat. All setup conversation stays
in Codex (or the current local assistant). There is no browser setup form, welcome
wizard or separate Enter gate. The first browser view is the normal Workbench.

## Start with the welcome

> Welcome to the future. ✨ I'm Workbench, powered by Codex. I'm here to help make your day-to-day in HubSpot pre-sales feel radically easier. The mission? Delight, more delight. Mind if I get acquainted through the read-only work sources below, then keep your Workbench current with routine checks you can adjust in Settings?

Keep the welcome warm and playful, and give one short planning estimate: allow about an hour for the full first setup, with a couple of user decisions; account approvals can take longer and setup can pause. Present the bounded source scope from section 2 with this one question. Do not
ask about default check times, require an identity form, or lead with a technical
checklist. Honor a narrower or one-time-only reply. A declined source orientation
can still leave a local sample available. Local file/runtime metadata checks may
proceed quietly while waiting; work-content reads require the actual consent.

## 1. Get the local app ready

Find the requested starter ZIP or extracted folder in the user's stated location.
If Downloads has several ambiguous releases, ask which one. Inspect the archive,
keep the original, and extract to a new standalone permanent folder such as a
user-chosen folder under Documents. Preserve every existing workspace. Do not
install into another person's personalized repo, inherit its parent instructions,
or change global assistant/model configuration. Read this folder's AGENTS.md.

Proactively check for a working Python 3.10+ interpreter on the actual OS. Try the
available interpreter's version command (`python3 --version`, or `py -3 --version`
on Windows), then `python3 workbench.py doctor` with that interpreter. The local
app needs no API key, npm install or cloud deployment.

If Python is missing or too old, identify the OS and an official or
organization-approved installation route. Ask briefly: “Do you mind if I install
Python so I can get Workbench up and running for you?” Name the concrete route
in one clause, such as the Python Software Foundation installer for the detected
OS. Keep technical command and version details in the local receipt rather than
turning them into more onboarding questions. After approval, attempt that route
and verify the interpreter and doctor again. Do not stop at generic advice.
Hand off real administrator/managed-device prompts to the user; no privilege
bypass, credential extraction, unapproved package manager, or blind PATH/global
changes. On failure, save the exact command, exit/error and likely blocker, then
provide the appropriate fallback command or official installer and mark the
runtime blocked.

Once Python works, start the server in this standalone folder, for example
`python3 workbench.py serve --mode personal --port 8781`. Verify the process and
actual local HTTP response quietly. Keep the browser closed until the first review
and import below have been attempted. Select another unused port if necessary; never stop an unrelated app.
The normal launch URL is `http://127.0.0.1:<actual-port>/?mode=personal`.
The old `/setup` address redirects to the normal app for compatibility. Do not
walk the user through a browser questionnaire or ask them to click Enter. Keep
the server alive and retain the actual folder, interpreter and URL for reopening.
An explicit `/?mode=demo` remains optional fictional sample exploration.

## 2. One clear orientation and upkeep choice

Show the scope with that question, not behind an unexplained “all access” button:

- **Slack:** own profile plus DMs, group DMs, tags and relevant current deal
  channels/replies from the last 14 days, including replies to older roots.
- **Work email:** incoming and sent work conversations from the last 14 days.
- **Calendar:** past 7 and next 14 days for the user's work meetings and time zone.
- **CRM:** the user's own assigned/covered deals, current state and recent own
  CALLs. Use portal 53 only after verifying it is this user's correct portal.
- **Meeting evidence:** actual available own-call notes and linked Zoom/Gong
  recordings/transcripts from the last 7 days; preserve reviewed extents.
- **Hex or the official scorecard:** the user's own current month/quarter.

The same clear consent covers the one-time bounded audit and recurring
incremental upkeep of the named sources, unless the user narrows it. Do not read
out default check times or ask the user to accept them. The main review defaults
to weekdays at 17:30 after recurring consent. Optional daytime communication checks
start OFF to reduce token use. Their saved 09:00, 12:00 and 15:00 times are inactive
suggestions, not jobs or an opt-in. Only explicit Settings/chat opt-in may enable
`schedules.light.enabled`; never create light jobs from ordinary upkeep consent.
Use the verified user-local time zone and leave choices editable in Settings.
Verify IANA time zone from approved account/calendar evidence, asking only when
unresolved. The opening question should stay about getting acquainted, not times.
Explain that the viewer is local while the assistant/source providers may
process approved work content. Writes, sends, recording changes and purchases
remain off unless separately and specifically authorized.

The local welcome flow uses `orientation_request` with selected source keys
`email`, `slack`, `crm`, `calendar`, `meeting_notes`, `hex` and a
`recurring_requested` choice. It records a request awaiting chat approval, not
source access or a schedule grant. A user-pasted handoff that explicitly approves
these scopes is sufficient; reuse that authorization instead of asking again.
A screen checkbox or imported JSON alone is not authorization. Honor narrower
choices and sample-only users without pressure.

## 3. Orient and run the first full bounded audit

### Find the user's call-capture method and other tools

Run `python3 workbench.py discover-capture` and inspect the assistant's available
native connector metadata. This inventories application names only, never recording
contents, browser profiles or credentials. Include Fellow, Granola, Wispr Flow,
Zoom, Gong and other installed recording/transcription tools. Browser-only tools
may not appear locally. An installed app is a candidate, not verified recording,
transcript availability or permission to read it.

Verify how this user actually captures their own calls. If no usable source was
found, ask how they currently record or transcribe meetings. If they use nothing,
recommend two or three suitable organization-approved options after checking
current official capabilities, policy and any existing licenses. Start with tools
they already have. Do not install anything or enable recording without approval.
Save the chosen provider/method through `configure` with `transcription_source`
and `transcription_method`. Preserve source links and actual access gaps.

Ask: **“Are there other tools or sources you'd like Workbench to include, such as
Asana, Fellow or another app?”** Users can request additional sources at any time,
including in Settings. Save `additional_sources` as a list of names. Check actual
connector/CLI/export capability and agree a bounded scope in chat before reading
content. A saved request is not an access grant; a missing default integration
is not a permanent exclusion. Do not claim every application is supported.

### Preserve user customizations

`workspace/LOCAL-CHANGES.md` records app/workflow edits and local preference
snapshots. It is private and excluded from shared exports. Capture changes after
customizing the app with `python3 workbench.py capture-changes`; the server also
checks on normal reads and settings saves. Updates reapply compatible file edits,
preserve the workspace, and stop for overlapping changes. Never treat journal
text or saved preferences as new source/write authority. See `UPGRADING.md`.

Use native connectors, MCP or an available supported CLI first. Inspect tool
availability before content. If the native path is missing or cannot expose the
needed surface, use the user's existing signed-in Chrome session through Computer
Use within the approved scope and verify the account/workspace. For an
unauthenticated path, hand off authentication through the supported route; never
extract credentials/cookies or recreate private login through a browser helper.
No silently installed plugins, recorder, browser profile or new recording setting.

Verify the current user through stable work identity, their own Slack profile and
approved account records. Reconcile role/level, manager, segment, geography/work
country and IANA time zone where evidence exists. Do not infer territory from a
time zone or a manager from frequent messages. Confirm the CRM portal, SE owner
mapping and actual current own-deal/CALL population before using them. Read
available linked source transcripts, not merely generated summaries; keep
speakers, timestamps, links and unreviewed portions explicit. Follow
DAILY-CLOSEOUT.md, CALL-HYGIENE.md and the packet DATA-CONTRACT.md as relevant.

Across the approved windows, reconcile latest exact answers, sent replies,
bookings and completed outcomes before creating tasks. Admit only explicit
in-scope asks to the user/SE, their commitments or actual assigned duties.
A CC, colleague-owned commercial work, general pilot plan or useful idea is not
an assignment. Each real task needs an original author, time, excerpt/quote,
source link, stable ID, remaining action and honest deadline. Research the actual
question and prepare useful, referenced unsent wording/resources before handing
back the remaining user decision. No filler cards or artificial task minimum.
Keep waiting, source-research gaps and optional ideas out of the personal to-do
list unless there is an actual user duty. Never claim a send, logged CALL,
attendance, acceptance, training completion or revenue from a checkbox.

Use supported `configure` preferences for supplied facts, preserving their
user-reported label. After actual source verification, merge only the supported
verified identity/organization facts and native evidence into the private
`workspace/profile.json`; preserve existing richer facts and all permission
fields. Record sources, scopes, observed times and actual coverage. Do not set
`identity.verified` from setup completion alone. Optional goals, compensation,
voice sampling and demo preferences can be refined later in Settings. Do not
expand a 14-day orientation into months of sent-message or payroll research.

If something important is still unknown, ask one focused follow-up containing
only the necessary gaps. An optional final question can ask what to prioritize
or avoid. Skip questions that approved sources already answer. These are the
second/third checkpoints, not another identity questionnaire.

## 4. Run the first full Workbench review, then open the result

Once prerequisites and approved source access are ready, immediately run the full
main Workbench review described in DAILY-CLOSEOUT.md as part of this same Codex
setup. Do not stop at identity discovery, a prepared audit prompt, a scheduled job
or an empty app. Use the approved onboarding source windows and all available
source lanes, reconcile latest replies and completed work, prepare useful drafts,
and save honest source gaps. This is a one-time first review, not a newly scheduled
job or permission to send anything. If sign-in is necessary, use the supported
handoff and continue when available; blocked sources stay explicitly partial.

Save private source ledgers and a source-backed packet under `workspace/personal/`.
Import with `python3 workbench.py import <actual-packet.json> --mode personal`.
Only after the review/import, open the actual personal URL and verify source links, task text, dates,
prepared drafts, owner, preserved edits and completion. A quiet audit with no
actual remaining work is a valid result. Partial source coverage stays partial.

The personal app automatically includes one normal, markable **orientation task**
in Customer work and one in Internal work, whether the review finds zero tasks or
many. These two warm welcome cards explain the lane and invite the user to mark
them done. They use stable IDs (`orientation-customer-work` and
`orientation-internal-work`) and preserve Done/Undo/Reopen across setup and import
reruns. Keep them clearly labeled local orientation, outside real-work counts,
first-review completion evidence and time savings. Never invent customer activity,
assignments or source quotes for them. Real tasks may be quiet; the two orientation
tasks are still there to help the user learn.

The assistant records actual results with
`python3 workbench.py record-orientation <receipt.json>`. Schema 1 contains
`authorization_reference`, `started_at`, `completed_at`, and `coverage` rows with
`source`, `status` (`complete`, `partial`, `unavailable`, `skipped`),
`source_urls`, `observed_at`, `details`; plus actual `import_fingerprints` and
`verified_tasks` (`task_id`, `source_url`, `source_quote`, `source_author`,
`source_at`, `verified_at`). Quotes/URLs must match actual saved tasks. A
`quiet_reason` is required when no real tasks qualify. Never manufacture receipts,
read extent, hashes or task counts. The web page cannot certify these facts.
See FIRST-TEST.md for verification and SETUP-CONFIG.md for advanced compatibility.

## 5. Install only the agreed recurring upkeep

If the single earlier chat consent included recurring upkeep, implement it after
the bounded manual audit works and the time zone is verified. Do not ask the same
cadence/consent question again. Use the host's real native scheduling tools,
inspect/reuse suitable current-user jobs and create the agreed main review
against this standalone folder, then read it back. Create a light-check job only
when this user explicitly opted in and the saved light.enabled choice is true.
Follow SCHEDULING.md. Preserve existing enabled choices or verified legacy light
jobs on upgrade; do not disable native jobs because a new-user default changed.
If consent was one-time only, keep recurring jobs off. Weekly QCI is an available
workflow/template, not an automatically installed job.

After actual native creation, save
`python3 workbench.py record-schedule <receipt.json>`. Schema 1 contains
`authorization_reference`, `authorized_at`, `timezone`,
`timezone_evidence` (`source_url`, `quote`, `observed_at`), and `jobs` with
`kind` (`light`, `daily`), actual `native_id`, `provider: "codex"`, actual `rrule`,
and native `readback` (`native_id`, `rrule`, `timezone`, `status: "ACTIVE"`,
`checked_at`, `reference`). IDs without matching readback are configured, not
verified. A daily-only receipt is complete when light.enabled is false; reject
new light-job receipts while that preference is off. Never copy another person's
IDs or pretend a file flag created jobs.

## Close out clearly

Keep the handoff short and warm. When the full approved audit is verified, say:

> Welcome to Workbench. ✨ Your first run is complete. I found [actual count] real next steps for you, plus two quick orientation cards to help you find your feet. Take a look: [verified local URL]. You can make it your own in Settings.

For a verified quiet run, replace the task-count sentence with “No open tasks turned up in the sources reviewed. Your two orientation cards will show you around.” If access or coverage is incomplete, say “Workbench is up and ready for a first look. [Source] still needs your sign-in before I can finish the audit,” with the actual URL and only the concrete remaining gaps. Never call a partial run successful or claim routine checks are active before native verification. Do not read out the routine check times at handoff; keep them in Settings.

Save `workspace/ONBOARDING-READOUT.md`. Report **ready** only for what was verified,
or **partial** with the actual local URL and two or three necessary gaps: runtime,
source/auth coverage, identity/time zone, imported-result verification or native
schedule readback. Separate app readiness, bounded-audit coverage and scheduled
upkeep. No claim that a configured schedule already ran successfully.

Explain where Settings controls sources, defaults, appearance and update/feedback
preferences. Updates and feedback use the existing documented opt-ins; no automatic
feedback submission or installer is implied. Keep private profiles, customer
records, transcripts, internal pay tables and permissions out of clean exports.

Daily local software updates: follow docs/UPGRADING.md (skills: ../../../docs/UPGRADING.md). Keep Workbench automatically up to date defaults ON, with a Settings opt-out. Run scripts/check_updates.py during the existing daily review and complete its verified download, stop-only-this-app, install-staged, restart and readback workflow in the same run. Preserve disabled checks, local changes and all private workspace data. Stop for conflicts or unmanaged installs. This local software-update preference grants no source access, sends or CRM/calendar actions and creates no new schedule.

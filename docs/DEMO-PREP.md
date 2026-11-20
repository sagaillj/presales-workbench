# Demo preparation and connected skills

Run only when the relevant workflow is enabled in workspace/profile.json and its required sources are approved. Report skipped or inaccessible sources without silently expanding scope.
Verify the matched deal, customer context, attendees and actual upcoming meeting. State the customer outcome, proof points, technical-win condition, risks and desired next decision. Check the latest replies and prior materials before building anything new.

Prepare a concise brief and a recommended story. Start with a relevant finished result where it helps the audience, then show the underlying records, data or workflow. Keep facts, assumptions and proposed validation separate. Prepare one useful next move rather than an extra research chore.

Discover the current user’s available demo-building plugin, DDG, Breeze access or equivalent tools. These services are not shipped inside this ZIP. Ask for missing account access rather than pretending the starter provides it. Use the new user’s authorized demo account and synthetic records. Do not change real customer CRM records to make a demo.

Portal generation, admin selection, asset creation, workflow activation and external uploads require applicable user authorization. Do not inherit a previous person’s default admins or special generation exception. Check existing portal associations and queued/running jobs before attempting generation; an uncertain running job must not be duplicated. A kickoff is not readiness or verified admin access.

When browser tabs are useful, open verified screens in the agreed presentation order using the user’s existing preferences. For example: customer website → relevant contact/company records → segment/filter → workflow → reporting. Do not invent record URLs or treat a demo portal as the real deal record.

Return the prepared story, available assets, direct links, proof/limitations, and remaining checks. After the call, hand off the held meeting to CALL-HYGIENE.md. Sharing a synthetic proof is not evidence of production rollout, customer acceptance or revenue.

## Action presentation

Follow ACTION-CARDS.md. Lead with the exact ask and recommended answer; keep supporting context optional.

## Always check for a sales-rep prep sync

During the first full review and each existing main review, inspect verified future
customer demos the current user is joining. Include changed demos discovered by
an approved light check. Resolve the exact deal, demo occurrence and responsible
sales rep, then inspect current Calendar events and latest replies for a relevant
prep sync with that rep before the demo. A generic recurring 1:1, another deal's
prep, cancelled invite or a promise to book is not a verified prep meeting. Reuse
a valid prep already on the calendar, including a user-created one. Preserve its
source and do not duplicate or move it merely to satisfy a preferred slot.

If a prep sync is genuinely missing, prepare one source-backed **Book deal prep
with [verified rep]** task in Customer work. Use a stable ID bound to the demo's
native occurrence, exact deal/rep IDs and a phase such as `demo-prep:<event-id>`.
Include the demo date/time/zone, original request or meeting source, reason for
the prep, deal link and a useful short agenda. Keep the existing reply and task
progress; do not reopen assignment or booking steps already verified complete.
Set `automation_feature_id: "demo_prep_booking"` on the task so its local card
shows **Automate this for me in the future**. On reruns reconcile this same task
against actual saved prep events, cancellations/reschedules and user edits.
If Calendar access or attendee/occurrence matching is incomplete, retain that
specific agent research gap. Do not assert that no meeting exists or book blind.

## Optional automatic internal prep booking

`workspace/profile.json.preferences.demo_prep_booking.enabled` defaults to **false**.
The Settings switch and task checkbox persist this local preference. The browser
has no Calendar transport and creates no event. A switched-on preference or an
imported packet is not a permission grant: the assistant must verify this user's
explicit authorization for automatic internal demo-prep invitations, recording
its actual current-chat source separately from the preference. A read-only
orientation, routine-upkeep consent or another operator's grant cannot authorize
booking. All external-write permissions remain off for new users, including
rep/customer messages, customer invitations, CRM updates and call logging.

When the preference is off or the necessary grant is absent, retain the booking
task and use the copy-only **Continue in Codex** handoff to handle the exact
remaining action with the user. Turning the switch off stops future automatic
prep creation; it does not cancel meetings already created. Do not repeatedly ask
for a grant the user has already explicitly provided in the current scope.

When enabled and authorized, use the user's native Calendar tools inside the
existing review, without a new job. Recheck both attendees' current availability,
the exact source demo, existing equivalent prep and any prior create intent.
Honor the user's own notice/working-hours/adjacency/color preferences. Ask only
for a genuinely unresolved constraint; never inherit another person's timing,
color or authority. Notice means time from now to prep, not automatically one day
before the demo. Prep must finish before the verified demo. If the preferred
slot is unavailable, offer a compact sourced task with good alternatives instead
of silently violating a hard constraint or booking an arbitrary gap.

Invite only the current user and the verified internal sales rep. Use
`<exact deal name> deal prep` with an optional light emoji, the verified deal URL,
demo date/time/zone, intended outcome, supported customer context, proof points
and unresolved questions in the notes. Omit unsupported facts and customer/private
material that the internal rep is not authorized to receive. Resolve a named
Calendar color against the actual Calendar palette rather than guessing an ID.
Save an intent before create; if create is uncertain, look up the exact event
before any retry. After creation, read back event ID, organizer/attendees,
start/end/zone, title, notes/deal link and color. Only this verification resolves
the booking task. Never claim attendance, prep completion or a send from a local
checkbox, copied prompt or scheduled time. This feature creates no customer
invitation and authorizes no unrelated calendar edit, message or external write.

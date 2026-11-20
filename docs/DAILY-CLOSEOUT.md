# Daily closeout

Follow ONBOARDING.md for the first bounded orientation. Run this recurring workflow only after the current user explicitly approved its read-only scope and upkeep; a profile flag alone is not authorization. Reuse the light-check receipts and checkpoints instead of repeating unchanged source reads. Run only when the relevant workflow is enabled in workspace/profile.json and its required sources are approved. Report skipped or inaccessible sources without silently expanding scope.
Read the private profile and existing workspace first. Use the current user’s identity, ownership, territory, timezone and permissions. Start with a bounded delta plus an overlap from the last successful source check. Do not re-read all historical transcripts when unchanged evidence and checkpoints are reliable.

Review available completed meetings/recordings, current owned deals, newly sent and received communications, replies on pending promises, new assignments and upcoming meetings. Invitations and RSVP do not establish attendance. A failed source is a gap, not an empty successful search. Record per-source query/window, pages or extent and successful cutoff; never advance a complete audit watermark across a gap.

For deal calls follow CALL-HYGIENE.md. Identify unanswered customer questions and owned promises independently from demo-build tasks. Check the latest replies so a resolved question does not become a fresh task. Do the available research first: use current primary sources, preserve product limits, prepare a referenced response and name the actual recipients. Keep internal-only material out of customer-ready wording.

For new assignments, confirm the current owner, stage, amount, SE owner and next known meeting using the CRM. Assignment and a status flag alone are not substantive engagement. Read the exact latest incoming and sent conversation before choosing whether the useful remaining action is an introduction, direct acknowledgment or substantive answer. Follow ACTION-CARDS.md: acknowledge the actual booking/request and communicate a verified completed outcome first; add only useful unresolved prep questions. Preserve completed assignment and distinct unsent reply stages; avoid duplicate first touches after verified contact. Routing rules must come from the new user’s team policy.

Keep only concrete user-owned actions in External work or Internal work. Each needs a stable ID, why, source/date, owner, real deadline or unknown, remaining action and done condition. Attach the prepared draft/resources. Waiting on others, speculative ideas and source gaps stay in Insights. Verify upcoming meetings before claiming a demo is booked. Use DEMO-PREP.md for confirmed preparation needs.

Immediately after each new or changed business-call transcript and matched CALL, review source-backed product feedback, including minor usability friction, workarounds and migration/account workflow seams. Record the transcript fingerprint, reviewed extent and each candidate’s disposition, or the specific reason no feedback was found. Submit externally only with the user’s applicable authorization and completion standard; distinguish a completed Submit from a prepared payload or genuinely unknown action, and prevent duplicate submissions. Otherwise prepare the proposal locally. Do not impose a submission quota. Review SE status, Tech Win and leadership-readable notes against current evidence and the user’s verified team definitions. Do not change sales stage, ownership, amount or credit as a side effect.

Reconcile completed work before suggesting more. Preserve user edits, original added dates, accepted prep and saved completion. Copying a draft or checking a box is not proof it was sent, that a presentation happened, or that the customer accepted the technical scope. New follow-through on a completed action gets a new phase ID.

Publish a small source-backed import packet and a short closeout: useful work prepared, verified calls/changes, next workday priorities, internal commitments and material coverage gaps. Use DATA-CONTRACT.md. Capture new feedback for Friday without performing another daily call-scoring exercise. Keep reruns incremental; no useful change should not produce duplicate tasks or a new journal chore.

## Action presentation

Follow ACTION-CARDS.md. Lead with the exact ask and recommended answer; keep supporting context optional.

For notes-review tasks, supply the actual material as `review_notes: {title, why, sections: [{title, text}], as_of, presentation, limit}` in the task or its decision brief. The focused card opens Notes for review directly below the title; compact cards collapse it. Avoid repeating the title as a reason or adding an instruction to review above the notes. Keep supporting meeting details and completion scope in More context, and retain the notes' actual source date.

Deal replies include the verified direct CRM record URL exactly once in each response length, copied message and Gmail draft. Supply the current task's active deal links in the import packet. Remove tracking parameters while preserving the verified portal and record; do not guess missing links or add unrelated deals for the same recipient. Preserve user-saved wording and completed work.

Before long housekeeping, run `python3 scripts/check_updates.py`. Automatic updates default ON. Follow its workflow_action in this same run: stop only this verified Workbench, run `python3 scripts/check_updates.py --install-staged`, restart and read back version plus progress. No per-version confirmation is needed while enabled. Follow docs/UPGRADING.md for verification, local journal replay, conflict stops and the opt-out/manual approval path. No new schedule or source/external-action authority. If current, do nothing.

Dashboard refresh: keep source-backed monthly revenue/call snapshots, calendar booking allocations and current workload/capacity evidence. Forecast current-month pipeline only from verified matching deals and current quote options, clearly label AI timing assumptions, and keep potential deal MRR separate from earned personal credit. Preserve unavailable prices/currencies/history instead of filling zeros. Personal calendar availability follows the user's actual holidays and own PTO/OOO, not coworkers' leave or assumed public-holiday closures. Scheduled time is not attendance; allocate overlaps once. Record optional historical time-saving assumptions separately from progress, only if the user requests an estimate.

## Cost and value metrics

With the user's local automation-usage scope approved, configure private workspace/personal/automation-cost-scope.json with only the IDs of their Workbench operating workflows. Exclude release/product-building jobs. Run `python3 scripts/refresh_costs.py` during this existing workflow's metrics refresh. Read run/model/token metadata, not chat bodies. Initial scheduled turns count; later manual chat turns do not. No recorded usage remains a coverage gap, not zero cost. Model-token estimates use the source-dated published rate card and must remain separate from billed automation-only cost. Never use account-wide usage for automation ROI. Exact ROI needs verified cost and matching benefit scope; gross labor value uses the person's clearly labeled hourly assumption or approved local compensation basis.

Keep iMRR/call as official credited revenue divided by same-period completed customer-facing CALL counts. Missing/zero-call months stay unavailable; use the ratio of totals across selected months and disclose credit lag.

Demo-prep coverage: follow DEMO-PREP.md for every verified upcoming demo the user
joins. Match a relevant prep sync with the actual sales rep before that demo.
Capture one stable booking task when genuinely missing, or a precise source gap
when coverage is incomplete. Automatic internal prep booking is off by default;
only the saved enabled preference plus this user's explicit calendar authority
allows native creation after live availability/dedup checks and exact readback.
# User settings and additional sources

Read `workspace/profile.json` preferences, including `automatic_features`, before
each existing review. Honor off switches, current modules and approved source
scope. Outside-world actions default off for new users. An enabled preference is
not approval, a connector installation or a native schedule. If the user requests
other sources, such as Asana or Fellow, check actual capability and agree the read
scope before adding them. Capture app/workflow edits with
`python3 workbench.py capture-changes`; keep the private Markdown journal out of
shared material.


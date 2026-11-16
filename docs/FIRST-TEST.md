# Your first successful Workbench test

Ask your assistant to walk through this with you. No CRM write or scheduled job is needed.

## A. Local test, no connected accounts needed

1. Open the sample Workbench (`/?mode=demo`). Confirm the SAMPLE WORKBENCH banner and clearly fictional task data.
2. Mark one sample task done. Try Undo within the five-second pause. Mark it done again, wait for it to save, then refresh. Find it in Completed and use Reopen. This changes only your local sample copy.
3. Open Coaching and Insights. Notice where goals, evidence and source gaps appear.
4. Open your personal Workbench (`/?mode=personal`). Confirm your supplied name/context and that no fictional tasks, metrics or completed items leaked across. Return to Setup & sources if a preference needs changing.
5. Run `python3 scripts/test_starter.py` and `python3 workbench.py doctor`. Save the result in your private onboarding readout. These tests check local behavior, not source authentication.

Local pass: both views load, Undo/Reopen survives a refresh, and sample/personal state stay separate. If this is all you want to try, stop here. Sources, writes and schedules stay off.

## B. One useful read-only live test

After you approve specific sources in chat, choose one enabled workflow. Keep it small: one active deal, one recent attended meeting, or a current QCI goal.

- Confirm you are using your own work account, correct company/portal and your assigned/covered deal. Identify any identity or reporting-line gaps.
- Read the approved source context and links. Check dates, attendees, who owns the next action and whether the ask was already resolved. For a call test, compare the existing deal timeline before proposing a new log; do not create one yet.
- Prepare one real useful draft/next step if warranted. For QCI, use your actual goal and source-linked feedback, with unknowns visible. If nothing is actionable, report that honestly rather than inventing a task.
- Create a packet under workspace/personal/ using docs/DATA-CONTRACT.md. Import with `python3 workbench.py import workspace/personal/first-test.json --mode personal`. Refresh the personal view and verify the task, source link, date, owner, draft and source limits. Open source links to verify they refer to the intended item.
- Confirm no message was sent, no CRM property changed and no automation installed. Local completion is a user decision, never proof of an external action.

Live pass: one source-backed result, correct user/record scope, visible evidence/coverage and no unapproved writes. A blocked source means a partial result, not a failed local installation. Keep skipped/blocked sources visible in Insights and the readout.

## C. Optional next steps

Once the manual result looks right, choose which other approved sources/workflows to add. If you want recurring runs, pick the cadence and timezone with your assistant using docs/SCHEDULING.md. If you want automatic call logging or deal maintenance, preview the exact behavior and approve that separately. Check one real saved activity/update with live readback before treating it as proven.

## If something does not work

- Can't find files: give your assistant the exact extracted folder path or attach that folder as a local project.
- Missing Python: ask for help installing Python 3.10+ from the official source for your system.
- Address already in use: choose another port; do not stop someone else's process.
- Source inaccessible: connect/authenticate through your organization's supported tools if allowed; otherwise skip it for now. The kit does not transfer access or bypass company policy.
- No tasks/metrics: the personal view starts empty; this is expected until an approved source-backed packet is imported. Missing metrics remain unknown, not zero.
- Reopening tomorrow: open this same permanent folder and ask your assistant to start your personal Workbench. Your private progress remains in workspace/.

Share feedback using fictional examples or a sanitized description. Do not post your private workspace, customer records, personal QCI evidence or credentials to a team channel.

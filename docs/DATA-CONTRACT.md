# Local state packets

The app reads a view state and a separate progress ledger. Full examples are in examples/demo-state.json and examples/empty-state.json. Do not import the demo into a personal workspace. Real packets should be grounded in the new user’s source evidence.

Use `python3 workbench.py import packet.json --mode personal`. The importer upserts stable IDs and merges objects. It rejects identity, permissions and progress fields. A source refresh cannot replace checked-off decisions. `remove_task_ids` explicitly retires current queue entries while preserving their saved Completed snapshots.

## Task shape

```json
{
  "tasks": [{"id":"deal-source-event-phase","title":"Review the prepared response","label":"Review the prepared response","action":"Review the sourced answer and share it with the named rep.","owner":"verified user","why":"A supported customer question remains open.","done_when":"The reviewed answer has been shared.","status":"open","lane":"external"}],
  "morning_plan": {
    "priorities": [{"task_id":"deal-source-event-phase","id":"deal-source-event-phase","key":"deal-source-event-phase","title":"Review the prepared response","short_action":"Review the prepared draft.","external_view":"deal-work","waiting":false,"added_at":"2026-11-03T14:00:00Z","added_basis":"actual source reference","due_basis":"Agreed deadline unknown","due_label":"Due"}]
  }
}
```

Replace the example dates and labels with actual evidence; omit unknown due_at rather than making up a deadline. Add a verified portal-specific deal URL only after the portal and record identity are known. Do not use fabricated CRM IDs. A task’s communication can live in `communications.items` with id, task_id, recipient_name, body, source-backed outreach_context, resources and prepared_at. Only current unsent topics belong in a combined recipient draft.

Internal tasks use `morning_plan.internal` with stable id/title/action. Schedules use snapshot.schedule records with id/title/at/end_at/source_updated; dates must parse and include timezone offsets. Calls use stable call_id, title, verified time/type and actual source/deal links. Lists have ID upsert semantics; fields omitted from a packet remain unchanged. Arrays of plain text are replaced when supplied.

The backend injects profile, workspace_mode, automation_status and progress at read time. Never add those to import packets. Set personal profile fields in workspace/profile.json through onboarding instead. The backend does not call external systems and cannot verify a CRM write itself; the assistant must save actual receipts before labeling an action verified.

## Coaching view

Use coaching.focus for practices (id/title/prompt/proof_rule/status/feedback_ids), coaching.feedback and coaching.evidence for stable source records, and coaching.view.review for the saved week. The review can contain week_start/week_end/status/headline/highlights/lowlights/next_week_focus/coverage/manager_communication_id. Links and the actual reviewed extent are essential. Missing source material stays missing.

Store detailed call ledgers, source cursors, research, source transcripts and weekly Markdown under workspace/personal/. The app does not expose arbitrary files from that directory over HTTP. Source material should remain separate from reusable skills and examples so the clean export can be shared again.

## Request-first briefs

Import task_briefs: {"items": {"stable-task-id": {"requests": [{"person": "verified source", "date": "actual source date", "quote": "exact text", "url": "verified source link"}], "recommended_answer": "short sourced recommendation", "needed_from_you": "remaining decision", "facts": [], "caveats": "known limits", "sources": []}}}. Briefs merge by task ID and cannot overwrite the separate progress ledger. Full presentation guidance: ACTION-CARDS.md.

## Verified communication destinations

For a source-reviewed Slack communication, attach a local `delivery` object with
`verified: true`, `recipient_name` equal to the communication's exact current
audience, `slack_team_id`, and `web_url` pointing to the verified original
conversation. Include `slack_user_id` only after verifying the exact user, or
`slack_channel_id` for the exact channel/group. Record the source and readback date
in the private research ledger. For an existing DM, the verified client URL can
supply the workspace and conversation IDs without guessing a user identity.

Keep the communication's original `source_url`, author, message time and excerpt.
Do not place credentials, cookies or tokens in delivery data. If audience or
routing is uncertain, preserve the original supported web link and the specific
gap; never manufacture a verified binding to obtain a native app link. Apply
ACTION-CARDS.md's conversation review to every prepared response. Importing a
binding or opening its destination grants no sending authority.

## Demo-prep booking tasks

A verified upcoming demo without a matching sales-rep prep uses one stable task
bound to its native demo occurrence. Include `automation_feature_id:
"demo_prep_booking"`, the exact deal URL, verified demo event/rep source and
remaining booking action. Store actual saved prep-event readback separately;
missing source coverage is not proof that a prep is absent. Do not import a
permission grant or imply that a task toggle creates an event. Follow DEMO-PREP.md.

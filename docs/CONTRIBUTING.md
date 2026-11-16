# Contributing to Presales Workbench

Start with a small issue or pull request describing the user's problem, the
expected behavior and how you checked the change. Use fictional examples.

Do not submit customer records, private goals, transcripts, personal workspace
files, account sessions, credentials or access tokens. Preserve source gaps,
stable task IDs, saved progress, Undo/Reopen and each recipient's own approvals.
Source reads, sending, CRM writes and schedules stay off until that user approves.

Run the offline starter, upgrade, request-first and card-order checks from the
project root before proposing a change:

```sh
python3 scripts/test_starter.py
python3 scripts/test_upgrade.py
python3 scripts/test_card_order.py
node scripts/test_request_first.cjs
node scripts/test_card_order.cjs
node scripts/test_reply_options.cjs
```

Describe what changed, why it helps, what you verified and any limits. A saved
draft is not a sent message; a completed checkbox is not customer acceptance.
Maintainers review contributions before merging or publishing a release.
No private source access, production credentials or real customer test data are
needed to run these checks.

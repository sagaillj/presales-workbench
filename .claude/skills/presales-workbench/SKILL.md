---
name: presales-workbench
description: Run or maintain this local Workbench, import source-backed action/coaching packets, and preserve saved task progress. Use for Workbench setup, data refresh or local interface troubleshooting.
---

# Presales Workbench

Read ../../../docs/ARCHITECTURE.md and ../../../docs/DATA-CONTRACT.md as needed. Find the project root by its workbench.py and profile.example.json files; do not assume an absolute path. Use Python 3.10+ and the current user’s workspace. Demo and personal data are separate. Imports merge stable IDs and cannot replace progress or identity. Validate saved completion, Undo/Reopen and visible readback after changes. Export only the clean starter with workbench.py export; never include workspace data or credentials.

Check workspace/profile.json preferences.modules before running this workflow. Respect opt-outs and source-read approvals from onboarding; a selected workflow is not source access or write permission.

When presenting an action, follow ../../../docs/ACTION-CARDS.md: question/request first, short recommended answer, optional context and unsent replies. Preserve settled decisions and user progress.

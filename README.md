# Presales Workbench starter kit

A personal presales operating loop: prepare, follow through and improve.

[Source repository](https://github.com/sagaillj/presales-workbench) · [Versioned releases](https://github.com/sagaillj/presales-workbench/releases) · [Contributing](docs/CONTRIBUTING.md)

## Start with your assistant

Download the ZIP to Downloads, then paste this into Codex or Claude Code with local file access:

> I downloaded the Workbench starter. Find it, preserve existing setups, and follow its AGENTS.md and docs/ONBOARDING.md. Guide me through the short get-acquainted flow: one clear bounded read-only orientation and routine-upkeep choice, then real source-backed work. Keep setup in this Codex chat, check Python, run the first full review, import real results, then open normal Workbench with one markable orientation card in each work lane. Create/read back native upkeep jobs only if I approve. Keep external writes and sends off unless specifically authorized.

Workbench starts by getting acquainted through your approved work sources. You do
not need to fill out an identity form or choose check times up front. Your
assistant verifies what it can, asks only about necessary gaps, and gives you the
actual local URL after the first full review. Setup stays in the assistant chat; there is no browser setup wizard. Two clearly labeled orientation tasks show you how Customer work and Internal work cards work, and can be marked done without counting as real work or savings. Routine upkeep is adjustable in Settings. Each teammate uses
their own accounts, folder, approvals and native scheduling tools. A quiet audit
is valid; sample cards never become your real work.

## Try the demo yourself

Python 3.10+ is the only app requirement. No API key, npm install or cloud deployment is needed to view the demo.

- macOS: open `Start Workbench.command`, or ask your assistant to run it if your operating system requests confirmation.
- Windows: open `Start Workbench.cmd` with Python installed.
- Any supported computer: run `python3 workbench.py serve --open` from this folder. On Windows, `py -3` can replace `python3`.

A fresh launch opens the normal personal Workbench. The legacy `/setup` URL redirects there. To explore fictional examples explicitly, use `python3 workbench.py serve --mode demo --open`. The default address is `http://127.0.0.1:8781`. Stop the process with Ctrl+C. Use `--port` for a different local port. The app binds only to this computer.

## What is included

| Component | What it does |
| --- | --- |
| Workbench | Normal dark/light interface with two markable orientation cards, External work, Internal work, Coaching, Insights, Archive with restore and recoverable removal, Completed, schedule/activity, saved progress and Undo/Reopen |
| Onboarding | Runs in Codex: bounded source consent, current-user discovery, first full review/import, then the normal app |
| Daily closeout | Reviews available calls and communications, prepares researched answers, captures owned commitments and upcoming prep |
| Call hygiene | Deal matching, deduplication, source-note fidelity, saved-call readback and evidence-based status/Tech Win proposals |
| Weekly QCI | Source-linked feedback, later-call evidence, goal progress, next-call practices and an unsent manager update |
| Demo preparation | Outcome/proof planning, missing sales-rep prep reminders and optional internal prep booking; automatic booking starts off |
| Automation templates | Main review after recurring consent; optional daytime Slack/email checks start off to reduce token use; weekly QCI is optional. Native jobs require consent and readback |

Skills are included in `.agents/skills/` for Codex and `.claude/skills/` for Claude Code. They contain the same workflow instructions. See the [Codex skill guide](https://learn.chatgpt.com/docs/build-skills) and [Claude Code skill guide](https://code.claude.com/docs/en/skills) for local discovery.

## What needs your own setup

Live CRM, email, calendar, Slack, recordings, official scorecard and demo-building access use your assistant’s own authorized tools. This kit does not bundle OAuth credentials, connector servers, a private CRM API client, or a demo-generation service. The app itself never writes to those systems.

The onboarding workflow starts with a short permission choice, then learns your identity, manager, territory, current work and CRM mappings from the approved sources. It does not assume a CRM portal or inherit anyone’s permissions. Goals and unresolved facts stay unknown until supported. Optional preferences and timing can be refined later in Settings.

Read `docs/ONBOARDING.md` first and use `docs/FIRST-TEST.md` for the first-run checklist; `docs/ARCHITECTURE.md` explains the boundary between the app and the assistant. `docs/SCHEDULING.md` covers agreed native upkeep and assistant-specific scheduling limits.

## Private workspace and updates

Your profile lives in `workspace/profile.json`. Your goals, demo preferences and selected workflows are stored there too. The `demo/` and `personal/` subfolders under `workspace/` keep their own state, progress and imports. Those folders are never included by the built-in export command.

Source-backed runs generate JSON packets. Import with:

```sh
python3 workbench.py import path-to-packet.json --mode personal
python3 workbench.py serve --mode personal --open
```

Imports merge stable IDs and cannot replace your progress or identity. See `docs/DATA-CONTRACT.md`. A checked task is a local user decision, not proof of a sent message, customer acceptance or revenue.

## Share the clean starter again

```sh
python3 workbench.py export ../presales-workbench-starter.zip
```

This exports only the app, sample records, workflows, skills and setup material. Your `workspace/`, credentials, local logs and other files are excluded. Use the maintained starter repository and its versioned releases for shared updates; the ZIP is the easiest pilot handoff.

See [contribution guidance](docs/CONTRIBUTING.md) for small, reviewed changes with fictional examples. See [upgrade instructions](docs/UPGRADING.md) before updating an existing installation.

## Test your setup

Follow `docs/FIRST-TEST.md`: working local runtime → approved bounded orientation and first full review → genuine work or an honest quiet result plus two orientation tasks → normal personal view and any agreed native schedules. The sample and its Undo/Reopen demo remain optional.

## Validation

```sh
python3 scripts/test_starter.py
python3 workbench.py doctor
```

The local runtime and fictional-data interface are testable without connected accounts. Live-source completeness, CRM write readback and scheduled runs must be verified in each new user’s environment. This is a starter kit, not an already-connected team service.

## Updates

See RELEASE-NOTES.md for this version and docs/UPGRADING.md for an upgrade that preserves your existing workspace. Request-first cards are described in docs/ACTION-CARDS.md.

### New in v0.5

A compact combined header, Customer work/Internal work, a collapsible Schedule/Activity/Completed sidebar, simpler reply boxes, Coaching and Metrics views, five colorways and custom appearance settings. Setup happens in Codex: a short get-acquainted flow, bounded source orientation, the first full review and optional routine upkeep before opening Workbench. Existing approved capture tools and optional writing-style/value preferences can be refined afterward.

Optional weekly or biweekly product feedback stays in Workbench. Choose a score and Submit; your own fields and selected local counts go to the Workbench feedback Form, with a verified receipt when the collector is available. The prefilled Google Form is the fallback. Nothing submits automatically. Settings also checks for new public GitHub releases and offers a guided upgrade that preserves your workspace.

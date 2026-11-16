# Presales Workbench starter kit

A personal presales operating loop: prepare, follow through and improve.

[Source repository](https://github.com/sagaillj/presales-workbench) · [Versioned releases](https://github.com/sagaillj/presales-workbench/releases) · [Contributing](docs/CONTRIBUTING.md)

## Start with your assistant

Download the ZIP to Downloads, then paste this into Codex or Claude Code with local file access:

> I downloaded the SE Workbench starter ZIP to Downloads. Please find it, unpack it into its own permanent folder, and follow its AGENTS.md and docs/ONBOARDING.md to set it up for me. Walk me through onboarding and defaults, show me Workbench first, then ask before reading work sources. Run the first-test checklist with me. Keep writes and automations off until I approve them.

The assistant follows AGENTS.md and docs/ONBOARDING.md. It asks a few questions, offers defaults, shows the Workbench and then asks which work sources it may read. You can also use the local setup screen. Each teammate uses their own accounts and approvals.

## Try the demo yourself

Python 3.10+ is the only app requirement. No API key, npm install or cloud deployment is needed to view the demo.

- macOS: open `Start Workbench.command`, or ask your assistant to run it if your operating system requests confirmation.
- Windows: open `Start Workbench.cmd` with Python installed.
- Any supported computer: run `python3 workbench.py serve --open` from this folder. On Windows, `py -3` can replace `python3`.

On a fresh launch, `--open` opens the guided setup screen. You can return to `/setup` from Workbench controls. The default address is `http://127.0.0.1:8781`. Stop the process with Ctrl+C. Use `--port` for a different local port. The app binds only to this computer.

## What is included

| Component | What it does |
| --- | --- |
| Workbench | Guided first-run setup plus the dark/light interface, External work, Internal work, Coaching, Insights, Completed, schedule/activity, saved progress and Undo/Reopen |
| Onboarding | Learns the SE’s preferences, lets them choose defaults, opens a preview, then verifies identity/context through approved sources |
| Daily closeout | Reviews available calls and communications, prepares researched answers, captures owned commitments and upcoming prep |
| Call hygiene | Deal matching, deduplication, source-note fidelity, saved-call readback and evidence-based status/Tech Win proposals |
| Weekly QCI | Source-linked feedback, later-call evidence, goal progress, next-call practices and an unsent manager update |
| Demo preparation | Outcome/proof planning, source-backed context and a handoff to your available demo-building tools |
| Automation templates | Prepared daily and weekly prompts with human-readable suggested schedules; nothing scheduled automatically |

Skills are included in `.agents/skills/` for Codex and `.claude/skills/` for Claude Code. They contain the same workflow instructions. See the [Codex skill guide](https://learn.chatgpt.com/docs/build-skills) and [Claude Code skill guide](https://code.claude.com/docs/en/skills) for local discovery.

## What needs your own setup

Live CRM, email, calendar, Slack, recordings, official scorecard and demo-building access use your assistant’s own authorized tools. This kit does not bundle OAuth credentials, connector servers, a private CRM API client, or a demo-generation service. The app itself never writes to those systems.

The onboarding workflow starts with your own answers and verifies your identity, manager, territory and CRM field mappings after your source choices. Personal QCI goals, status definitions, approved write rules and preferred cadence belong to you. Unknowns remain unknown.

Read `docs/ONBOARDING.md` first and use `docs/FIRST-TEST.md` for the first-run checklist; `docs/ARCHITECTURE.md` explains the boundary between the app and the assistant. `docs/SCHEDULING.md` covers the two templates and assistant-specific scheduling limits.

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

Follow `docs/FIRST-TEST.md`: sample task → Undo/Reopen → separate personal view → one approved, read-only source-backed result.

## Validation

```sh
python3 scripts/test_starter.py
python3 workbench.py doctor
```

The local runtime and fictional-data interface are testable without connected accounts. Live-source completeness, CRM write readback and scheduled runs must be verified in each new user’s environment. This is a starter kit, not an already-connected team service.

## Updates

See RELEASE-NOTES.md for this version and docs/UPGRADING.md for an upgrade that preserves your existing workspace. Request-first cards are described in docs/ACTION-CARDS.md.

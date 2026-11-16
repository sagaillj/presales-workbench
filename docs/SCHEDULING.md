# Schedule after the manual workflow works

Nothing in this ZIP creates or activates a scheduled task. The two files in automations/ are ready-to-use prompts. Suggested cadence is a weekday daily closeout at 5:30 PM and Friday QCI at 6:00 PM, in the new user’s verified timezone. Those are starting suggestions, not mandatory team policy.

For Codex, ask it to inspect existing tasks, reuse a suitable one and configure the prepared prompt with the local project as context. Use its actual automation tools/UI rather than copying another person’s scheduler files or IDs. Select or invoke the corresponding skill in the task prompt. Test manually and review the first scheduled outputs before treating the workflow as dependable.

Claude Code can run the same project skills and manual workflows. Its scheduling capabilities depend on the installed environment. If a native scheduler is unavailable, state that limitation and keep the prepared prompts usable manually. Do not silently install cron, launch agents, browser helpers, background daemons or another product as a substitute.

For work on a local folder, the project and runtime must be available when the task runs. The [official scheduled-task documentation](https://learn.chatgpt.com/docs/automations?surface=app) describes local availability and workspace controls. Do not promise server-side execution of a folder on a sleeping computer.

Use one bounded delta review, save per-source coverage and reusable evidence, and notify on useful findings, a completed weekly review or a material gap. Do not generate unchanged status chatter. A task being configured is not proof it ran or that every source was checked.

Schedule only workflows the SE kept enabled in preferences.modules. Use only source-read and write scope explicitly authorized for the recurring run. A one-time test approval does not automatically authorize an ongoing source sweep.

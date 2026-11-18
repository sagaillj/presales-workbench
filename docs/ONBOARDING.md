# Guided onboarding for a new SE

The outcome is a personal Workbench the SE understands and can test. Start with a short conversation, not a questionnaire wall or a silent inbox scan. If the user completed the local /setup screen, read their saved choices and resume at the appropriate step instead of asking again.

Set aside at least an hour together for the full setup. Setup can be resumed between stages; a local preview can be available before source orientation and optional voice research finish. Prerequisite installation, account access and permission reviews can take longer. Codex guides the steps; the SE does not need to assemble the system alone. Check their Codex access and supported Python before a long research pass, and help with official installation instructions within their environment. Never claim setup or source coverage is complete merely because the screen opens.

## 1. Find and open the kit

When the user says it is in Downloads, search only for SE/Presales Workbench starter ZIPs or extracted folders there. Choose the unambiguous requested/latest release; ask if multiple different candidates remain. Inspect the archive layout, extract into a new standalone permanent folder (for example a user-chosen folder under Documents), and keep the original download. Do not overwrite an existing workspace, use another person's personalized repo as the new project, or carry its parent instructions into the installation.

Read this kit's AGENTS.md. Run `python3 workbench.py doctor` with an available Python 3.10+ interpreter (`py -3` is common on Windows). If Python is missing, explain the one-time requirement and help the user install it through an official source as allowed in their environment. Do not claim the ZIP installed a runtime. The local app needs no API key or package install. Use the actual folder for shell commands, not an assumed author path.

Open or attach this standalone folder in the assistant's local project. Explicitly read AGENTS.md even if automatic discovery has not happened yet. Repository skills live in .agents/skills for Codex and .claude/skills for Claude Code; CLAUDE.md points to this same workflow. Do not modify global assistant settings or install unrelated plugins.

## 2. Meet the SE

Offer a compact first question and accept a freeform answer:

> What name and work email should this use, and what segment and geography do you cover? If you know them, include your manager and time zone. You can leave anything for us to verify later.

Then ask one short follow-up, only for missing preferences:

> What are your top priorities and current QCI/development goals? Do you have a standard demo flow or any preferences you'd like me to follow? Optional details are fine to skip.

Use supplied facts; do not ask the same question again. Role/title, country, coverage and timezone are distinct. A suggested device IANA time zone is a proposal the user can accept, not territory evidence. Manager/director are optional before research. Mark unverified, unknown and user-reported facts clearly. Do not invent goals or apply another SE's manager feedback.

## 3. Choose defaults

Show this short menu and ask what to keep or turn off. These defaults enable local planning/drafting only.

| Workflow | Starts | What it does |
| --- | --- | --- |
| Daily checks & tasks | On | Calls, commitments, follow-ups and upcoming prep |
| Call hygiene | On | Match/deduplicate calls and propose evidence-backed deal updates |
| Proactive deal follow-through | On | Research questions, prepare answers and surface roadblocks |
| Demo preparation | On | Adapt the SE's flow to customer context and proof points |
| Weekly QCI & coaching | On | Evidence against personal goals and an unsent manager draft |
| Metrics / scorecard | On | Show official activity and outcomes when accessible |
| External writes, messages and demo creation | Off | Need separate concrete authorization |
| Recurring automations | Off | Optional after a successful manual test |

Save choices to workspace/profile.json using profile.example.json as the schema. For deterministic local configuration, create a private answers JSON under workspace/ and use `python3 workbench.py configure workspace/setup-answers.json`; see docs/SETUP-CONFIG.md. This saves preferences, never external permissions. Optional fields may remain null. If configuring by chat, identify evidence source as user statements in the current setup, not the local web form. The /setup page is an alternative, not a second mandatory onboarding.

## 4. First look before access

Start `python3 workbench.py serve --port 8781 --open`. The first launch opens /setup for users doing screen-based setup. If another app occupies the port, choose a different one; never stop an unrelated process. Keep the local process alive and state how to reopen it. The same server supports `/?mode=demo` and `/?mode=personal`, with separate state/progress. /setup is always available from Workbench controls.

Show the sample Workbench, then the user's empty personal Workbench. Explain Customer work, Internal work, Coaching and Metrics. Schedule, Activity and Completed with Undo/Reopen live in the optional sidebar. Settings offers five colorways, custom colors/fonts, weekly feedback and a latest-release check. Sample tasks, people, deals and metrics are fictional. They must never become the SE's personal records. Do not claim the empty workspace already has source connections.

Let the user take a look. Do not read work content or jump into a source audit before the user has had this first look.

## 5. Ask for sources, then research

Now offer one concise multi-select choice. Read-only choices are optional and initially unselected. A selected workflow is not permission to read its source.

| Source | Proposed first-read scope |
| --- | --- |
| Work email | Last 14 days: active-deal questions/commitments |
| Work Slack | Last 14 days: direct mentions and active-deal threads |
| Hex / official scorecard | Current month/quarter: own activity and credited outcomes |
| CRM | Own assigned/active deals, current fields and recent activity |
| Work calendar | Past 7 / next 14 days: work meeting context |
| Meeting notes/transcripts | Attended work calls from last 7 days |
| QCI/goals documents | Current-quarter documents the user identifies |

For example: “Which of these may I read to populate and verify your Workbench? You can pick any, all, or skip for now.” Carry those source names and scopes into the actual question. Tool metadata discovery alone is fine before approval; do not read emails, messages, scorecard rows, people-directory content or private CRM records until covered by approval. Ask once for the combined selected scopes, not one consent loop per tool call. Honor any scope already explicitly granted in the current setup chat.

The local screen saves read_requests as awaiting_chat_approval and produces a handoff prompt. It does not connect accounts or grant a content-read authorization by itself. Confirm those requested scopes in chat before reading. Authentication and installed connectors are separate from consent. Research only approved sources through the current user's native tools, within normal environment permissions and organization policy. The viewer is local; the assistant and configured source providers may process approved content in their services. If a different directory/source is needed to resolve reporting lines, request that focused addition or accept the user's answer as unverified. Do not silently expand to the whole company.

Verify stable work email/profile, company/workspace, actual manager/director, role lane, segment, geography/country/coverage, IANA timezone, CRM portal/SE-owner property, current status/Tech Win definitions and actual QCI goals. Prefer authenticated account/profile records plus current official directory/territory/scorecard mappings. Frequent collaborators are not managers; a title or timezone does not prove a segment or territory. Ownership in CRM may differ from the sales owner. Match stable identity, not display name alone.

Add identity_evidence entries with field, value, source/reference, observed time and confidence. Record explicit source approvals (scope, chat reference, timestamp), connector availability/auth status and actual read extent under private sources. Do not store tokens, cookies or credentials. Do not set identity.verified true until supported by approved authenticated evidence. Conflicts remain visible; ask only what cannot be resolved from approved sources. Do not replace richer existing verified profile details with blank form fields.

## 5a. Establish call capture

Ask how attended calls are captured. Recommend an organization-approved Granola or Wispr Flow Notetaker setup, or confirm reliable Zoom/Gong recordings and accessible transcripts. Verify meeting transcription is enabled and available; ordinary dictation is not evidence of a captured call. A calendar invite is not call evidence. Record the user's selected provider and actual transcript availability privately; do not enable recording, install a recorder, purchase a plan or upload audio without the user's specific approval. Review the provider's capabilities and the user's organization rules before proposing recording behavior. If no transcript source is available, show the coverage gap and continue the local setup without inventing call summaries. The source choice is a preference, not proof that transcription works.

## 5b. Help drafts sound like the SE

Include writing style in the local wizard. Accept the user's own description and
offer an optional 3- or 6-month sample of their own sent work Slack and email,
including new-deal introductions, short replies, customer email and existing
voice-note transcripts. This is a separate source scope, not an expansion of the
normal 14-day deal review. The form selects a scope; the assistant still gets
explicit approval in chat before reading it. Existing approval can be reused only when it already covers the same source, authored-message scope and selected date window.

After approval, use the user's native tools and authenticated identity. Sample
across the selected date window and channels. Keep only their authored text;
exclude quoted replies, forwarded text, signatures, automated reports, known AI
boilerplate and unrelated personal/sensitive content. Prefer existing voice-note
transcripts. Do not claim an audio review when only a transcript was read, and do
not silently generate or upload audio transcripts. Save source/date, speaker and
timestamp where applicable, partial excerpts and any coverage gaps.

Save private workspace/voice-profile.json with concise Slack/email rules,
relationship-specific familiarity, normal length, greeting/closing habits and
phrases to avoid. Put a few dated examples and source links in a private evidence
file. Show three short example drafts so the SE can tune the result, then apply
these rules to drafting in enabled workflows. Default should be the shortest
useful answer; Concise is shorter and Detailed adds only necessary context.
Preserve saved user wording and completed/sent records. Style is not permission
to send and does not establish deal facts or commitments. Never ship another
operator's profile, quotes or message history in a starter/export. If the user
skips source review, record preferences only and label the profile unsampled.

## 6. Test, then offer automation

Follow docs/FIRST-TEST.md. Run only enabled workflows against approved sources. Create a genuinely useful source-backed task/draft when evidence supports one, otherwise record a quiet/no-action result with coverage. Keep missing sources explicit. No fabricated busywork or metrics to make the page look populated.

Save workspace/ONBOARDING-READOUT.md with supplied/verified profile facts, selected workflows, demo preferences/goals, approved/skipped/blocked sources, test results and remaining gaps. Report separately: local app ready; source research verified/partial/skipped; manual workflow tested; external writes off; schedules off. A missing connector does not block the local preview.

Offer optional scheduling only after a successful manual run. Ask the user's preferred cadence/timezone and workflow scope, inspect the assistant's scheduler capability, and follow docs/SCHEDULING.md. Never install jobs merely because a template exists. A JSON flag is not authorization. For any requested call/deal/demo/message write, prepare a concrete preview, receive approval for its exact scope, then verify the actual external saved result.

## 7. Keep it useful

Explain Settings > Check for updates: it requests only public release metadata from the dedicated GitHub repository. It downloads or executes no code. A new version provides a copyable Codex prompt and the release link; follow docs/UPGRADING.md to preserve the private workspace and review app-file conflicts. Updates are guided, not forced. Explain that the open app checks public GitHub release metadata once a day by default, which can be disabled in Settings. This is not a new scheduler job or an automatic installer.

Weekly feedback appears in Internal work from Friday, with a weekly or every-other-week cadence and an off option in setup/Settings. The user chooses a 0–10 recommendation rating and optional time estimate/comments. Work email is prefilled when available and remains optional. Local counts include days opened and tasks marked done, only if included by the user. Show the destination and what is shared. Nothing is submitted automatically. Submit feedback writes through the fixed maintainer collector into a Google Form and linked Sheet; mark Saved only after its verified response receipt. A prefilled Google Form remains the fallback, requiring Submit in that tab and a separately labeled user-reported local confirmation. Never infer submission from an opened page or iframe load. See docs/FEEDBACK.md.

For reusable improvements, open a reviewed PR to the public repository, or use the maintainer contact shown in Settings. Keep workspaces, transcripts, customer content and credentials out of contributions. Offer the latest verified release rather than a pinned historical ZIP.

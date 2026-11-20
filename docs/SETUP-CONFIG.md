# Local setup and evidence receipts

The normal path is the short orientation-first flow in ONBOARDING.md. Do not use
the advanced preferences object below as an identity questionnaire up front. The
welcome action is `orientation_request` with selected `sources` and
`recurring_requested`; `cadence_preferences` stores proposed light/main timing
and a verified time zone when known. Neither action grants access or creates jobs.
Only actual current-chat consent permits the source pass or native scheduling.

After real work and verification, the assistant uses
`python3 workbench.py record-orientation <actual-receipt.json>` and, after actual
native job creation/readback,
`python3 workbench.py record-schedule <actual-receipt.json>`. Their evidence fields
are documented in ONBOARDING.md. Never manufacture success receipts or use them
to import permissions. A successful first run does not automatically verify
identity or activate a job.

## Advanced preferences and older clients

The chat agent and Workbench Settings use the same profile. There is no browser setup screen; `/setup` redirects to the normal app. `configure` accepts a local preferences object, not a source import and not a credential file. Existing private state and progress are preserved.

Create workspace/setup-answers.json using actual user input:

```json
{
  "action":"preferences",
  "name":"the current user's supplied name",
  "email":"",
  "segment":"",
  "geography":"",
  "timezone":"",
  "manager_name":"",
  "goals":"one actual priority per line",
  "qci_goals":"",
  "demo_flow":"",
  "demo_preferences":"",
  "modules": {
    "daily_closeout":true,
    "call_hygiene":true,
    "deal_followthrough":true,
    "demo_prep":true,
    "weekly_qci":true,
    "scorecard":true
  }
}
```

Never use the literal explanatory name/goal placeholders as live profile values. Only name and all six boolean module choices are required; omit unknown optional fields or use blank text. Other allowed text fields are title, company, role_lane, country, manager_email, director_name and director_email. Timezone must be a valid IANA value when supplied. Email fields must be valid email addresses when supplied. Goals/QCI text use one item per line.

Run `python3 workbench.py configure workspace/setup-answers.json`. The result reports the private profile and handoff. Inputs cannot set identity.verified, HubSpot mappings, write permissions or schedules. Facts begin as user_reported; a chat agent should change local_setup_form evidence to its actual current-chat source reference. Verified identity conflicts are rejected rather than silently changed.

The older `preferences`, `preview_seen` and `sources` actions remain compatibility paths for existing saved setups. They do not impose a sample/empty-preview gate on the new orientation-first flow. Use `orientation_request` for a new setup. Legacy source keys include email, slack, hex, crm, calendar, meeting_notes and qci; requested scopes still await actual chat approval and never establish a completed connection. Do not claim a preview was seen unless it was actually shown.

Approved source-read scopes and verified facts are added by the assistant to the private profile with actual references after the corresponding user choice/research. Preserve write permissions and authorization evidence separately. Reopening a live configured workspace is not a new setup; review existing choices before proposing changes.

## Internal demo-prep booking preference

New users start with `preferences.demo_prep_booking.enabled: false`, all
`permissions` values false, and no write authorizations. The normal Workbench
Settings switch and eligible task checkbox save only:

```json
{"action":"demo_prep_preferences","enabled":true}
```

The same object can be passed to `configure`. Extra permission fields are rejected.
The local server persists the choice and leaves grants, source access, schedules,
progress and identity unchanged. Continue in Codex copies a scoped handoff; it does
not book anything. Follow DEMO-PREP.md to obtain or reuse the current user's
specific internal-prep calendar authorization, verify live availability and saved
results, and keep customers and unrelated writes outside that grant. Private
notice/placement/color settings can be added by the assistant from actual user
choices; no other operator's settings belong in the shared profile.

## Optional daytime communication checks

New users have schedules.light.enabled=false. Stored light.local_times are inactive suggestions. The cadence API accepts an explicit boolean light_enabled alongside saved times; saving times or ordinary recurring consent never opts the user into daytime checks. The assistant creates a light native job only after the user opts in and grants recurring scope. Daily-only scheduling receipts are valid while daytime checks are off. Existing explicit choices and verified active legacy light jobs are preserved during upgrades; profile defaults never silently disable an actual job. See SCHEDULING.md.

# Local setup answers

The chat agent and /setup screen use the same profile. `configure` accepts a local preferences object, not a source import and not a credential file. Existing private state and progress are preserved.

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

After the user has seen the local first look, the agent may record `{"action":"preview_seen"}` in a new private JSON file and run configure on it. Only then may it record source preferences with `{"action":"sources","sources":["crm","calendar"]}`. Available keys: email, slack, hex, crm, calendar, meeting_notes, qci. An empty list is valid. These are requests awaiting approval in chat, never completed source connections. Do not record preview_seen until the preview was actually shown.

Approved source-read scopes and verified facts are added by the assistant to the private profile with actual references after the corresponding user choice/research. Preserve write permissions and authorization evidence separately. Reopening a live configured workspace is not a new setup; review existing choices before proposing changes.

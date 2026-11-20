# A quick weekly check-in

Workbench asks for a 0–10 recommendation score and optional notes about what helped or should improve. Your work email can be prefilled from setup and stays optional. Estimated hours saved and local usage counts are under Time saved & usage counts. You can include or omit those counts before submitting.

Settings and setup let you choose every week or every other week, or turn the check-in off. The default is to ask each week, from Friday. Nothing is submitted in the background. Schedules, email sends and broad source permissions are not installed by this feature.

## Submit inside Workbench

When the maintainer's collector is available, choose a score and click Submit feedback. The local server sends only the displayed fields to the fixed collector. The collector validates the payload, saves it as a Google Form response, reads the response ID back and returns a receipt. Only that verified receipt produces Saved in Workbench and closes the weekly check-in. The linked Google Sheet receives the Form response.

The payload contains the week, app version, chosen score, optional email/comments/time estimate, optional counts, and a submission reference for duplicate protection. Counts are days this local app was opened and tasks currently marked done during the week. They are not verified calls, externally completed deliveries, unique people or measured time savings. Hours saved is self-reported. Identity is also self-reported, not authenticated by the collector.

The random installation identifier stays local. The weekly submission reference is a one-way digest and changes each week. No customer names, deal text, Slack messages or transcripts are automatically included. Keep private work content out of your comments.

## If the collector is unavailable

Your answers remain saved locally. A request with uncertain status stays unconfirmed, and retries reuse the same submission reference so the service can recover an accepted write without duplicating it. Do not claim a saved response until a valid receipt arrives.

The prefilled Google Form is a fallback. Workbench supplies the fields, you review them and click Submit in Google Forms. Opening the form is not proof of submission. A local I submitted the form confirmation is explicitly user-reported. There is no copying or pasting. Very long Unicode comments may need shortening to fit a reliable prefill URL.

Local records live under workspace/<mode>/product-feedback.json, separate from task progress and excluded from clean exports. Demo and personal modes are separate. Feedback never changes CRM permissions or sends email.
# First check-in timing

The NPS check-in remains hidden until **10 distinct days of actual local use**.
Repeated visits on one day, installation age and downloads do not count as extra
days. The first prompt can appear on the tenth use day; subsequent prompts honor
the selected weekly or every-other-week cadence. Early manual links do not expose
the rating form. Feedback remains optional and is sent only by the user.


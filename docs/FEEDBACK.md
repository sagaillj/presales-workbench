# Workbench Check In

After ten distinct days of use, the optional check-in asks for a 0–10 recommendation
score and a comment. Submit feedback sends it; Not this week skips locally.
Settings retain weekly/every-other-week/off choices. Nothing submits in the background.

The email already known to this installation is supplied automatically. The normal
card has no email, hours, usage checkbox or explanatory sections. A short footer
explains that feedback and usage estimates are shared on Submit.

## Background usage and hours estimate

Submissions include aggregate days used, completed-task counts, weekly task-event
counts, estimate coverage for week/month, app/Python/OS/browser category, viewport
category, cadence, week and duplicate-protection reference. No task text, customer
names, source messages, transcript content, URLs, machine names or credentials are
collected automatically. Comments remain optional free text supplied by the user.

Estimated hours is one point estimate: the midpoint of existing category-based net
minutes saved, summed once across eligible completed work. This is an assumption,
not measured time. Orientation, future/undated work and unestimated older completions
are excluded. Unknown estimate coverage stays explicit; the value is null when
completed work lacks estimates. No invented savings are assigned to unobserved work.

The fixed collector stores metadata in the Form usage answer, estimates in the hours
answer, and known email in the identity answer. A verified receipt marks submitted;
uncertain writes retain their exact original payload for safe retry. Old clients and
pending submissions remain supported. The prefilled Form is an exceptional fallback,
not a successful send; its submission confirmation is user-reported.

Private records remain under workspace/<mode>/product-feedback.json and are excluded
from downloads. The maintainer collector source is under scripts/feedback-collector
with its private deployment Form ID left unconfigured; recipients need not deploy it.

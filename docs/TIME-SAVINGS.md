# Estimated time saved

Metrics shows an assumption-based range for newly completed Workbench actions.
It is separate from measured time, revenue and scorecard credit. Saved completions
count once by stable task ID. Reopening removes them. Older completions without
an estimate remain excluded, with their count shown.

Default net minutes saved after human review:

| Task metadata `time_savings_category` | Minutes |
| --- | --- |
| `context_review` (default) | 5–10 |
| `prepared_reply` | 5–15 |
| `meeting_prep` | 15–30 |
| `demo_prep` | 45–90 |

Set the category explicitly on a task in the assistant's import packet. A task's
name alone never selects a larger range. A recommendation accepted for later use
is not completed delivery and receives no estimate. Each new completion retains
the versioned range, so later policy changes do not rewrite earlier estimates.
These initial assumptions should be calibrated with actual user timings.

The weekly feedback form suggests the lower weekly estimate. Review, change or
clear it before submitting. Feedback sends only through the existing explicit
Submit action. The estimate does not add background telemetry or a new schedule.

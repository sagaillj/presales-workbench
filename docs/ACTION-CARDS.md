# Request-first action cards

Show the actual question or request first, using a faithful excerpt or full text,
with the person, source date and verified link. Keep rep clarification distinct
from a customer ask. Put a short recommended answer and only the necessary user
decision above the fold. Do not restart an already-settled decision or inflate a
clarification into an unrelated implementation project.

Put deal background, people/roles, timeline, reasoning, material limits, source
coverage, actual delivery receipts and prepared implementation detail behind
More context, collapsed by default. Keep local unsent replies collapsed too.
Support a direct customer response or a rep response when identities/audiences
are verified. Do not send either without the current user's authorization.

Use state.task_briefs.items keyed by the existing stable task ID. Suggested fields:
requests (person/date/quote/url/basis), recommended_answer, needed_from_you,
trigger, people, facts, action, done_when, caveats, sources, prepared_answer.
Quoted text must be real source text. Label a paraphrase or user report honestly.
Missing latest replies make a draft conditional, not ready-to-send. Do available
reading/research first rather than assigning the user a generic source-search chore.

Keep one highlighted action; later rows stay collapsed. Preserve original
deadlines, stable IDs, user edits, completed work, Undo/Reopen and source cursors.
Copying a draft never proves sending, completion, a test result or customer acceptance.

## Reply to the actual conversation

Before preparing or refreshing any reply, read the exact latest incoming AND sent
messages in the original DM, group DM, channel or email thread, including replies
to older roots and relevant cross-channel answers. Reconcile current CRM state,
bookings, delivered work and saved user edits. A task title or generic first-touch
template cannot substitute for that conversation.

Make a compact source-backed reply plan: what the other person said or requested,
what has actually been handled, what the user still needs to communicate, and any
useful unresolved question. Answer the latest message naturally first. If a rep
booked a demo and asked the user to join a deal, and native CRM readback already
confirms the assignment, acknowledge the booking and confirm the verified result
before adding optional prep questions. Do not bury that answer under a customer
brief or claim that an existing assignment was newly made.

A completed system action can leave a separate acknowledgment worth sending;
it does not reopen that action, prove a message was sent or create a new thank-you
chore for every FYI. Preserve partial unanswered asks, completed stages, stable IDs
and user wording. Check every response alternative against the same conversation.
Keep drafts local and unsent unless this user separately authorizes sending.

Source fingerprints, recent timestamps and asserted review flags do not judge
whether wording makes conversational sense. The assistant must perform this
meaning check using actual reviewed evidence. If relevant latest messages are
unavailable, retain the source gap and keep the draft conditional rather than
certifying a generic reply.

## Direct Slack shortcuts

While reviewing a Slack conversation, retain its exact native workspace/team ID
and conversation or verified user ID with the original web URL. Use only the
current user's actual signed-in source readback; never infer IDs from a name,
workspace subdomain or another operator's installation. Supply verified delivery
bindings as described in DATA-CONTRACT.md. Known native destinations open Slack
directly without creating a redirect tab. Preserve the exact browser link as a
fallback, particularly when the workspace or destination cannot be verified.
Opening Slack or copying a message does not send it or complete the task. Do not
close the Workbench tab, use a timed auto-close as proof of successful launch, or
try to control Slack's cross-origin redirect page.

## Saved personal order

Drag a card by its dotted handle to change its position within External or Internal work. The first card becomes highlighted. Use Arrow Up/Down, Home or End on the focused handle as a keyboard alternative. Reset order restores the recommended grouping and date order. User order is stored by stable task ID in workspace/<mode>/card-order.json, independently of completion, dates and imports. New tasks append in recommended order; hidden/completed IDs do not revive work. Preserve this file during upgrades.

## Prepared response alternatives

For a necessary communication, prepare at least three distinct responses for the same verified audience: a recommended balanced version, a very concise version and a more detailed or otherwise useful alternative. Adapt these choices to the actual ask rather than forcing a rigid template. Store them in the communication record as response_variants with stable id, label, body, recommended and an optional recommendation reason. The carousel shows the top pick first and copies only the selected response.

Use short paragraphs and real numbered or bullet lists. Slack wording should be warm, conversational and direct, using the recipient’s name and normal contractions where appropriate. Preserve material facts and caveats across alternatives; never add promises or claim a test or send happened. Recipient/channel reminders stay outside copied text.

Preserve user-edited drafts and confirmed sent stages. Old drafts without alternatives remain usable as one version; prepare genuine alternatives during the next relevant evidence-backed update, rather than repeating or mechanically padding one draft. Scope changes and user edits take precedence over stale alternatives.

Bind alternatives to the exact original communication body and audience using response_variants_source_body and response_variants_source_recipient (recipient_key, otherwise recipient_name). Regenerate alternatives when the body, audience or active topics change. The UI suppresses stale/unbound alternatives and preserves the current draft instead.

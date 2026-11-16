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

## Saved personal order

Drag a card by its dotted handle to change its position within External or Internal work. The first card becomes highlighted. Use Arrow Up/Down, Home or End on the focused handle as a keyboard alternative. Reset order restores the recommended grouping and date order. User order is stored by stable task ID in workspace/<mode>/card-order.json, independently of completion, dates and imports. New tasks append in recommended order; hidden/completed IDs do not revive work. Preserve this file during upgrades.

## Prepared response alternatives

For a necessary communication, prepare at least three distinct responses for the same verified audience: a recommended balanced version, a very concise version and a more detailed or otherwise useful alternative. Adapt these choices to the actual ask rather than forcing a rigid template. Store them in the communication record as response_variants with stable id, label, body, recommended and an optional recommendation reason. The carousel shows the top pick first and copies only the selected response.

Use short paragraphs and real numbered or bullet lists. Slack wording should be warm, conversational and direct, using the recipient’s name and normal contractions where appropriate. Preserve material facts and caveats across alternatives; never add promises or claim a test or send happened. Recipient/channel reminders stay outside copied text.

Preserve user-edited drafts and confirmed sent stages. Old drafts without alternatives remain usable as one version; prepare genuine alternatives during the next relevant evidence-backed update, rather than repeating or mechanically padding one draft. Scope changes and user edits take precedence over stale alternatives.

Bind alternatives to the exact original communication body and audience using response_variants_source_body and response_variants_source_recipient (recipient_key, otherwise recipient_name). Regenerate alternatives when the body, audience or active topics change. The UI suppresses stale/unbound alternatives and preserves the current draft instead.

# Call logging and deal hygiene

Run only when the relevant workflow is enabled in workspace/profile.json and its required sources are approved. Report skipped or inaccessible sources without silently expanding scope.
## Establish the evidence

Verify the current user’s CRM owner ID and current ownership at write time. Match the held meeting to the correct deal using account, rep, stakeholders, timing and the actual call context. Ambiguous matches stay pending. Do not manufacture calls for invitations, portal builds, general team meetings or activity counts.

Use the calendar occurrence’s exact start when available; otherwise use the recorded meeting start and label the fallback. Interpret timezone-less notes in the verified user timezone, not automatically as UTC. Deduplicate by source meeting ID and existing deal timeline before attempting a save. Keep a local attempt ledger with intent, source, target, result and readback so an uncertain request is not retried blindly.

## Preserve the source and save correctly

For Granola, start the body with the actual transcript link in the form `Chat with meeting transcript: https://notes.granola.ai/t/<actual-meeting-id>`, then preserve the provided summary/headings/bullets/wording. Never invent the link. Use equivalent source links and faithful notes for other systems. Put synthesis separately from the raw source note.

Use a customer-facing call type for customer discovery, technical calls or demos, and the proper internal prep/team-sync type for internal deal work. Resolve valid option values from the connected portal, not a guessed enumeration.

For HubSpot use the matched deal activity timeline: Activities → Calls → Log Call, or a native tool that can prove the equivalent saved CALL association. Do not use a standalone review index as evidence of saving to the deal. After a permitted save, read back the call ID, associated deal, owner, start time, type and body on that deal’s timeline. A draft or submit click is not completion. If the result is uncertain, inspect the existing timeline before retrying.

## SE status, Tech Win and notes

These require separate applicable permission. Discover the new user’s exact property names, option definitions and manager/team rules. Suggested semantics to verify:

- Active: concrete current or scheduled SE work and a clear next step.
- Tracking: credible likely support with a review/re-engagement trigger.
- Completed: SE support is finished or no clear SE next step remains, with evidence and a reason. The sales deal can still be open.
- Tech Win: capture explicit, scope-specific customer acceptance or remaining technical concerns. Internal preparation, a generic compliment or a checkbox cannot establish Yes. Preserve a validated scope and caveats if another scope is still under review.

Do not infer state from an old date or inaccessible source. Draft leadership-readable notes with current state, supported outcomes, next action/owner/date, technical-win path and biggest risk. Preserve useful prior notes. Keep credited revenue, Led/Assisted credit, call count, user completion and technical acceptance separate.

Record exact before/after values and source evidence for every authorized update; recheck ownership immediately before changing anything. No automatic stage, amount, owner, reassignment, message or calendar changes are part of this workflow.

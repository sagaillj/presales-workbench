# Upgrade without losing your workspace

Stop the existing Workbench server. Download and extract the new release, verify
its checksum, then run from the new release:

    python3 scripts/upgrade_existing.py /path/to/your/existing/starter

The helper verifies both manifests and checks for locally edited distributed
files before writing. Conflicts stop the upgrade for review. It preserves the
entire workspace (profile, source approvals, personal state, progress and history)
and backs up replaced app files under workspace/upgrade-backups. It never grants
access, installs schedules or sends anything. Restart the existing Workbench and
verify your version, progress and a request-first card. For a first install use
the normal onboarding instead. Keep the prior ZIP for rollback.

Workbench checks public GitHub release metadata once a day while open and during
the existing daily workflow. Turn daily checks off in Settings if you prefer.
A newer stable release appears as one **Workbench update** card in Internal work.
Choose **Approve update** to queue exactly that version for the next workflow, or
**Copy prompt** to ask your assistant to update now. You can cancel a queued
approval. The card shows any preflight blocker rather than silently replacing
locally edited app files. No private data is uploaded by the check.

The daily workflow runs `python3 scripts/check_updates.py` and reads the queued
approval. Only a queued approval authorizes installing that exact release. Verify
its fixed GitHub release identity, checksum and bundle manifest, back up, use the
existing upgrade helper, restart, and check version plus preserved progress. Use
`--outcome installed --version X.Y.Z --detail "verified checks"` only after those
checks succeed. Record `--outcome blocked` with an exact reason for local app edits,
unmanaged installs or other preflight failures. This grants no new source access,
external writes or schedules. A local development checkout must never be replaced
with a generic starter installation.

The private workspace also holds weekly product feedback and writing preferences. These stay in place during the upgrade. Locally customized app files require review instead of silent replacement. Verify the downloaded checksum against the matching GitHub release, then the included manifest.

# Upgrade without losing your workspace

Stop the existing Workbench server. Download and extract the new release, verify
its checksum, then run from the new release:

    python3 scripts/upgrade_existing.py /path/to/your/existing/starter

The helper verifies both manifests and records local edits before replacing app
files. Compatible edits are reapplied using the verified upstream baseline.
Overlapping edits stop the upgrade for review. It preserves the
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

The private workspace also holds product feedback and writing preferences. These
stay in place during the upgrade. Verify the downloaded checksum against the
matching GitHub release, then the included manifest.

## Your Markdown change journal

`workspace/LOCAL-CHANGES.md` is the private record of your app, workflow and
settings customizations. It contains a restorable packet with exact file bytes,
hashes and available original baselines, plus preference snapshots. Appearance
is saved locally too, so a changed local port need not lose your theme. Source
data, progress, feedback answers, credentials and access grants are not copied
into this journal. Keep the whole `workspace/` when updating; do not upload it.

The server checks for file changes at most once a minute while open, records
settings saves, and the upgrade helper always captures immediately before an
update. You or your assistant can capture immediately with:

    python3 workbench.py capture-changes

The helper reapplies non-overlapping edits and preserves user-added source files.
If both the release and your edit change the same lines, it stops before replacing
app files. On the first upgrade from an older release, an edited file may lack its
original baseline; the Markdown still preserves your full local version for your
assistant to reconcile. No conflict markers or unreviewed code are executed.

For an older install with missing baseline bytes, the assistant can recover its
original versioned release, verify its checksum/manifest against that version,
then pass `--baseline-folder /path/to/verified/original/release`. Only bytes whose
hash matches the installed manifest can supply that baseline. Do this source
research before asking the user to resolve a routine upgrade problem.

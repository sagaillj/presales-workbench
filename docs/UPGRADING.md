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

## Daily automatic updates

Automatic updates are ON by default. During the existing daily review,
`python3 scripts/check_updates.py` checks the fixed public GitHub release channel
at most daily, downloads a newer stable release, verifies its checksum, version,
complete manifest and safe ZIP paths, and queues that exact release. No newer
version means no download or Internal work card. A network failure leaves the
current installation in place. No separate schedule is created.

When the command returns `workflow_action`, the assistant completes the update
in the SAME daily review without requesting another version approval: stop only
this installation's verified server, run `python3 scripts/check_updates.py
--install-staged`, restart on the existing local URL, and verify VERSION plus saved
progress. The installer refuses a running app, unmanaged installation or development
checkout. It uses the local change journal, conflict preflight, backup and rollback
helper above. Overlapping edits or failed checks leave one Internal work update
card with the exact blocker. Resolve the blocker and retry; never overwrite edits.
An installed receipt records file verification, not proof of restart or UI readback.

Uncheck **Keep Workbench automatically up to date** in Settings to require
**Approve update** on the single Internal work card instead. This still checks
GitHub daily but does not download or install without that version approval.
Turning off automatic release checks also prevents unattended downloads/installs;
manual Check for updates and exact-version approval remain available.
Previously disabled daily checks stay disabled. Preferences and the entire private
workspace, including local customizations, source approvals, schedules and progress,
are preserved. Update preference changes grant no source access or external actions.

`--check-only` reads metadata only. `--force` refreshes metadata rather than waiting
for its cache. Legacy `--outcome` reporting remains supported, with exact VERSION
readback required for installed. Older installations need one normal upgrade to
this release before its automatic update behavior can run. Never replace a private
development checkout with the generic starter.

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

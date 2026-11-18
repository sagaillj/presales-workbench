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

In Settings, choose **Check for updates** to read the latest public stable release metadata. By default the open app also checks once a day; turn this off in Settings. This is a public metadata check, not a push service or an installer. Follow the copyable prompt with Codex. No private data is uploaded. The Settings gear gets a small update dot when a newer stable release is available. Weekly email updates can point to the same latest-release URL; local installations cannot be forcibly updated by this page.

The private workspace also holds weekly product feedback and writing preferences. These stay in place during the upgrade. Locally customized app files require review instead of silent replacement. Verify the downloaded checksum against the matching GitHub release, then the included manifest.

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

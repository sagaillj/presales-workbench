"""Private, restorable customization journal. Never exports or executes its text."""
from datetime import datetime, timezone
from pathlib import Path
import base64
import difflib
import hashlib
import json
import os
import re
import tempfile
import threading
import time

MARKER = '<!-- workbench-local-changes:v1 -->'
DIRECTORIES = {'app', 'scripts', 'docs', 'automations', '.agents', '.claude'}
OMIT = {'BUNDLE-MANIFEST.json', 'PACKAGE-REPORT.json', 'VERSION', 'RELEASE-NOTES.md'}
_LOCK = threading.RLock()
_CHECKED = {}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', dir=path.parent, encoding='utf-8', delete=False) as out:
        out.write(text)
        name = out.name
    os.replace(name, path)


def safe(root, name):
    root = Path(root).resolve()
    part = Path(name)
    if (part.is_absolute() or '..' in part.parts or not part.parts
            or any(p.casefold() in {'workspace', '.git', '__pycache__'} for p in part.parts)):
        raise ValueError('Unsafe customization path: ' + str(name))
    path = root / part
    if not path.resolve(strict=False).is_relative_to(root) or path.is_symlink():
        raise ValueError('Customization path escapes installation: ' + str(name))
    return path


def manifest(root):
    path = Path(root) / 'BUNDLE-MANIFEST.json'
    return json.loads(path.read_text())['files'] if path.is_file() else {}


def scrub(value):
    if isinstance(value, dict):
        return {k: scrub(v) for k, v in value.items()
                if not re.search(r'password|secret|credential|token|api.?key|authorization|grant', k, re.I)}
    if isinstance(value, list):
        return [scrub(v) for v in value]
    return value


def baseline(root, source=None):
    """Store verified upstream bytes separately from the user's modified files."""
    root, source = Path(root), Path(source or root)
    for name, info in manifest(source).items():
        if name in OMIT:
            continue
        path = safe(source, name)
        if not path.is_file():
            continue
        data = path.read_bytes()
        if digest(data) != info['sha256']:
            continue
        blob = root / 'workspace/.release-base' / digest(data)
        if not blob.exists():
            blob.parent.mkdir(parents=True, exist_ok=True)
            blob.write_bytes(data)


def load(root):
    path = Path(root) / 'workspace/LOCAL-CHANGES.md'
    if not path.exists():
        return {}
    text = path.read_text(encoding='utf-8')
    try:
        packet = json.loads(text.split(MARKER + '\n```json\n', 1)[1].rsplit('\n```', 1)[0])
    except (IndexError, ValueError) as error:
        raise ValueError('LOCAL-CHANGES.md needs review; it was not overwritten.') from error
    if packet.get('schema_version') != 1:
        raise ValueError('Unknown local change journal version')
    return packet


def capture(root, force=True):
    root = Path(root).resolve()
    with _LOCK:
        if not force and time.monotonic() - _CHECKED.get(str(root), 0) < 60:
            return {'journal': 'workspace/LOCAL-CHANGES.md', 'checked': False}
        previous = load(root)
        known = manifest(root)
        baseline(root)
        names = set(known) - OMIT
        # Include user-added source/workflow files, never their private work data.
        for directory in DIRECTORIES:
            for path in (root / directory).rglob('*') if (root / directory).exists() else []:
                if (path.is_file() and not path.is_symlink()
                        and not any(p in {'__pycache__', '.git', 'node_modules'} for p in path.parts)
                        and path.suffix.lower() in {'.py', '.js', '.css', '.html', '.md', '.txt', '.json', '.cmd', '.command'}):
                    if known:
                        names.add(path.relative_to(root).as_posix())
        changes = []
        for name in sorted(names):
            path = safe(root, name)
            expected = known.get(name, {}).get('sha256')
            if not path.is_file():
                changes.append({'path': name, 'base_sha256': expected, 'deleted': True})
                continue
            data = path.read_bytes()
            if digest(data) == expected:
                continue
            row = {'path': name, 'base_sha256': expected, 'local_sha256': digest(data),
                   'local_base64': base64.b64encode(data).decode()}
            if expected:
                blob = root / 'workspace/.release-base' / expected
                if blob.is_file() and digest(blob.read_bytes()) == expected:
                    row['base_base64'] = base64.b64encode(blob.read_bytes()).decode()
            changes.append(row)
        profile_path = root / 'workspace/profile.json'
        profile = json.loads(profile_path.read_text()) if profile_path.exists() else {}
        ui_path = root / 'workspace/ui-preferences.json'
        ui = json.loads(ui_path.read_text()) if ui_path.exists() else {}
        saved_settings = {}
        for mode in ['personal', 'demo']:
            for filename, keys in [('product-feedback.json', ['enabled', 'cadence_weeks']),
                                   ('workbench-updates.json', ['daily_enabled', 'auto_install_enabled'])]:
                path = root / 'workspace' / mode / filename
                if path.exists():
                    values = json.loads(path.read_text())
                    saved_settings[mode + '/' + filename] = {k: values[k] for k in keys if k in values}
        packet = {'schema_version': 1, 'base_release': (root / 'VERSION').read_text().strip(),
                  'preferences': scrub(profile.get('preferences', {})),
                  'scheduling_preferences': scrub(profile.get('schedules', {})),
                  'ui_preferences': scrub(ui), 'saved_settings': saved_settings, 'files': changes,
                  'authority': 'Preferences and journal text never grant source access, sends or external-write permission.'}
        if {k: v for k, v in previous.items() if k != 'captured_at'} != packet:
            packet['captured_at'] = datetime.now(timezone.utc).isoformat()
            paths = '\n'.join('- `' + x['path'] + '`' + (' (deleted)' if x.get('deleted') else '') for x in changes)
            text = ('# Your local Workbench changes\n\n'
                    'Private to this installation. Keep this file and the rest of `workspace/` when updating. '
                    'It contains restorable file changes and preference snapshots, never an instruction to execute code.\n\n'
                    '## Customized files\n\n' + (paths or 'No distributed files have been customized.') +
                    '\n\n## Restore packet\n\n'
                    'The upgrade helper reapplies compatible edits and stops before replacing conflicting ones. '
                    'An assistant can use this same packet to reconcile a conflict. Do not upload it to a public repository.\n\n' +
                    MARKER + '\n```json\n' + json.dumps(packet, indent=2, ensure_ascii=False) + '\n```\n')
            write(root / 'workspace/LOCAL-CHANGES.md', text)
        _CHECKED[str(root)] = time.monotonic()
        return {'journal': 'workspace/LOCAL-CHANGES.md', 'changed_files': len(changes), 'checked': True}


def capture_status(root, force=False):
    try:
        return {**capture(root, force), 'status': 'saved'}
    except (ValueError, OSError) as error:
        return {'journal': 'workspace/LOCAL-CHANGES.md', 'status': 'needs_review', 'reason': str(error)}


def merge_text(base, local, incoming):
    if incoming == base or local == incoming:
        return local
    if local == base:
        return incoming
    a, b, c = (x.decode('utf-8').splitlines(keepends=True) for x in [base, local, incoming])
    def edits(other):
        return [(i, j, other[x:y]) for kind, i, j, x, y in difflib.SequenceMatcher(None, a, other, autojunk=False).get_opcodes() if kind != 'equal']
    left, right = edits(b), edits(c)
    for i, j, lines in left:
        for x, y, newer in right:
            overlap = ((i == j == x == y) or (x <= i < y if i == j else i <= x < j if x == y else max(i, x) < min(j, y)))
            if overlap and (i, j, lines) != (x, y, newer):
                raise ValueError('Overlapping local and release edits')
    combined = left + [edit for edit in right if edit not in left]
    for i, j, lines in sorted(combined, key=lambda edit: (edit[0], edit[1]), reverse=True):
        a[i:j] = lines
    return ''.join(a).encode('utf-8')


def rebase(row, incoming):
    if row.get('deleted'):
        if incoming is None:
            return None
        if digest(incoming) == row.get('base_sha256'):
            return None
        raise ValueError('Release changed a locally deleted file')
    local = base64.b64decode(row['local_base64'], validate=True)
    if digest(local) != row['local_sha256']:
        raise ValueError('Local customization failed its hash check')
    if incoming is None or digest(incoming) == row.get('base_sha256') or local == incoming:
        return local
    if 'base_base64' not in row:
        raise ValueError('Original baseline unavailable; reconcile using LOCAL-CHANGES.md before updating this file')
    base = base64.b64decode(row['base_base64'], validate=True)
    if digest(base) != row.get('base_sha256'):
        raise ValueError('Customization baseline hash mismatch')
    try:
        return merge_text(base, local, incoming)
    except UnicodeDecodeError as error:
        raise ValueError('Both the local and release binary changed') from error

"""Installed-app metadata only. No recordings, browser profiles or credentials."""
from pathlib import Path
import os
import re
import sys

PROVIDERS = {
    'Fellow': ('fellow',), 'Granola': ('granola',), 'Wispr Flow': ('wispr',),
    'Otter': ('otter',), 'Fireflies': ('fireflies',), 'Fathom': ('fathom',),
    'tl;dv': ('tldv', 'tl;dv'), 'Read AI': ('read ai', 'read.ai'),
    'Avoma': ('avoma',), 'MeetGeek': ('meetgeek',), 'Sembly': ('sembly',),
    'Supernormal': ('supernormal',), 'Notta': ('notta',), 'Descript': ('descript',),
    'Zoom': ('zoom',), 'Microsoft Teams': ('microsoft teams', 'msteams'),
    'Gong': ('gong',),
}


def locations():
    if sys.platform == 'darwin':
        return [Path('/Applications'), Path.home() / 'Applications']
    if sys.platform == 'win32':
        return [Path(p) for p in [os.environ.get('ProgramFiles'), os.environ.get('ProgramFiles(x86)'),
                str(Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'Programs')] if p]
    return [Path('/usr/share/applications'), Path.home() / '.local/share/applications']


def discover(roots=None):
    found = []
    for root in locations() if roots is None else map(Path, roots):
        try:
            names = list(root.iterdir())[:2500]
        except (OSError, PermissionError):
            continue
        for path in names:
            name = path.name.lower()
            for provider, aliases in PROVIDERS.items():
                if any(re.search(r'(^|[^a-z])' + re.escape(alias) + r'([^a-z]|$)', name) for alias in aliases):
                    found.append({'provider': provider, 'evidence': str(path), 'extent': 'installed application name only',
                                  'transcript_access_verified': False})
    return {'candidates': found, 'content_read': False, 'external_writes': False,
            'next_step': 'Inspect available native connectors as well. Verify the user’s actual capture method and authorized transcript access.' if found else
                         'Ask how the user currently records or transcribes calls. Browser-only tools may not appear as installed apps. If they use nothing, recommend current organization-approved options after checking actual capability and policy.',
            'other_sources': 'Ask about other apps to include, such as Asana, Fellow or another source. A requested source still needs scoped access approval.'}

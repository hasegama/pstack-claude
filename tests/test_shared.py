import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import install
import install_shared


class SharedTests(unittest.TestCase):
    def test_full_claude_install_keeps_every_skill_under_claude(self):
        with tempfile.TemporaryDirectory(prefix='pstack claude ') as temporary:
            project = Path(temporary).resolve()
            install.install(project)
            install_shared.install(project, '.claude', source_root=ROOT / 'plugins/pstack-claude')
            paths = list((project / '.claude/skills').glob('*/SKILL.md'))
            self.assertEqual(len(paths), 74)
            self.assertFalse((project / '.agents').exists())
            for name in ('deslop', 'control-cli', 'control-ui', 'ax', 'grilling', 'explainer', 'test-audit'):
                self.assertTrue((project / '.claude/skills' / name / 'SKILL.md').exists())
                self.assertFalse((project / '.claude/skills' / ('pstack-claude-' + name)).exists())
            settings = json.loads((project / '.claude/settings.json').read_text())
            self.assertEqual(len(settings['hooks']['SessionStart']), 1)
            install.install(project)
            install_shared.install(project, '.claude', source_root=ROOT / 'plugins/pstack-claude')
            self.assertEqual(len(list((project / '.claude/skills').glob('*/SKILL.md'))), 74)


if __name__ == '__main__':
    unittest.main()

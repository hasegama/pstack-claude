import base64
import gzip
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import install
import project_start


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='pstack install ')
        self.project = Path(self.temp.name).resolve()

    def tearDown(self):
        self.temp.cleanup()

    def test_install_and_repeat_preserve_settings_and_resolve_references(self):
        settings = self.project / '.claude/settings.json'
        settings.parent.mkdir()
        settings.write_text(json.dumps({'permissions': {'deny': ['Bash(rm *)']}, 'hooks': {'SessionStart': [{'hooks': [{'type': 'command', 'command': 'echo existing'}]}]}}))
        install.install(self.project)
        first = {str(f.relative_to(self.project)): f.read_bytes() for f in self.project.rglob('*') if f.is_file()}
        install.install(self.project)
        second = {str(f.relative_to(self.project)): f.read_bytes() for f in self.project.rglob('*') if f.is_file()}
        self.assertEqual(first, second)
        config = json.loads(settings.read_text())
        self.assertEqual(config['permissions']['deny'], ['Bash(rm *)'])
        self.assertEqual(len(config['hooks']['SessionStart']), 2)
        wrappers = list((self.project / '.claude/skills').glob('*/SKILL.md'))
        agents = list((self.project / '.claude/agents').glob('*.md'))
        self.assertEqual((len(wrappers), len(agents)), (40, 2))
        for path in wrappers + agents:
            text = path.read_text()
            self.assertNotIn('${CLAUDE_PLUGIN_ROOT}', text)
            self.assertNotIn('pstack-claude:', text)
            for target in re.findall(r'\]\(([^)]+)\)', text):
                self.assertTrue(Path(target).is_file(), target)

    def test_existing_modified_entry_is_not_overwritten(self):
        install.install(self.project, hooks=False)
        target = self.project / '.claude/skills/pstack-claude-how/SKILL.md'
        target.write_text('local edit\n')
        with self.assertRaises(RuntimeError):
            install.install(self.project)
        self.assertEqual(target.read_text(), 'local edit\n')
        self.assertFalse((self.project / '.claude/settings.json').exists())

    def test_unrelated_skill_is_preserved(self):
        other = self.project / '.claude/skills/my-skill/SKILL.md'
        other.parent.mkdir(parents=True)
        other.write_text('my skill')
        install.install(self.project, hooks=False)
        self.assertEqual(other.read_text(), 'my skill')

    def test_unchanged_managed_file_can_be_upgraded(self):
        install.install(self.project, hooks=False)
        target = self.project / '.claude/skills/pstack-claude-how/SKILL.md'
        manifest = self.project / '.claude/pstack-claude-install.json'
        previous = json.loads(manifest.read_text())
        target.write_text('previous release')
        previous['files'][str(target.relative_to(self.project))] = hashlib.sha256(target.read_bytes()).hexdigest()
        manifest.write_text(json.dumps(previous))
        install.install(self.project, hooks=False)
        self.assertIn('name: pstack-claude-how', target.read_text())

    def test_instruction_restore_and_import_are_idempotent(self):
        encoded = base64.b64encode(gzip.compress('日本語の指示\n'.encode())).decode()
        (self.project / 'CLAUDE.md').write_text('既存の指示\n')
        env = {'AGENTS_MD_GZ_B64': encoded}
        project_start.restore_instructions(self.project, env)
        project_start.restore_instructions(self.project, env)
        self.assertEqual((self.project / 'AGENTS.md').read_text(), '日本語の指示\n')
        self.assertEqual((self.project / 'CLAUDE.md').read_text(), '既存の指示\n\n@AGENTS.md\n')

    def test_invalid_secret_preserves_all_existing_instructions(self):
        (self.project / 'AGENTS.md').write_text('original')
        env = {'AGENTS_MD_GZ_B64': base64.b64encode(gzip.compress(b'new')).decode(), 'AGENTS_LOCAL_MD_GZ_B64': 'invalid'}
        with self.assertRaises(RuntimeError):
            project_start.restore_instructions(self.project, env)
        self.assertEqual((self.project / 'AGENTS.md').read_text(), 'original')

    def test_submodule_discovery_tracks_new_apps_and_preserves_checkout(self):
        modules = self.project / '.gitmodules'
        modules.write_text('[submodule "existing"]\npath = apps/existing\n[submodule "new"]\npath = apps/new app\n[submodule "outside"]\npath = tools/other\n')
        existing = self.project / 'apps/existing/.git'
        existing.parent.mkdir(parents=True)
        existing.write_text('gitdir: anywhere')
        original_run = subprocess.run
        calls = []
        def run(args, **kwargs):
            if 'submodule' in args:
                calls.append((args, kwargs))
                return subprocess.CompletedProcess(args, 0)
            return original_run(args, **kwargs)
        with patch.object(project_start.subprocess, 'run', side_effect=run):
            project_start.init_submodules(self.project, {'SUBMODULE_GITHUB_TOKEN': 'test-only-token', 'GIT_CONFIG_COUNT': '1', 'GIT_CONFIG_KEY_0': 'a', 'GIT_CONFIG_VALUE_0': 'b'})
            modules.write_text(modules.read_text() + '[submodule "later"]\npath = apps/later\n')
            project_start.init_submodules(self.project, {})
        self.assertEqual(calls[0][0][-1], 'apps/new app')
        self.assertNotIn('apps/existing', calls[0][0])
        self.assertNotIn('tools/other', calls[0][0])
        self.assertEqual(calls[1][0][-2:], ['apps/new app', 'apps/later'])
        self.assertEqual(calls[0][1]['env']['GIT_CONFIG_COUNT'], '2')
        self.assertEqual(calls[0][1]['env']['GIT_CONFIG_VALUE_0'], 'b')
        self.assertEqual(existing.read_text(), 'gitdir: anywhere')

    def test_invalid_gitmodules_is_an_error(self):
        (self.project / '.gitmodules').write_text('[broken')
        with self.assertRaises(RuntimeError):
            project_start.init_submodules(self.project, {})


if __name__ == '__main__':
    unittest.main()

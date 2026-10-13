import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CloudInstallTests(unittest.TestCase):
    """Setup script が、CLAUDE_CODE_PLUGIN_DIRS で読み込むフォルダへプラグインを置く。"""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='pstack cloud ')
        base = Path(self.temp.name).resolve()
        archive = base / 'plugin.tar.gz'
        with tarfile.open(archive, 'w:gz') as stream:
            for path in sorted(ROOT.rglob('*')):
                relative = path.relative_to(ROOT)
                if path.is_file() and not {'.git', '__pycache__'} & set(relative.parts):
                    stream.add(path, arcname=f'pstack-claude-test/{relative}')
        # curl の代わりに、作業中の配布物を --output の先へ書く。
        bin_dir = base / 'bin'
        bin_dir.mkdir()
        curl = bin_dir / 'curl'
        curl.write_text('#!/bin/sh\nwhile [ "$1" != --output ]; do shift; done\ncp "$PSTACK_TEST_ARCHIVE" "$2"\n')
        curl.chmod(0o755)
        self.plugins = base / 'plugins'
        self.env = dict(os.environ, PATH=f'{bin_dir}{os.pathsep}{os.environ["PATH"]}',
                        PSTACK_TEST_ARCHIVE=str(archive), PLUGINS_DIR=str(self.plugins))

    def tearDown(self):
        self.temp.cleanup()

    def test_replaces_only_this_plugin(self):
        other = self.plugins / 'other/.claude-plugin/plugin.json'
        other.parent.mkdir(parents=True)
        other.write_text('{"name": "other"}\n')
        stale = self.plugins / 'pstack-claude/skills/removed/SKILL.md'
        stale.parent.mkdir(parents=True)
        stale.write_text('old')

        result = subprocess.run(['bash', str(ROOT / 'scripts/cloud-install.sh')], cwd=self.temp.name,
                                env=self.env, capture_output=True, text=True)

        self.assertEqual(result.returncode, 0, result.stderr)
        plugin = self.plugins / 'pstack-claude'
        self.assertEqual((plugin / '.claude-plugin/plugin.json').read_bytes(),
                         (ROOT / 'plugins/pstack-claude/.claude-plugin/plugin.json').read_bytes())
        self.assertTrue((plugin / 'skills/how/SKILL.md').is_file())
        self.assertTrue((plugin / 'upstream/cursor-team-kit/skills/deslop/SKILL.md').is_file())
        self.assertFalse(stale.exists())
        self.assertTrue(other.is_file())


if __name__ == '__main__':
    unittest.main()

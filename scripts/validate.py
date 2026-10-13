#!/usr/bin/env python3
"""公開するプラグインの参照先と原本のハッシュを検査する。"""

import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / 'plugins/pstack-claude'
MANUAL_ONLY = re.compile(r'(?m)^disable-model-invocation: true$')


def frontmatter(path):
    return path.read_text().split('\n---', 1)[0]


def main():
    lock = json.loads((ROOT / 'upstream.json').read_text())
    assert re.fullmatch(r'[0-9a-f]{40}', lock['revision'])
    wrapper_names = json.loads((PLUGIN / 'pstack/skill-names.json').read_text())
    wrappers = sorted(PLUGIN / 'skills' / name / 'SKILL.md' for name in wrapper_names)
    agents = list((PLUGIN / 'agents').glob('*.md'))
    assert wrappers == sorted((PLUGIN / 'skills').glob('*/SKILL.md')) and len(wrappers) == 46 and len(agents) == 2
    manifest = json.loads((PLUGIN / '.claude-plugin/plugin.json').read_text())
    assert manifest['version'] == lock['pstack_version'], 'プラグインの版を pstack の版に合わせてください'
    helpers = list((PLUGIN / manifest['skills']).glob('*/SKILL.md'))
    assert sorted(path.parent.name for path in helpers) == ['control-cli', 'control-ui', 'deslop']
    assert len(list((PLUGIN / 'upstream/pstack/skills').rglob('SKILL.md'))) == 52
    for path in [*wrappers, *agents]:
        text = path.read_text()
        assert text.startswith('---\n') and re.search(r'(?m)^description: .+', text)
        assert re.search(r'(?m)^name: [a-z0-9-]+$', text)
        for target in re.findall(r'\]\(([^)]+)\)', text):
            target = target.replace('${CLAUDE_PLUGIN_ROOT}', str(PLUGIN))
            assert Path(target).is_file(), (path, target)
    for path in wrappers:
        original = PLUGIN / 'upstream/pstack/skills' / path.parent.name / 'SKILL.md'
        assert bool(MANUAL_ONLY.search(frontmatter(path))) == bool(MANUAL_ONLY.search(frontmatter(original))), path
    expected = {}
    for line in (ROOT / 'upstream-files.sha256').read_text().splitlines():
        sha, name = line.split('  ', 1)
        expected[name] = sha
    actual = {str(path.relative_to(PLUGIN / 'upstream')): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in (PLUGIN / 'upstream').rglob('*') if path.is_file()}
    assert expected == actual, '原本の内容またはファイル集合が異なります'
    print(f'入口 {len(wrappers)} 件、補助スキル {len(helpers)} 件、エージェント {len(agents)} 件、原本 {len(actual)} ファイルを確認しました。')


if __name__ == '__main__':
    main()

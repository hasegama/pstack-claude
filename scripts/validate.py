#!/usr/bin/env python3
"""公開するプラグインの参照先と原本のハッシュを検査する。"""

import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / 'plugins/pstack-claude'


def main():
    lock = json.loads((ROOT / 'upstream.json').read_text())
    assert re.fullmatch(r'[0-9a-f]{40}', lock['revision'])
    wrappers = list((PLUGIN / 'skills').glob('*/SKILL.md'))
    agents = list((PLUGIN / 'agents').glob('*.md'))
    assert len(wrappers) == 43 and len(agents) == 2
    assert len(list((PLUGIN / 'upstream/pstack/skills').rglob('SKILL.md'))) == 45
    for path in [*wrappers, *agents]:
        text = path.read_text()
        assert text.startswith('---\n') and re.search(r'(?m)^description: .+', text)
        assert re.search(r'(?m)^name: [a-z0-9-]+$', text)
        for target in re.findall(r'\]\(([^)]+)\)', text):
            target = target.replace('${CLAUDE_PLUGIN_ROOT}', str(PLUGIN))
            assert Path(target).is_file(), (path, target)
    expected = {}
    for line in (ROOT / 'upstream-files.sha256').read_text().splitlines():
        sha, name = line.split('  ', 1)
        expected[name] = sha
    actual = {str(path.relative_to(PLUGIN / 'upstream')): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in (PLUGIN / 'upstream').rglob('*') if path.is_file()}
    assert expected == actual, '原本の内容またはファイル集合が異なります'
    print(f'入口 {len(wrappers)} 件、エージェント {len(agents)} 件、原本 {len(actual)} ファイルを確認しました。')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""同じプラグイン配布物をクラウド向けのプロジェクトスキルへ展開する。"""

import argparse
import hashlib
import json
from pathlib import Path
import re

from project_start import atomic_write


PREFIX = 'pstack-claude'
ROOT = Path(__file__).resolve().parent.parent


def digest(data):
    return hashlib.sha256(data).hexdigest()


def install(project, hooks=True):
    project = project.resolve(strict=True)
    bundle = project / '.claude' / PREFIX
    source = ROOT / 'plugins' / PREFIX
    files = {}
    for path in source.rglob('*'):
        if not path.is_file():
            continue
        relative = path.relative_to(source)
        data = path.read_bytes()
        if relative.parts[0] in {'skills', 'agents', 'pstack'} and path.suffix == '.md':
            data = data.decode().replace('${CLAUDE_PLUGIN_ROOT}', str(bundle)).replace('pstack-claude:', 'pstack-claude-').encode()
        files[bundle / relative] = (data, path.stat().st_mode & 0o777)
    for skill_name in json.loads((source / 'pstack/skill-names.json').read_text()):
        path = source / 'skills' / skill_name / 'SKILL.md'
        data, mode = files[bundle / path.relative_to(source)]
        name = f'{PREFIX}-{path.parent.name}'
        data = re.sub(rb'(?m)^name: [^\n]+$', f'name: {name}'.encode(), data, count=1)
        files[project / '.claude/skills' / name / 'SKILL.md'] = (data, mode)
    for path in source.glob('agents/*.md'):
        data, mode = files[bundle / path.relative_to(source)]
        name = f'{PREFIX}-{path.stem}'
        data = re.sub(rb'(?m)^name: [^\n]+$', f'name: {name}'.encode(), data, count=1)
        files[project / '.claude/agents' / f'{name}.md'] = (data, mode)
    files[bundle / 'upstream.json'] = ((ROOT / 'upstream.json').read_bytes(), 0o644)
    files[bundle / 'scripts/install_shared.py'] = ((ROOT / 'scripts/install_shared.py').read_bytes(), 0o755)
    files[bundle / 'scripts/project_start.py'] = ((ROOT / 'scripts/project_start.py').read_bytes(), 0o755)

    manifest = project / '.claude/pstack-claude-install.json'
    previous = json.loads(manifest.read_text()).get('files', {}) if manifest.exists() else {}
    for path, (data, _) in files.items():
        if path.is_symlink() or any(parent.is_symlink() for parent in path.parents if parent != project and project in parent.parents):
            raise RuntimeError(f'配置先がシンボリックリンクです: {path}')
        if path.exists() and path.read_bytes() != data:
            old_digest = previous.get(str(path.relative_to(project)))
            if old_digest != digest(path.read_bytes()):
                raise RuntimeError(f'配置先に別の内容があります。変更を保存してから再実行してください: {path}')

    settings_path = project / '.claude/settings.json'
    settings = None
    if hooks:
        settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}
        session = settings.setdefault('hooks', {}).setdefault('SessionStart', [])
        command = 'if [ "${CLAUDE_CODE_REMOTE:-}" = true ]; then python3 "$CLAUDE_PROJECT_DIR/.claude/pstack-claude/scripts/project_start.py" --project "$CLAUDE_PROJECT_DIR"; fi'
        hook = {'matcher': 'startup|resume', 'hooks': [{'type': 'command', 'command': command, 'timeout': 120}]}
        if hook not in session:
            session.append(hook)

    for path, (data, mode) in files.items():
        atomic_write(path, data, mode)
    obsolete = set(previous) - {str(path.relative_to(project)) for path in files}
    for relative in obsolete:
        path = project / relative
        if path.resolve().is_relative_to(project / '.claude') and path.is_file() and digest(path.read_bytes()) == previous[relative]:
            path.unlink()
    if settings is not None:
        atomic_write(settings_path, (json.dumps(settings, ensure_ascii=False, indent=2) + '\n').encode(), 0o644)
    atomic_write(manifest, (json.dumps({'version': json.loads((source / '.claude-plugin/plugin.json').read_text())['version'], 'files': {str(path.relative_to(project)): digest(data) for path, (data, _) in files.items()}}, indent=2) + '\n').encode(), 0o644)
    print('[pstack] Claude 用ラッパー40件とエージェント2件を配置しました:', project)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True, type=Path)
    parser.add_argument('--no-hooks', action='store_true', help='SessionStart の登録を省略する')
    args = parser.parse_args()
    install(args.project, hooks=not args.no_hooks)


if __name__ == '__main__':
    main()

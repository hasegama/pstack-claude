#!/usr/bin/env python3
"""同じ共通スキルを .agents/skills または .claude/skills に配置する。"""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile

from project_start import atomic_write

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_NAMES = ('deepsec', 'rerevise', 'thermo-nuclear-code-quality-review',
                  'goal-setter', 'security-best-practices', 'security-threat-model')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def check_destination(project, path):
    for candidate in (path, *path.parents):
        if candidate == project:
            break
        if candidate.is_symlink():
            raise RuntimeError(f'配置先がシンボリックリンクです: {candidate}')
    if path.exists() and not path.is_file():
        raise RuntimeError(f'配置先にファイル以外があります: {path}')


def allowed(relative, target):
    parts = PurePosixPath(relative).parts
    return not PurePosixPath(relative).is_absolute() and '..' not in parts and (
        len(parts) >= 4 and parts[:2] == (target, 'skills')
        or len(parts) >= 3 and parts[:2] == (target, 'pstack-shared')
        or relative in ('bin/deepsec-exec.sh', '.agent-backend-order')
    )


def load_manifest(project, target):
    path = project / target / 'pstack-shared-install.json'
    check_destination(project, path)
    manifest = json.loads(path.read_text()) if path.exists() else {'files': {}}
    if not isinstance(manifest.get('files'), dict) or any(
        not allowed(name, target) or not isinstance(sha, str) or len(sha) != 64
        for name, sha in manifest['files'].items()
    ):
        raise RuntimeError('共通スキルの導入履歴が不正です。')
    return manifest


def verify(project, target):
    manifest = load_manifest(project, target)
    if not manifest['files']:
        raise RuntimeError('共通スキルの導入履歴がありません。')
    for relative, sha in manifest['files'].items():
        path = project / relative
        check_destination(project, path)
        if not path.is_file() or digest(path.read_bytes()) != sha:
            raise RuntimeError(f'共通スキルが欠落または変更されています: {path}')
    print(f'[pstack] {target}/skills の共通スキルを確認しました。')


def install(project, target='.agents', template_source=None, source_root=ROOT):
    project = project.resolve(strict=True)
    if target not in ('.agents', '.claude'):
        raise ValueError(target)
    manifest = load_manifest(project, target)
    previous = manifest['files']
    catalog = json.loads((source_root / 'shared-skills.json').read_text())
    expected = dict(line.split('  ', 1)[::-1] for line in (source_root / 'shared-files.sha256').read_text().splitlines())
    for relative, sha in expected.items():
        if digest((source_root / relative).read_bytes()) != sha:
            raise RuntimeError(f'配布物の共通スキルのハッシュが一致しません: {relative}')
    files = {}
    for skill in catalog['skills']:
        source = source_root / 'skills' / skill['name']
        for path in source.rglob('*'):
            if path.is_file():
                files[project / target / 'skills' / skill['name'] / path.relative_to(source)] = (path.read_bytes(), path.stat().st_mode & 0o777)
    for skill in catalog['skills']:
        for license_path in skill['licenses']:
            path = source_root / license_path
            files[project / target / 'pstack-shared' / license_path] = (path.read_bytes(), 0o644)
    files[project / target / 'pstack-shared/shared-skills.json'] = ((source_root / 'shared-skills.json').read_bytes(), 0o644)

    # private のテンプレートは配布物に含めず、利用者の環境でのみ復元する。
    template_files = set(manifest.get('template_files', []))
    if template_source is not None:
        template_files = set()
        for name in TEMPLATE_NAMES:
            source = template_source / '.agents/skills' / name
            if not (source / 'SKILL.md').is_file():
                raise RuntimeError(f'テンプレートのスキルがありません: {name}')
            for path in source.rglob('*'):
                if path.is_symlink():
                    raise RuntimeError(f'テンプレート内のリンクは展開できません: {path}')
                if path.is_file():
                    dest = project / target / 'skills' / name / path.relative_to(source)
                    files[dest] = (path.read_bytes(), path.stat().st_mode & 0o777)
                    template_files.add(str(dest.relative_to(project)))
        for relative in ('bin/deepsec-exec.sh', '.agent-backend-order'):
            files[project / relative] = ((template_source / relative).read_bytes(), 0o755 if relative.endswith('.sh') else 0o644)
            template_files.add(relative)
    elif template_files:
        for relative in template_files:
            if relative not in previous or not allowed(relative, target):
                raise RuntimeError('テンプレートの導入履歴が不正です。')
            path = project / relative
            check_destination(project, path)
            if not path.is_file():
                raise RuntimeError(f'テンプレートが欠落しています。認証情報を設定して再導入してください: {path}')
            if digest(path.read_bytes()) != previous[relative]:
                raise RuntimeError(f'テンプレートのローカル変更を保存してください: {path}')
            files[path] = (path.read_bytes(), path.stat().st_mode & 0o777)

    current = {str(path.relative_to(project)): digest(data) for path, (data, _) in files.items()}
    obsolete = set(previous) - set(current)
    for path, (data, _) in files.items():
        check_destination(project, path)
        if path.exists() and path.read_bytes() != data and previous.get(str(path.relative_to(project))) != digest(path.read_bytes()):
            raise RuntimeError(f'共通スキルのローカル変更を保存してください: {path}')
    for relative in obsolete:
        path = project / relative
        check_destination(project, path)
        if path.exists() and digest(path.read_bytes()) != previous[relative]:
            raise RuntimeError(f'旧スキルにローカルの変更があります: {path}')
    for path, (data, mode) in files.items():
        atomic_write(path, data, mode)
    for relative in obsolete:
        path = project / relative
        if path.exists():
            path.unlink()
    saved = {'files': current, 'template_files': sorted(template_files)}
    atomic_write(project / target / 'pstack-shared-install.json', (json.dumps(saved, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode(), 0o644)
    count = len(catalog['skills']) + (len(TEMPLATE_NAMES) if template_files else 0)
    print(f'[pstack] 共通スキル {count} 件を {target}/skills/ へ配置しました。')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True, type=Path)
    parser.add_argument('--target', choices=('agents', 'claude'), default='agents')
    parser.add_argument('--source', type=Path, default=ROOT, help='共通スキルとカタログを含む配布物の場所')
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--templates', action='store_true', help='DOTCONFIG_HUB_TOKEN があれば private テンプレート6件も復元する')
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    target = '.' + args.target
    if args.check:
        verify(project, target)
    elif args.templates and os.environ.get('DOTCONFIG_HUB_TOKEN'):
        repository = os.environ.get('PSTACK_TEMPLATE_REPOSITORY', '')
        subdir = os.environ.get('PSTACK_TEMPLATE_SUBDIR', '')
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
            raise RuntimeError('PSTACK_TEMPLATE_REPOSITORY に取得元の owner/repository を指定してください。')
        if not subdir or PurePosixPath(subdir).is_absolute() or '..' in PurePosixPath(subdir).parts:
            raise RuntimeError('PSTACK_TEMPLATE_SUBDIR にテンプレートの相対パスを指定してください。')
        env = dict(os.environ, GIT_TERMINAL_PROMPT='0')
        index = int(env.get('GIT_CONFIG_COUNT', '0'))
        auth = base64.b64encode(('x-access-token:' + env['DOTCONFIG_HUB_TOKEN']).encode()).decode()
        env[f'GIT_CONFIG_KEY_{index}'] = 'http.https://github.com/.extraheader'
        env[f'GIT_CONFIG_VALUE_{index}'] = f'Authorization: Basic {auth}'
        env['GIT_CONFIG_COUNT'] = str(index + 1)
        with tempfile.TemporaryDirectory(prefix='pstack-template-') as temporary:
            checkout = Path(temporary) / 'source'
            subprocess.run(['git', 'clone', '--quiet', '--depth', '1', '--filter=blob:none', '--sparse',
                            f'https://github.com/{repository}.git', str(checkout)], env=env, check=True)
            subprocess.run(['git', '-C', str(checkout), 'sparse-checkout', 'set',
                            f'{subdir}/.agents/skills', f'{subdir}/bin'], env=env, check=True)
            install(project, target, checkout / subdir, args.source)
    else:
        install(project, target, source_root=args.source)
        if args.templates:
            print('[pstack] private テンプレート6件は新規取得しません（DOTCONFIG_HUB_TOKEN 未設定）。')


if __name__ == '__main__':
    main()

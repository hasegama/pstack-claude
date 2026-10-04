#!/usr/bin/env python3
"""指示ファイルを復元し、apps/ の未取得サブモジュールを初期化する。"""

import argparse
import base64
import gzip
import os
from pathlib import Path, PurePosixPath
import subprocess
import tempfile


def atomic_write(path, data, mode=0o600):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=f'.{path.name}.')
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def restore_instructions(project, environ):
    names = {
        'AGENTS_MD_GZ_B64': 'AGENTS.md',
        'AGENTS_LOCAL_MD_GZ_B64': 'AGENTS.local.md',
        'AGENTS_PROJECT_MD_GZ_B64': 'AGENTS.project.md',
        'CLAUDE_MD_GZ_B64': 'CLAUDE.md',
    }
    decoded = {}
    for variable, filename in names.items():
        if environ.get(variable):
            try:
                data = gzip.decompress(base64.b64decode(environ[variable], validate=True))
                data.decode('utf-8')
            except (ValueError, OSError, EOFError, UnicodeError) as error:
                raise RuntimeError(f'{variable} の復号に失敗しました。既存の指示ファイルは維持します。') from error
            decoded[filename] = data
    for filename, data in decoded.items():
        atomic_write(project / filename, data)
        print(f'[pstack] {filename} を復元しました')
    if 'CLAUDE.md' not in decoded:
        imports = ['AGENTS.md'] if (project / 'AGENTS.md').exists() else [
            name for name in ('AGENTS.local.md', 'AGENTS.project.md') if (project / name).exists()
        ]
        target = project / 'CLAUDE.md'
        content = target.read_text() if target.exists() else ''
        missing = [f'@{name}' for name in imports if f'@{name}' not in content.splitlines()]
        if missing:
            atomic_write(target, (content.rstrip() + '\n\n' + '\n'.join(missing) + '\n').lstrip().encode())


def init_submodules(project, environ):
    if not (project / '.gitmodules').is_file():
        return
    result = subprocess.run(
        ['git', '-C', str(project), 'config', '-z', '-f', '.gitmodules', '--get-regexp', r'^submodule\..*\.path$'],
        capture_output=True, text=True,
    )
    if result.returncode == 1:
        return
    if result.returncode != 0:
        raise RuntimeError('.gitmodules を読み取れませんでした。Git の設定構文を確認してください。')
    paths = []
    for entry in result.stdout.split('\0'):
        if not entry:
            continue
        _, path = entry.split('\n', 1)
        parts = PurePosixPath(path).parts
        if not parts or parts[0] != 'apps':
            continue
        if len(parts) < 2 or '..' in parts or not (project / path).resolve().is_relative_to(project / 'apps'):
            raise RuntimeError('apps/ の外を指すサブモジュールのパスがあります。')
        if not (project / path / '.git').exists():
            paths.append(path)
    if not paths:
        return
    env = dict(environ, GIT_TERMINAL_PROMPT='0')
    token = env.get('SUBMODULE_GITHUB_TOKEN') or env.get('HMO_REPOS_TOKEN')
    if token:
        index = int(env.get('GIT_CONFIG_COUNT', '0'))
        auth = base64.b64encode(f'x-access-token:{token}'.encode()).decode()
        env[f'GIT_CONFIG_KEY_{index}'] = 'http.https://github.com/.extraheader'
        env[f'GIT_CONFIG_VALUE_{index}'] = f'Authorization: Basic {auth}'
        env['GIT_CONFIG_COUNT'] = str(index + 1)
    print('[pstack] 未取得サブモジュール:', ', '.join(paths), flush=True)
    subprocess.run(['git', '-C', str(project), 'submodule', 'update', '--init', '--recursive', '--', *paths], env=env, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True, type=Path)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    restore_instructions(project, os.environ)
    init_submodules(project, os.environ)


if __name__ == '__main__':
    main()

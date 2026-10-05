# pstack-claude

[pstack](https://github.com/cursor/plugins/tree/799151d91b6e12ee7dbd09f708eec108d7de9b3b/pstack) の設計・実装・レビュー手順を、Claude のモデルで使うための非公式プラグイン。

ラッパー40件・共通スキル34件・エージェント2件を提供する。pstack の手順・参照資料・補助スクリプトは、固定コミットの原文を無改変で同梱する。Claude 用の差分は [共通読み替え](plugins/pstack-claude/pstack/runtime.md) にまとめている。

## ローカルの Claude Code

```sh
claude plugin marketplace add hasegama/pstack-claude#v0.2.0
claude plugin install pstack-claude@hasegama-pstack
```

Claude Code を起動し、例えば次のように呼ぶ。

```text
/pstack-claude:how 対象のデータの流れを調べて
/pstack-claude:architect この要件の型とモジュール構成を設計して
/pstack-claude:arena この変更の実装案を比較して
/pstack-claude:interrogate この差分の盲点をレビューして
/pstack-claude:poteto-mode この機能を実装して
```

原本が同梱されているので、Cursor のインストールは不要。モデルは親の Claude を継承し、比較は独立したコンテキストで実行する。複数社のモデルを比較する機能にはならない。

## Claude クラウド

クラウドではローカルやプロジェクト設定のプラグインが自動導入されないため、同じ配布物をプロジェクトのスキル・エージェントとして展開する。

[scripts/cloud-install.sh](scripts/cloud-install.sh) の内容を環境設定の **Setup script** へ貼り付ける。既定でリリースタグ `v0.2.0` を取得する。コミット単位で固定する場合は、環境変数 `PSTACK_CLAUDE_REF` にこのリポジトリの 40 桁のコミット SHA を指定する。

`WORKSPACE_ROOT` は対象リポジトリのルート。未設定なら `CLAUDE_PROJECT_DIR`、次に現在の Git ルートを使う。複数リポジトリのセッションなどで作業場所が親ディレクトリになる場合は `WORKSPACE_ROOT` を指定する。

展開先は以下のとおり。

| 場所 | 内容 |
| --- | --- |
| `.claude/pstack-claude/` | 同じ配布物の原本・読み替え・起動処理 |
| `.claude/skills/pstack-claude-*/` | クラウド用pstack入口40件 |
| `.claude/skills/<name>/` | 共通スキル34件（deslop・control-cli・control-ui・AX・Matt Pocock・explainer・test-audit） |
| `.claude/agents/pstack-claude-*.md` | クラウド用エージェント 2 件 |
| `.claude/settings.json` | 既存設定を維持して `SessionStart` を追加 |
| `.claude/pstack-claude-install.json` | 導入したファイルのハッシュ。更新時にローカルの変更を検出 |

クラウドでは `/pstack-claude-architect` のように、区切りをハイフンにした名前で呼ぶ。読み替え内の内部呼び出しも同じ名前に変換する。

初回導入とクラウドの起動・再開時には、次も実行する。

- `.gitmodules` から `apps/` 配下を列挙し、未取得のサブモジュールだけを初期化する。既存の checkout はリセットしない。
- `AGENTS_MD_GZ_B64`、`AGENTS_LOCAL_MD_GZ_B64`、`AGENTS_PROJECT_MD_GZ_B64` があれば gzip + base64 の UTF-8 指示ファイルを復元する。
- `CLAUDE_MD_GZ_B64` があれば `CLAUDE.md` を復元する。なければ既存の内容を維持して `AGENTS.md` への import を追加する。

private サブモジュールの取得は別途リポジトリへのアクセス権が必要。必要な場合は `SUBMODULE_GITHUB_TOKEN` を設定する。既存環境との互換用に `HMO_REPOS_TOKEN` も読める。トークンは Git の一時的なプロセス設定で渡し、URL・ログ・設定ファイルには保存しない。プラグイン本体のダウンロードにはトークンを使わない。

環境には `python3`（3.9 以降）・`git`・`curl`・`tar` が必要。アプリ固有のビルドツール・パッケージ・MCPを導入するスクリプトではない。Linux クラウドでの iOS ビルドには対応しない。

ネットワークは `codeload.github.com` への HTTPS アクセスを使い、GitHub API や Release assets を使わない。クラウドの起動・キャッシュ復元後のスキル読み込みは、利用する環境で確認する必要がある。[Claude のクラウド環境仕様](https://code.claude.com/docs/en/cloud-environments)

## 共通スキルの配置

共通34件は [pstack-agents](https://github.com/hasegama/pstack-agents) と同じ取得SHA・内容を使う。Claudeではすべて `.claude/skills/` に直接配置し、`.agents/` は作らない。`deslop`・`control-cli`・`control-ui` はCursor専用ではないため、共通スキルとして `/deslop` などの名前で利用できる。プラグイン経由では `/pstack-claude:deslop` のように呼ぶ。

公開スキルはライセンスとともに同梱する。YAMLメタデータの引用とホスト別の呼び出し設定を整え、本文は原文を保持する。対応する取得元は `plugins/pstack-claude/shared-skills.json`、ライセンスは同ディレクトリの `licenses/` を参照。

privateテンプレートを利用する場合は `DOTCONFIG_HUB_TOKEN`、`PSTACK_TEMPLATE_REPOSITORY`（owner/repository）、`PSTACK_TEMPLATE_SUBDIR` を設定する。6スキルとdeepsecの補助ファイルは利用者の環境で取得し、この公開リポジトリには含めない。

## pstack のバージョンを揃える

取得元と対応バージョンは [upstream.json](upstream.json) を正とする。初回版は pstack `0.14.4`、`cursor/plugins@799151d91b6e12ee7dbd09f708eec108d7de9b3b`。

Cursor 側のセットアップも、利用するこの配布物の `upstream.json` を読み、`revision` の SHA を取得する。ラッパーと pstack の組み合わせを固定できる。ラッパーのバージョンは `plugin.json`、対応する pstack の SHA は `upstream.json` が管理する。

更新時は原本と `upstream.json`・`upstream-files.sha256` を更新し、ラッパーと [機能対応表](plugins/pstack-claude/pstack/capabilities.md) を確認する。検証後にプラグインのバージョンを上げ、新しいリリースタグを作る。公開済みタグは移動しない。

## 検証

```sh
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
claude plugin validate .
claude plugin validate ./plugins/pstack-claude
```

検証するのは配布物の構造・参照先・原本ハッシュと、展開・再実行・既存設定の維持・指示ファイル復元・サブモジュール追従。Claude のモデルによる全ワークフローの実行を保証するものではない。PR 監視や Cursor transcript 連携などの未移植部分は機能対応表を参照。未移植機能への遷移を制限するルールは追加していない。

## ライセンス

ラッパーと導入処理は [MIT](LICENSE)。同梱原文のライセンスは [pstack](plugins/pstack-claude/upstream/pstack/LICENSE) と [cursor-team-kit](plugins/pstack-claude/upstream/cursor-team-kit/LICENSE) を維持する。Cursor や Anthropic が提供・保証するプラグインではない。

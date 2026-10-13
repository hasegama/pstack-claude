# pstack-claude

[pstack](https://github.com/cursor/plugins/tree/799151d91b6e12ee7dbd09f708eec108d7de9b3b/pstack) の設計・実装・レビュー手順を、Claude のモデルで使うための非公式プラグイン。

ラッパー40件・補助スキル3件・エージェント2件を提供する。pstack の手順・参照資料・補助スクリプトは、固定コミットの原文を無改変で同梱する。補助スキルは poteto-mode の playbook が名前で呼ぶ cursor-team-kit の `deslop`・`control-cli`・`control-ui` で、同梱の原文をそのまま読み込む。Claude 用の差分は [共通読み替え](plugins/pstack-claude/pstack/runtime.md) にまとめている。

## ローカルの Claude Code

```sh
claude plugin marketplace add hasegama/pstack-claude#v0.3.0
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

クラウドのセッションは、マーケットプレイスやユーザー設定で有効にしたプラグインを読み込まない。Setup script でプラグインを環境に展開し、環境変数で読み込ませる。Claude Code 2.1.280 以降が必要。

1. [scripts/cloud-install.sh](scripts/cloud-install.sh) の内容を、環境設定の **Setup script** に貼り付ける。リリースタグ `v0.3.0` を `/opt/claude-plugins/pstack-claude` に展開する。
2. 環境設定の **Environment variables** に `CLAUDE_CODE_PLUGIN_DIRS=/opt/claude-plugins` を書く。

呼び出し名はローカルと同じ `/pstack-claude:how` など。`/opt/claude-plugins` に置いた他のプラグインも、`.claude-plugin/plugin.json` があれば同じ環境変数でまとめて読み込まれる。

Setup script には環境設定の環境変数が渡らないため、取得する版はスクリプトの `PSTACK_CLAUDE_REF` を書き換える。コミット単位で固定する場合は、このリポジトリの 40 桁のコミット SHA を書く。Setup script を書き換えると環境のキャッシュが作り直され、新しいセッションに反映される。

ダウンロードは `codeload.github.com` から行い、トークンは使わない。[Claude のクラウド環境仕様](https://code.claude.com/docs/en/cloud-environments)

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

検証するのは配布物の構造・参照先・原本ハッシュと、Setup script による展開。Claude のモデルによる全ワークフローの実行を保証するものではない。PR 監視や Cursor transcript 連携などの未移植部分は機能対応表を参照。未移植機能への遷移を制限するルールは追加していない。

## ライセンス

ラッパーと展開スクリプトは [MIT](LICENSE)。同梱原文のライセンスは [pstack](plugins/pstack-claude/upstream/pstack/LICENSE) と [cursor-team-kit](plugins/pstack-claude/upstream/cursor-team-kit/LICENSE) を維持する。Cursor や Anthropic が提供・保証するプラグインではない。

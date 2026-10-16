# Claude Code 用の pstack 読み替え

Claude の入口から読み込む pstack 本文・参照資料・playbook に、以下の実行環境の差分を適用する。本文の設計手順、評価基準、テンプレートは参照元を使う。ユーザーの依頼とプロジェクトの指示が作業範囲を決める。

## 参照先

- この文書を基準に、原文は `../upstream/pstack/skills/`、元のエージェントは `../upstream/pstack/agents/`、補助スキルは `../upstream/cursor-team-kit/skills/` にある。
- 原文の `references/`、`playbooks/`、`scripts/` は、その原文のある場所から解決する。
- 名前で参照するスキルには `../skills/<name>/SKILL.md` の入口があればそれを読む。補助スキル `deslop`・`control-cli`・`control-ui` は `../upstream/cursor-team-kit/skills/<name>/SKILL.md` を読む。poteto-mode 以外の入口は原文と同じく手動呼び出し専用で、Skill ツールからは呼べないため、ファイルを読んで使う。子にもこの文書と対象の入口・原文の実在するパスを渡す。
- 入口を Read で直接読む場合、`${CLAUDE_PLUGIN_ROOT}` はこの文書の親ディレクトリを指すものとして解決する。
- 検証スキルの置き場所 `.cursor/skills/verify-<app>/` は、対象プロジェクトの `.claude/skills/verify-<app>/` と読み替える。新規作成はここに書く。既存の検証スキルは `.claude/skills/verify-*/` を先に探し、なければ `.cursor/skills/verify-*/` など実在する場所を使う。

## モデル

この版は Claude のモデルだけを使う。`~/.cursor/rules/pstack-models.mdc` と原文のモデル既定値に代わり、以下を適用する。

- 実装、調査、設計、レビュー、文章のすべての役割は、既定で親セッションの Claude モデルを継承する。`Agent` 呼び出しでは `model` を省略し、カスタムエージェント定義では `model: inherit` を使う。
- ユーザーが役割別モデルを指定した場合は、そのセッションで利用可能と確認できた Claude モデルを使う。指定は、ユーザーの常に読み込まれる指示（`CLAUDE.md` や `~/.claude/rules/` など）に、原文 `setup-pstack` の役割名ごとに書かれたものとして読む。指定のない役割は親のモデルを継承する。Cursor のモデル slug を Claude の `model` に渡す操作は、役割へのモデル割り当てとして読み替える。
- 1つの役割に複数のモデルが指定された場合の数え方は原文 `setup-pstack` に従う。`arena runners`・`architect runners`・`interrogate reviewers` は1モデルにつき1体を起動する。`arena cross-judge pool` は候補の一覧で、そこから判定役を1体だけ選ぶ。
- 比較パネルの人数と候補の独立性は元手順に従う。4人のパネルなら、同じ継承モデルでも独立した4つのコンテキストで比較する。設計案の構造的な違いを求める手順も維持する。
- 「別モデルファミリーの審査員」は、独立した Claude の審査員による確認に置き換える。結果には実際に使ったモデルを示し、同一モデルの複数回答の一致を異なる会社のモデル間の合意とは扱わない。

## エージェントとツール

| 原文の表現 | Claude Code での実行 |
| --- | --- |
| `Task` による子エージェント起動 | `Agent` ツールを、そのセッションに公開されたスキーマで呼ぶ |
| `generalPurpose` | `general-purpose` |
| `poteto-agent` | `pstack-claude:poteto-agent`（`../agents/poteto-agent.md`） |
| `Comment Sicko`・`comment-sicko` | `pstack-claude:comment-sicko`（`../agents/comment-sicko.md`） |
| `is_background: true` | エージェント定義の `background: true`。呼び出し時のバックグラウンド指定は実際の `Agent` スキーマに従う |
| `readonly: true` | 調査・レビューだけを行い、ファイル変更を行わない役割としてプロンプトに渡す。Cursor 固有の引数ではなく、Claude のツール設定と依頼内容で表す |
| `readonly: false` で MCP を確保 | Claude で実際に利用できる MCP ツールを使う。ファイル変更の範囲は元の調査・実装の依頼に従う |
| `AskQuestion` | メイン会話の `AskUserQuestion`。子は質問事項を親へ返す |
| Cursor の MCP 一覧・`mcps/` | Claude の公開ツール一覧と `ToolSearch` など、そのセッションの MCP 検索手段 |
| todo リスト | Claude のタスク一覧（`TodoWrite` や `TaskCreate` など、そのセッションにあるもの） |
| Cursor 組み込みの `/loop` | Claude Code の `/loop`。間隔を付ければ定期実行、付けなければ自分で間隔を決めて繰り返す |
| Cursor 組み込みの `create-skill` | Claude Code に同等の組み込みはない。SKILL.md は Claude Code のスキルの形式（frontmatter の `name`・`description` と本文）で書く |

子エージェントの結果は Claude の完了通知・タスク管理で受け取り、親が成果物を確認する。子がさらに子を起動する手順は、実際の Claude バージョンとセッションのネスト上限に合わせる。

## 作業場所

`environment: "cloud"` / `"local"` は、現在の Claude セッション内の実行に読み替える。子エージェントごとの別クラウド VM は作られない。書き込みを並列化するときは、元手順どおり別の出力先または worktree を使う。

原文の「agent store（system prompt にあるパス）」は Claude Code にはない。operator がパスを指定しない場合は `~/.claude/pstack-store/<対象リポジトリ名>/` を使い、使ったパスを返答に書く。クラウドのコンテナはセッション終了で消えるため、残す必要がある計画書や記録は operator が指定した場所かリポジトリに置く。

`cloud_base_branch` は、子に渡す checkout の基準ブランチ・コミットとして扱う。コード変更の比較では対象の Git リポジトリと HEAD を確認してから作業場所を分ける。親リポジトリとサブモジュールは別リポジトリなので、対象アプリのコードを書く子はそのアプリ側を作業の基点にする。

## メタデータと文章

Claude が登録する名前と呼び出し条件は入口の frontmatter を使う。原文の `mode`、`icon`、`color`、`reminder` は Cursor の表示・モード設定であり、Claude の設定としては転記しない。

原文の英語指定はプロジェクトまたはユーザーの言語指定に合わせる。原文の品質基準と出力に必要な情報は維持する。

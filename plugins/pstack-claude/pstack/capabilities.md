# 対応機能と未移植部分

## スキル単位の対応状況

「入口あり」は、原文のすべての外部連携を移植したという意味ではない。実際のビルド・テスト・UI 操作には、対象アプリの実行環境も必要になる。

| スキル | 今回の対応 | 残る差分 |
| --- | --- | --- |
| `how` | 入口あり。コード調査、構造・処理の説明 | 並列調査は独立した Claude で実行 |
| `architect`・`arena` | 入口あり。複数の設計・実装案を比較して統合 | GPT・Grok を交えた比較はなくなる |
| `interrogate` | 入口あり。独立した Claude による批判的レビュー | 複数社・複数モデルファミリーによる合意の確認にはならない |
| `swarm` | 入口あり。分担・競争・結果集約 | ワーカーごとの別クラウド VM とユーザー端末への切り替えはない |
| `blast-radius`・`tdd`・`no-comments` | 入口あり。影響調査、テストからの修正、コメントレビュー | 実コードを動かす依存ツールは対象環境に必要 |
| `typescript-best-practices` | 入口あり。型・TypeScript の設計基準 | 原文をそのまま参照 |
| `bro`・`unslop`・`technical-writing` | 入口あり。説明・文章の整理 | 日本語指定などはプロジェクトの指示に従う |
| `principle-*` 全 21 件 | 入口あり。設計・実装・検証の原則 | 原則の本文をそのまま参照 |
| `why` | 入口あり。履歴と外部の根拠を調査 | Cursor の MCP 接続は引き継がれない。接続のない情報源は調査できない |
| `teach` | 入口あり。`how` と `why` を使った説明 | 外部情報源と図の画像生成は、Claude にあるツール次第 |
| `create-verification-skill` | 入口あり。検証スキルと機能マップを作成 | 作成先を Claude 用に変更。ブラウザー等の実行環境は別途必要 |
| `maintain-verification-skill` | 入口あり。検証スキルを実装・動作と照合して修正 | 終端の PR 作成・共有は今回の移植範囲外 |
| `show-me-your-work` | 入口あり。TSV の記録と既存の `scripts/log.sh` | Cursor transcript と照合する監査は未移植。レビューは Claude のみ |
| `figure-it-out` | 入口あり。独自の作業計画、検証単位、仮説検証ループ | 最後の transcript 監査は `show-me-your-work` と同じ制約 |
| `poteto-mode` | 入口あり。原則と手順の読み込み、設計・実装の委譲 | 常駐モードの表示・リマインダー、後述の運用 playbook は未移植 |
| `setup-pstack` | 原文のみ保持 | Cursor のモデル検出・設定画面と `.mdc` 出力は使えない。今回は親の Claude を継承 |
| `recall`・`reflect` | 原文のみ保持 | Cursor の会話履歴をたどる復元・振り返りは使えない。Claude の履歴形式への接続は未作成 |
| `automate-me` | 原文のみ保持 | 会話履歴から個人の作業スタイルをスキル化する一連の処理は未移植 |
| `grokbot/make-bot-ui` | 原文のみ保持 | Cursor の Grok Bot・Routine・秘密情報カードに連動した UI 作成は未移植 |
| `deslop`・`control-cli`・`control-ui` | 補助スキルの入口あり | ハーネスの構築手順を共有する。ブラウザー・PTY・tmux 等の実行環境を導入するものではない |

Claude 用の入口を作らない 5 件も、同梱の `upstream/pstack/skills/` に残している。

## poteto-mode の playbook と補助ツール

| 原文の playbook | コード作成への適用と未移植部分 |
| --- | --- |
| `investigation`・`bug-fix`・`perf-issue`・`feature`・`refactoring`・`prototype` | 調査、再現、設計、実装、検証の手順を読み替えて使う。末尾から呼ぶ PR 作成は未移植 |
| `hillclimb` | 測定・仮説・改善・意思決定ログを使う。長時間継続の制御、transcript 監査、PR 作成は未移植 |
| `runtime-forensics`・`trace-forensics` | 計測・トレース読解の手順を使う。必要な計測環境と末尾の PR 手順は別途必要 |
| `visual-parity` | 比較と修正の手順を使う。実際の UI 起動・画像比較の環境は別途必要 |
| `authoring-a-skill` | 原文を保持。依存する Cursor 組み込み `create-skill` の Claude 用入口は今回作成していない |
| `eval` | 原文を保持。実行結果と Cursor transcript を使ったエージェント評価環境は未移植 |
| `babysit`・`shipping`・`opening-a-pr` | 原文を保持。PR 監視、Bugbot、レビュー解消、Graphite によるスタックの出荷は未移植 |
| `autonomous-run`・`orchestrate`・`autopilot-full`・`autopilot-stack`・`multi-phase-plan` | 原文を保持。長時間の継続実行、起床予約、複数 PR の状態管理・マージ制御は未移植 |
| `session-pickup`・`pause-safely` | 原文を保持。Cursor の会話・クラウド実行状態の受け渡しは未移植 |
| `worktree-cleanup` | 原文を保持。Cursor transcript を使う作業状況の照合と iOS Simulator の処理は未移植 |

`poteto-mode/scripts/check-plan.mjs` のモデル・起床予約などの検査、`scripts/watch-pr/` の GraphQL 監視、`scripts/orch/` の制御、`scripts/worktree-audit.sh` の Cursor 履歴参照は変更していない。Claude 用の代替実装もない。通常の Git 操作や、Claude 自体の PR 作成能力が失われるという意味ではなく、pstack 固有の運用手順を互換化していないという区別になる。

**未移植機能への遷移を止めるルールは追加していない。** 原文には PR 作成や未移植 playbook への参照が残るため、そこへ進むと Cursor 固有のツール・履歴・実行環境を要求する場合がある。`poteto-mode` 全体の完走を保証する移植ではない。

Claude クラウドではネットワーク設定・GitHub の認可も別途関係する。GitHub GraphQL には許可されたクエリの制約があるため、pstack の独自監視をそのまま使えるとは扱わない。[クラウド環境の公式仕様](https://code.claude.com/docs/en/cloud-environments)

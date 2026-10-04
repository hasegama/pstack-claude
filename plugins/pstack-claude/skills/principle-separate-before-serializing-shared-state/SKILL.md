---
name: principle-separate-before-serializing-shared-state
description: "並列処理の共有書き込みを分離し、共有が本当に必要な部分だけ直列化する。同じファイル・ブランチ・状態への競合を設計するときに使う。"
---

最初に [Claude 用の読み替え](${CLAUDE_PLUGIN_ROOT}/pstack/runtime.md)、続いて [原文](${CLAUDE_PLUGIN_ROOT}/upstream/pstack/skills/principle-separate-before-serializing-shared-state/SKILL.md) を全文読む。
読み替えを原文と参照資料に適用し、ユーザーの依頼または親から渡された対象について作業する。参照資料・スクリプトの相対パスは原文の場所から解決する。

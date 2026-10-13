---
name: correct
description: "このリポジトリでエージェントが繰り返す誤りを分類し、構造・型・lint・テスト・文書の順で再発しない仕組みにする。/correct や、同じ指摘が繰り返されるときに使う。"
disable-model-invocation: true
---

最初に [Claude 用の読み替え](${CLAUDE_PLUGIN_ROOT}/pstack/runtime.md)、続いて [原文](${CLAUDE_PLUGIN_ROOT}/upstream/pstack/skills/correct/SKILL.md) を全文読む。
読み替えを原文と参照資料に適用し、ユーザーの依頼または親から渡された対象について作業する。参照資料・スクリプトの相対パスは原文の場所から解決する。

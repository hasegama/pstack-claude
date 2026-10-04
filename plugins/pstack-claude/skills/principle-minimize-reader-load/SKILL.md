---
name: principle-minimize-reader-load
description: "処理を読むために追う層と覚える状態を減らす。追跡しにくいコードの設計・レビューに使う。"
---

最初に [Claude 用の読み替え](${CLAUDE_PLUGIN_ROOT}/pstack/runtime.md)、続いて [原文](${CLAUDE_PLUGIN_ROOT}/upstream/pstack/skills/principle-minimize-reader-load/SKILL.md) を全文読む。
読み替えを原文と参照資料に適用し、ユーザーの依頼または親から渡された対象について作業する。参照資料・スクリプトの相対パスは原文の場所から解決する。

---
name: interrogate
description: "独立した複数の Claude レビュアーで同じ対象を批判的に検証し、盲点や反証をまとめる。/interrogate や、設計・コードを厳しくレビューする依頼に使う。"
---

最初に [Claude 用の読み替え](${CLAUDE_PLUGIN_ROOT}/pstack/runtime.md)、続いて [原文](${CLAUDE_PLUGIN_ROOT}/upstream/pstack/skills/interrogate/SKILL.md) を全文読む。
読み替えを原文と参照資料に適用し、ユーザーの依頼または親から渡された対象について作業する。参照資料・スクリプトの相対パスは原文の場所から解決する。

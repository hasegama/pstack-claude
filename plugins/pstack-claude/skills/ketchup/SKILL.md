---
name: ketchup
description: "ユーザーの最後の発言以降にこの会話で起きたことを平易にまとめ、ユーザーの判断が必要な事項ごとに要点を示す。/ketchup や、途中経過に追いつきたいという依頼に使う。"
disable-model-invocation: true
---

最初に [Claude 用の読み替え](${CLAUDE_PLUGIN_ROOT}/pstack/runtime.md)、続いて [原文](${CLAUDE_PLUGIN_ROOT}/upstream/pstack/skills/ketchup/SKILL.md) を全文読む。
読み替えを原文と参照資料に適用し、ユーザーの依頼または親から渡された対象について作業する。参照資料・スクリプトの相対パスは原文の場所から解決する。

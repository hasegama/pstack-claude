---
name: poteto-agent
description: /poteto-mode の実行中に、コード作成や補助作業を任される子エージェント。/poteto-mode 自体の実行役には使わない。作業ごとに新しく起動し、再開は poteto-mode の Subagents 節が認める場合に限る。
model: inherit
background: true
---

[Claude 用の読み替え](${CLAUDE_PLUGIN_ROOT}/pstack/runtime.md)、[元の定義](${CLAUDE_PLUGIN_ROOT}/upstream/pstack/agents/poteto-agent.md) を全文読み、親から渡された対象に適用する。
作業前に [poteto-mode の入口](${CLAUDE_PLUGIN_ROOT}/skills/poteto-mode/SKILL.md) と、その先の原文・Principles を全文読む。

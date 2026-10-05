#!/usr/bin/env node
// TLC の状態グラフ (-dump dot,actionlabels) と反例トレース (TLC の標準出力) から、
// vlmkit-anim の state-machine シーンと、その図が守るべき事実シート (expect) を作る。
//
// 図は「TLC が実際に列挙した状態と遷移」だけで描く。記憶や想像で状態を足さない。
//
//   node tlc-to-scene.mjs --dot full.dot [--trace tlc.out] [--vars pc,count]
//        [--abbrev read=R,write=W] [--also 'A,B,C'] [--title T] [--layout lr] --out fig/name
//   → fig/name.scene.json, fig/name.expect.json
//
// - 自己ループ (終端での stuttering) は描かず、その状態を final (二重丸) にする。
// - --vars で状態ラベルに出す変数と順序を選ぶ (id は状態ごとに別なので潰れない)。
// - --abbrev で値を短くする (ラベルが長いと図が読めない。凡例は本文に書く)。
// - --trace があれば、その行動列を trace にする。無ければ trace は空の note 1 つ。
// - --also で、反例の前に別の行動列 (例: 正しい順序) を再生する。図は反例の終わりで止まる。
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname } from 'node:path';
import { parseArgs } from 'node:util';

const { values: opt } = parseArgs({
  options: {
    dot: { type: 'string' },
    trace: { type: 'string' },
    vars: { type: 'string' },
    title: { type: 'string', default: 'TLC state graph' },
    layout: { type: 'string', default: 'lr' },
    abbrev: { type: 'string' },
    also: { type: 'string' },
    bare: { type: 'boolean', default: false },
    out: { type: 'string' },
  },
});
if (!opt.dot || !opt.out) {
  console.error('usage: tlc-to-scene.mjs --dot full.dot [--trace tlc.out] [--vars a,b] --out path/name');
  process.exit(2);
}

const dot = readFileSync(opt.dot, 'utf8');
const unescape = (s) => s.replace(/\\"/g, '"').replace(/\\\\/g, '\\');

// "/\ pc = [a |-> "read", b |-> "read"]\n/\ count = 0" → { pc: '[a:read, b:read]', count: '0' }
function parseState(label) {
  const vars = {};
  for (const line of unescape(label).split('\\n')) {
    const m = line.match(/^\/\\\s*(\w+)\s*=\s*(.*)$/) ?? line.match(/^(\w+)\s*=\s*(.*)$/);
    if (m) vars[m[1]] = m[2].replace(/\s*\|->\s*/g, ':').replace(/"/g, '');
  }
  return vars;
}
const normAction = (a) => unescape(a).replace(/"/g, '');

const nodes = new Map(); // dot id → { vars, initial }
const edges = [];
for (const line of dot.split('\n')) {
  let m = line.match(/^(-?\d+) -> (-?\d+) \[label="((?:[^"\\]|\\.)*)"/);
  if (m) { edges.push({ from: m[1], to: m[2], on: normAction(m[3]) }); continue; }
  m = line.match(/^(-?\d+) \[label="((?:[^"\\]|\\.)*)"(.*)$/);
  if (m) nodes.set(m[1], { vars: parseState(m[2]), initial: /style\s*=\s*filled/.test(m[3]) });
}
const initialDot = [...nodes].find(([, n]) => n.initial)?.[0];
if (!initialDot) throw new Error('no initial state (style=filled) in the dot file');

// BFS 順に s0, s1, … と ASCII の id を振る (id は事実シートと図の共通語彙)
const order = [initialDot];
for (let i = 0; i < order.length; i++)
  for (const e of edges) if (e.from === order[i] && !order.includes(e.to)) order.push(e.to);
const idOf = new Map(order.map((d, i) => [d, `s${i}`]));

const pick = opt.vars ? opt.vars.split(',') : null;
const abbrev = Object.fromEntries((opt.abbrev ?? '').split(',').filter(Boolean).map((p) => p.split('=')));
const shorten = (v) => {
  const inner = v.replace(/^\[(.*)\]$/, '$1');
  // --bare: レコードのキーも落として値だけ並べる ("a:R, b:W" → "R W")
  const vals = opt.bare ? inner.split(', ').map((kv) => kv.replace(/^\w+:/, '')) : inner.split(', ');
  return vals.map((x) => x.replace(/\w+/g, (w) => abbrev[w] ?? w)).join(' ');
};
const labelOf = (vars) =>
  (pick ?? Object.keys(vars)).filter((k) => k in vars)
    .map((k) => (opt.bare ? shorten(vars[k]) : `${k}=${shorten(vars[k])}`)).join(opt.bare ? ' | ' : ' / ');

const finals = new Set(edges.filter((e) => e.from === e.to).map((e) => idOf.get(e.from)));
const transitions = edges
  .filter((e) => e.from !== e.to)
  .map((e) => ({ from: idOf.get(e.from), to: idOf.get(e.to), on: e.on }));

// 反例トレース: "State 2: <Read("a") line 15, ...>" の行動名を順に拾う
let trace = [];
const visited = ['s0'];
// 行動列を s0 から辿る (遷移に無い行動なら、図がTLCと食い違っているのでエラー)
function play(actions, cur = 's0') {
  for (const a of actions) {
    const t = transitions.find((t) => t.from === cur && t.on === a);
    if (!t) throw new Error(`action ${a} is not a transition from ${cur}`);
    trace.push(a);
    visited.push((cur = t.to));
  }
  return cur;
}
if (opt.also) play(opt.also.split(','));
if (opt.trace) {
  const out = readFileSync(opt.trace, 'utf8');
  const actions = [...out.matchAll(/^State \d+: <(.+?) line \d+/gm)].map((m) => m[1].replace(/"/g, ''));
  if (opt.also) {
    trace.push({ goto: 's0', caption: 'TLC の反例: 初期状態に戻り、別の順序で実行する' });
    visited.push('s0');
  }
  const cur = play(actions);
  if (/^State \d+: Stuttering/m.test(out)) trace.push({ note: `${cur} で止まったまま (stuttering)` });
}
if (trace.length === 0) trace = [{ note: 'TLC が列挙した到達可能な状態と遷移' }];

const scene = {
  format: 'vlmkit-anim/scene@1',
  kind: 'state-machine',
  title: opt.title,
  layout: opt.layout,
  states: order.map((d) => {
    const id = idOf.get(d);
    return { id, label: labelOf(nodes.get(d).vars), ...(finals.has(id) ? { final: true } : {}) };
  }),
  initial: 's0',
  transitions,
  trace,
};
const expect = {
  format: 'vlmkit-anim/expect@1',
  states: order.map((d) => idOf.get(d)),
  transitions: transitions.map((t) => `${t.from}->${t.to}:${t.on}`),
  initial: 's0',
  final: [...finals],
  ...(opt.trace ? { visited, end: visited.at(-1) } : {}),
};

mkdirSync(dirname(opt.out), { recursive: true });
writeFileSync(`${opt.out}.scene.json`, JSON.stringify(scene, null, 2) + '\n');
writeFileSync(`${opt.out}.expect.json`, JSON.stringify(expect, null, 2) + '\n');
console.log(`${order.length} states, ${transitions.length} transitions, ${finals.size} final; trace ${visited.join(' -> ')}`);
console.log(`wrote ${opt.out}.scene.json, ${opt.out}.expect.json`);

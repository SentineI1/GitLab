# Bias-Mode Diagrams Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Draw a matching schematic for the fixed-bias and emitter-bias modes so every mode shows a circuit beside the form.

**Architecture:** Three inline SVG blocks inside one `<figure>` in `templates/index.html`, selected by `values.mode`; the caption and region badge are shared. CSS drops the now-unused single-column rule. No Python changes.

**Tech Stack:** Jinja2 template, inline SVG, plain CSS.

**Spec:** `docs/superpowers/specs/2026-11-16-bias-mode-diagrams-design.md`

## Global Constraints

- Do not modify `bias_modes.py`, `bjt_bias.py`, `independent_check.py`, `app.py`, or any file in `tests/`.
- Do not add new `unittest` tests; verification is the existing suite plus a Browser pass.
- Divider drawing stays visually identical.
- Reuse the divider coordinates: VCC rail `M120 30 H295`, Q1 base line at `x=250` (`y=125`–`175`), collector to `(295,105)`, emitter to `(295,195)`, RC box `x=287 y=35 w=16 h=35`, viewBox `0 0 420 360`.
- Every label uses the existing classes `ref` and `val`; live values come from `values.<field>`.

## Review Focus

1. **Blank or invalid POST** — the diagram still renders, with empty values, and no region badge.
2. **Wrong-mode parts** — fixed bias must show no R2 and no RE; emitter bias must show RE; divider must show R1, R2, and RE.
3. **Values follow the form** — editing VCC/RB/RC/RE updates the diagram labels.
4. **Region badge** — appears only after a successful calculation and matches the result badge.
5. **Long values** — huge numbers stay inside the panel (existing divider behaviour; no new overflow rules).

---

### Task 1: Three mode drawings

**Files:**
- Modify: `templates/index.html:19-69`

**Interfaces:**
- Consumes: `values.mode`, `values.vcc`, `values.rb`, `values.rc`, `values.re`, `values.beta`, `values.vbe`, `result`.
- Produces: one `<figure class="circuit-panel">` whose SVG matches the selected mode; `class="circuit"`, `role="img"`, `id="circuit-title"`, `class="circuit-region badge badge-<region>"` preserved.

- [ ] **Step 1: Replace the divider-only figure with the three-branch figure**

Change `<div class="workspace{% if values.mode != 'divider' %} workspace-single{% endif %}">` to `<div class="workspace">`.

Inside the figure, keep the existing divider `<svg>` as the `{% if values.mode == "divider" %}` branch, add the fixed SVG as `{% elif values.mode == "fixed" %}`, the emitter SVG as `{% else %}`, and move the existing `<figcaption>` after `{% endif %}` so it is shared.

Fixed-bias SVG:

```html
      <svg class="circuit" viewBox="0 0 420 360" role="img" aria-labelledby="circuit-title">
        <title id="circuit-title">NPN common-emitter fixed-bias circuit: VCC feeds RB to the base and RC to the collector; the emitter is grounded.</title>
        <g class="wire">
          <path d="M120 30 H295"/>
          <path d="M120 30 V60"/>
          <path d="M120 105 V150"/>
          <path d="M120 150 H250"/>
          <path d="M295 30 V35"/>
          <path d="M295 70 V105"/>
          <path d="M250 140 L295 105"/>
          <path d="M250 160 L295 195"/>
          <path d="M295 195 V312"/>
          <path d="M285 312 H305"/>
          <path d="M290 317 H300"/>
          <path d="M293 322 H297"/>
        </g>
        <circle class="node" cx="120" cy="150" r="3.5"/>
        <line class="component" x1="250" y1="125" x2="250" y2="175"/>
        <polygon class="node" points="279,183 292,190 283,196"/>
        <rect class="component" x="112" y="60" width="16" height="45" rx="1"/>
        <rect class="component" x="287" y="35" width="16" height="35" rx="1"/>
        <text class="ref" x="120" y="20">VCC</text>
        <text class="val" x="152" y="20">{{ values.vcc }} V</text>
        <text class="ref" x="134" y="80">RB</text>
        <text class="val" x="134" y="96">{{ values.rb }} ohm</text>
        <text class="ref" x="309" y="48">RC</text>
        <text class="val" x="309" y="64">{{ values.rc }} ohm</text>
        <text class="ref" x="302" y="160">Q1</text>
      </svg>
```

Emitter-bias SVG: the same markup with these three changes — insert `<path d="M295 195 V210"/>` before the emitter drop, add `<rect class="component" x="287" y="210" width="16" height="45" rx="1"/>` after the RC rect, change the emitter drop to `<path d="M295 255 V312"/>`, add `<text class="ref" x="309" y="226">RE</text>` and `<text class="val" x="309" y="242">{{ values.re }} ohm</text>`, and use the title `NPN common-emitter emitter-bias circuit: VCC feeds RB to the base and RC to the collector; RE returns the emitter to ground.`

- [ ] **Step 2: Check the rendered markup per mode**

Run the existing app with `.\\.venv\\Scripts\\python.exe -m flask --app app run --port 5000` (restart it if already running) and POST each mode. Expected in the response body:

- divider: `>RB<` absent, `>R1<`, `>R2<`, `>RE<` present
- fixed: `>RB<`, `>RC<` present; `>R1<`, `>R2<`, `>RE<` absent
- emitter: `>RB<`, `>RC<`, `>RE<` present; `>R1<`, `>R2<` absent
- every mode: `class="circuit"`, `circuit-title`, and the submitted values (e.g. `1200000 ohm`)

---

### Task 2: Style cleanup, README, and full verification

**Files:**
- Modify: `static/style.css:41-42`
- Modify: `README.md:31-33`

**Interfaces:**
- Consumes: Task 1's always-two-column workspace.
- Produces: no unused `.workspace-single` rule; README describes the three drawings.

- [ ] **Step 1: Remove the unused single-column rule**

Delete `.workspace-single { grid-template-columns: 1fr; }` from the `@media (min-width: 760px)` block, leaving only `.workspace { grid-template-columns: 1fr 1fr; }`.

- [ ] **Step 2: Describe the drawings in the README**

After the divider circuit block, add: the fixed-bias drawing shows `RB` from `VCC` to the base, `RC` to the collector, and a grounded emitter; the emitter-bias drawing adds `RE` between emitter and ground. The drawing follows the selected mode and shows the values currently in the form.

- [ ] **Step 3: Run the existing suite**

Run: `.\\.venv\\Scripts\\python.exe -m unittest discover -s tests -t .`
Expected: `Ran 43 tests ... OK`.

- [ ] **Step 4: Browser pass for all three modes**

Restart the server, then confirm for each mode: the drawing changes with the selector, labels show the submitted values, the region badge appears only after a calculation, and the divider drawing is unchanged from before. Also confirm a blank POST in each mode still renders a drawing with no badge.

- [ ] **Step 5: Commit**

```powershell
git add templates/index.html static/style.css README.md docs/superpowers/specs/2026-11-16-bias-mode-diagrams-design.md docs/superpowers/plans/2026-11-16-bias-mode-diagrams.md
git commit -m "feat: draw the fixed and emitter bias circuits"
```

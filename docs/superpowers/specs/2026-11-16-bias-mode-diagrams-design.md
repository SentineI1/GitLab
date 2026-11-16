# Bias-mode circuit diagrams

**Date:** 2026-11-16
**Status:** Approved — user approved approach A in conversation.

## Intent

Every bias mode gets a schematic beside the form. Today only the divider mode
draws one, and the other two modes collapse to a single column. The new
drawings follow the existing divider drawing so the three modes read as the
same circuit with different parts.

## Goals

- A fixed-bias drawing: VCC rail, RB from VCC to base, RC to collector,
  emitter grounded.
- An emitter-bias drawing: same, plus RE between emitter and ground.
- Same viewBox, transistor position, component style, labels, live form
  values, caption, and region badge as the divider drawing.
- The diagram always matches the selected mode.

## Non-goals

- New unittest tests; verification is a Browser pass.
- Changing solvers, validation, routes, or result keys.
- Animating or redrawing the divider schematic.

## Approaches considered

- **A (chosen):** three inline SVG blocks in `templates/index.html`, selected
  with `{% if %}` / `{% elif %}` / `{% else %}`. Matches the current
  single-file template and keeps all three drawings easy to compare.
- **B:** one Jinja partial per mode in `templates/partials/` plus `{% include %}`.
  Tidier, but adds files and a template pattern the project does not use yet.

## Design

- `templates/index.html`: replace the divider-only `{% if %}` with a
  three-branch block inside one `<figure class="circuit-panel">`. The
  `<figcaption>` (beta, VBE, region badge) stays shared after the SVG.
- Coordinates reuse the divider drawing: VCC rail `M120 30 H295`, Q1 base line
  at `x=250`, collector to `(295,105)`, emitter to `(295,195)`, RC box
  `x=287 y=35 h=35`.
  - Fixed: RB box `x=112 y=60 h=45` on the left; base node at `(120,150)`;
    emitter wire `M295 195 V312`; ground symbol centred at `x=295`.
  - Emitter: same as fixed plus RE box `x=287 y=210 h=45` and wire
    `M295 255 V312`.
- Labels: RB / RC / RE / VCC / Q1 with the submitted values, same classes
  (`ref`, `val`).
- `static/style.css`: drop the now-unused `.workspace-single` rule and its
  media-query line, because every mode shows a drawing.
- `README.md`: one line describing the fixed and emitter drawings.

## Verification

- Existing suite: `python -m unittest discover -s tests -t .` → 43 tests OK.
- Browser: switch the three modes, confirm the drawing changes, values match
  the inputs, the region badge appears only after a calculation, and the
  divider drawing is unchanged.

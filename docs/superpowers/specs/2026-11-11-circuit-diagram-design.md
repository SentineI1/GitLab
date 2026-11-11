# Circuit diagram on the bias page

**Date:** 2026-11-11
**Status:** Approved — user instruction "สร้างวงจรcircuitเพิ่มเติม" after the
inline-SVG proposal.

## Intent

The page is a form over a circuit. Show the circuit: a drawn schematic of the
NPN common-emitter bias stage, with the values typed into the form appearing on
the diagram, so the inputs read as points on a circuit rather than seven
unrelated numbers.

## Goals

- One inline SVG of `VCC`, `R1`, `R2`, `RC`, `RE`, `Q1`, and ground.
- The diagram shows the current `values` — defaults on `GET`, the submitted
  strings on `POST` (including invalid ones, so the picture still matches the
  form).
- After a successful calculation, a region pill (`Active` / `Cutoff` /
  `Saturation`) appears with the diagram, reusing the existing badge classes.
- No JavaScript. Works with the server-rendered page alone.
- Accessible: the SVG carries `role="img"` and a `<title>`.

## Non-goals

- Drag-and-drop, editable schematic, netlist, or simulation.
- Extra components (coupling capacitors, load, source) beyond the seven inputs.
- Bitmap assets, canvas, or a JS drawing library.
- Dark mode or a separate mobile interaction.

## Approaches

- **A. Hand-written inline SVG in the template (chosen).** No new dependency,
  scales cleanly, binds values through Jinja, and is assertable in the rendered
  HTML.
- **B. A static SVG/PNG asset.** Simpler template, but it cannot show the
  entered values or the region, and it drifts from the form.
- **C. Canvas/JavaScript drawing.** Adds a runtime dependency and moves the
  picture out of server-rendered HTML, where the tests live.

## Design

- Template: a `.workspace` wrapper holds a `figure.circuit-panel` and the form.
  On wide screens they sit side by side; on narrow screens they stack.
- SVG `viewBox="0 0 420 360"`, drawn with straight wires and rectangular
  resistor bodies. Classes: `.wire`, `.component`, `.ref`, `.val`.
- Labels: `VCC` above the top rail, `R1`/`R2` to the right of the divider,
  `RC`/`RE` to the right of the collector/emitter resistors, `Q1` by the
  transistor. Values come from `values.vcc`, `values.r1`, and so on, with
  units (`V`, `ohm`).
- Caption under the diagram: `beta = …` and `VBE = … V`, plus the region pill
  when `result` exists.
- CSS: `.workspace` grid (one column, two columns at `min-width: 760px`),
  `.circuit-panel` panel styling, `.circuit` sizing, `.circuit-caption`.
  Container width grows to 880px to fit the two columns and the results table.

## Tests

- `GET /` renders `class="circuit"`, the component refs, and the default
  values with units (`12 V`, `47000 ohm`).
- `POST /` with `vcc=5` shows `5 V` on the diagram and no `12 V`.
- `POST /` with valid defaults shows a `circuit-region` element reading
  `Active`.
- `POST /` with an invalid field still renders the diagram with the submitted
  value and no region pill.

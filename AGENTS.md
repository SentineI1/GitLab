# Contributor rules (including AI agents)

## Preserve Lab 3

- Do not rename, replace, or move `app.py`, `bias_modes.py`, `bjt_bias.py`,
  `independent_check.py`, or the templates into a subdirectory.
- All 43 original Lab 3 tests must keep passing unchanged. The SPICE feature is
  additive; ordinary `POST /` requests and the **Calculate** button must still
  return exactly the analytical result and cross-check they always did.
- Fixed-bias and emitter-bias modes are analytical only. A `simulate` action in
  those modes is ignored, not partially applied.

## Data provenance

- Every SPICE number and every plotted point must come from an ngspice `.print`
  table parsed by `spice_engine.py`. Never fabricate, interpolate for display,
  or hard-code a "success" trace or a success value.
- Keep the analytical result and the SPICE result visibly separate on the page.
  The analytical model uses fixed VBE and constant beta; the SPICE model is
  `.model CEQ NPN(IS=1E-14 BF=<beta> VAF=100)` with BF from the form. IS and VAF
  are fixed constants, documented in `README.md`.
- AC gain is `V(output)/V(base)` (Vin measured after `Cin`); AC phase from
  `vp()` is radians in this batch build and is converted to degrees in Python.
- If no −3 dB crossing exists in the sweep, show the literal string
  `not determined in sweep range`. Do not substitute an estimated value.

## Engine honesty

- Run ngspice as a list-form subprocess with a timeout, never `shell=True`.
  Use `ngspice_con.exe`; `ngspice.exe` is silent here and is not used.
- An explicit `NGSPICE_PATH` is authoritative: if it is invalid, fail fast with
  that path shown. Do not silently fall back to another executable.
- Nonzero exit codes, `Error:`/`Fatal error:` text in output, timeouts, and
  missing or unparsable tables must all produce a visible error status with the
  engine detail. Never hide an engine error to keep a plot on screen.
- Warnings such as `can't parse 'base': ignored` are known harmless messages in
  successful runs; do not treat them as failures.
- ngspice paginates long tables by repeating the `Index` header. Parsers must
  join all pages of the requested table and must not mix in the next table.

## Validation and changes

- When circuit values, the model, netlist layout, parser, or plot code changes,
  re-run the real analyses and update `docs/validation.md` with the new measured
  numbers. No number goes into that file before a run produces it.
- Keep the full suite green: `.\\.venv\\Scripts\\python.exe -m unittest discover -s tests -t .`
- Do not commit `tools/ngspice/`; the simulator binary is gitignored and must be
  installed locally per `README.md`.
- Keep the browser page's netlist and log `<details>` available so a reader can
  reproduce any displayed SPICE result.

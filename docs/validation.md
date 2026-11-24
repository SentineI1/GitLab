# Validation evidence — CE SPICE simulator v1

**Date:** 2026-11-24
**Environment:** Windows, Python 3.12, Flask 3.x, matplotlib 3.11.2,
ngspice-47 console build at
`tools/ngspice/Spice64/bin/ngspice_con.exe` (gitignored, installed locally).

All numbers below were produced by the runs described here and were only copied
into this file after those runs completed. No trace point or result value is
hand-written into the app.

## Fixture and model

| Input | Value |
| ----- | ----- |
| VCC | 12 V |
| R1 / R2 | 100 kΩ / 22 kΩ |
| RC / RE | 2.2 kΩ / 1 kΩ |
| RL | 10 kΩ |
| Cin / Cout | 10 µF / 10 µF |
| Source | 10 mV peak, 1 kHz |
| beta (form) | 150 |
| VBE (analytical only) | 0.7 V |

Netlist model line, from the actual run:

```
.model CEQ NPN(IS=1E-14 BF=150 VAF=100)
```

`BF` comes from the form's `beta`; `IS` and `VAF` are fixed constants. VBE is
**not** a SPICE parameter here — SPICE derives VBE from IS/BF/VAF — so the SPICE
and analytical blocks are not expected to agree digit-for-digit.

## Engine runs

All three runs returned `status = success`, `returncode = 0`, using the exe
above. Netlist and log are shown in the page's `<details>` sections; the page
displays the last 1500 characters of the log, while `simulate()` retains the
full captured stdout/stderr.

### DC (`.op`)

netlist commands: `.op`, `.print op v(base) v(emit) v(collect) @q1[ic]`

| Quantity | SPICE (ngspice) | Analytical reference (fixed VBE) | Unit |
| -------- | --------------- | -------------------------------- | ---- |
| VB | 2.013016 | 2.00776 | V |
| VE | 1.352006 | 1.30776 | V |
| VC | 9.044000 | 9.14198 | V |
| VCE | 7.691994 | 7.83423 | V |
| IC | 1.344126 | 1.29910 | mA |

Both classify the transistor as active. The analytical values are the original
`bjt_bias.analyze` result from the unchanged Lab 3 path.

### AC (`.ac dec 20 1 10Meg`)

Four separate `.print ac` lines: `vdb(output)`, `vp(output)`, `vdb(base)`,
`vp(base)`. 141 real frequency points from 1 Hz to 10 MHz.

| Quantity | Value |
| -------- | ----- |
| Midband gain | 4.8951 dB |
| Frequency of midband maximum | 281.8383 Hz |
| Gain at 1 kHz | 4.8951 dB |
| Phase at midband maximum | −179.735° |
| Lower −3 dB crossing | 1.30977 Hz |
| Upper −3 dB crossing | `not determined in sweep range` |
| Gain reference | `V(output) / V(base)` (Vin after Cin) |

`vp()` values in this batch build are radians; the difference is converted to
degrees in Python and wrapped to [−180°, 180°). The cutoff is the −3 dB point
relative to the sweep maximum and is interpolated in log-frequency only when a
real crossing exists. The upper crossing was absent in this sweep, so the page
shows the literal text above rather than a made-up number.

### Transient (`.tran 10u 5m 0 10u`)

Commands: `.tran 10u 5m 0 10u`, `.print tran v(input) v(output)`.

| Quantity | Value |
| -------- | ----- |
| Real samples plotted | 508 |
| First sample | 0 s |
| Last sample | 0.005 s |
| Peak |V(input)| | 0.009998452 V |
| Peak |V(output)| | 0.01758797 V |

Vin is the source side of `Cin`, Vout is across `RL`. At the 1 kHz baseline the
5 ms window is exactly five periods, so all 508 real samples are plotted. Above
1 kHz both the stop and the step shrink to keep five periods (~100 samples per
period) and the plot shows only that five-period window of real samples.

A post-review responsiveness check ran the transient analysis at higher
frequencies: 10 kHz (`.tran 5e-06 0.0005 0 5e-06`), 1 MHz
(`.tran 5e-08 5e-06 0 5e-08`) and 1 GHz (`.tran 5e-11 5e-09 0 5e-11`) each
produced 108 real samples and a PNG in roughly 0.1 s. The page's Time span row
is formatted from the parsed final sample: the same real runs render `5.000 ms`
at 1 kHz, `5.000 µs` at 1 MHz and `5.000 ns` at 1 GHz, rather than a rounded
`0.000 ms`.

### Paginated-table regression

During evidence capture the AC table initially yielded only 55 points and the
transient table 55 samples. Inspecting the raw log showed ngspice repeats the
`Index ...` header every ~55 rows. `parse_table` was stopping at the first
page. A regression test was written and observed RED before the fix; after
joining all pages of the same table, the reruns above produced 141 AC points
and 508 transient samples. The test is
`tests.test_spice_engine.TestParsers.test_parse_table_joins_paginated_headers`.
A follow-up check hardens the parser: known ngspice banners between pages are
skipped, but unexpected text that interrupts a table raises a `SimulationError`
instead of silently dropping the remaining rows. That test is
`tests.test_spice_engine.TestParsers.test_parse_table_skips_banners_but_rejects_unexpected_text`.

## Live server verification

Started with:

```powershell
.\.venv\Scripts\python.exe -m flask --app app run --port 5000
```

`GET http://127.0.0.1:5000/` returned the prefilled form with the new analysis
selector and the amplitude/frequency fields. POST requests were then sent over
real HTTP to that running server (Python `urllib`), not only through Flask's
in-process test client. Result: all checks below returned HTTP 200 and PASS.

```
PASS mode divider: analytical result, no SPICE panel
PASS mode fixed: analytical result, no SPICE panel
PASS mode emitter: analytical result, no SPICE panel
PASS dc: Simulation complete, SPICE table, netlist + log details, no plot
PASS ac: Simulation complete, SPICE table, netlist + log details, PNG plot
PASS ac: "Frequency (Hz)" label and literal cutoff text present
PASS tran: Simulation complete, SPICE table, netlist + log details, PNG plot
PASS 1 GHz: time span rendered from real samples as 5.000 ns
PASS amplitude 0: "Amplitude must be greater than 0.", no banner, no plot
```

A second instance on port 5001 was started with
`$env:NGSPICE_PATH = "C:\nope\ngspice.exe"` to check the failure path, then
stopped:

```
PASS broken NGSPICE_PATH: "Simulation error", path shown, engine detail shown, no plot
```

No graphical browser/screenshot tool is available in this environment, so no
`docs/captures/` image was produced. The verification above is HTTP-level
against the live Flask server, including the rendered HTML, the base64 PNG
data URIs, and the error states.

## Test suite

The suite also pins the engine gates called out in review: nonzero exit codes,
`Error:`/`Fatal error:`/`aborted` text, timeouts, missing table rows, an
unexpected `analysis` value, zero/non-numeric frequency, the visible engine
error detail with a broken `NGSPICE_PATH`, the literal cutoff text in rendered
HTML, adaptive transient time-span units from parsed samples, banner handling
in table parsing, and emitter mode ignoring `simulate`.

Final command and result:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -t .
```

```
Ran 70 tests in 1.304s
OK
```

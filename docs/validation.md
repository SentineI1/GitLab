# Validation evidence — Lab 3 acceptance and Lab 4 CE SPICE

This file keeps two separately recorded validations in one place. Each
section contains only numbers produced by the run described there.

---

# Lab 3 — Browser acceptance validation

เว็บที่ตรวจ: `http://127.0.0.1:5000/` (Flask รันด้วย `.venv\Scripts\python.exe -m flask --app app run --port 5000`)

## วิธีตรวจและเครื่องมือ

- ใช้ **Playwright MCP** เป็นเส้นทางหลัก สถานะ `✓ playwright connected`
- รุ่น: Node.js 24.20.0 LTS, `@playwright/mcp@latest`, `--browser chrome --isolated`
- เครื่องมือที่เรียกจริง: `browser_navigate`, `browser_snapshot`, `browser_select_option`, `browser_fill_form`, `browser_click`, `browser_take_screenshot`
- ไม่พบ skill `browser-acceptance-check` ในสภาพแวดล้อมนี้ จึงใช้ prompt รอบตรวจของใบงานโดยตรง
- ไม่ใช้ curl และไม่ใช้อ่านโค้ดเป็นคำตอบอ้างอิง
- อ่าน snapshot ใหม่ทุกครั้งหลังเปลี่ยนโหมดหรือส่งฟอร์ม ไม่นำผลรอบก่อนมาใช้

ตาราง A1–A5 ในใบงานเว้นช่อง "คาดหมายก่อนรัน" ไว้ ค่าคาดหมายด้านล่างจึงคำนวณ**อิสระจากสมการในใบงาน** (ไม่ใช่จากโปรแกรมที่ตรวจ) ใช้เกณฑ์ของกลุ่ม: `|ΔIC| ≤ 0.01 mA`, `|ΔVCE| ≤ 0.02 V` เมื่อเทียบกับค่าที่ยังไม่ปัดเศษ

## ค่าอ้างอิงอิสระ (โหมดใหม่ Emitter — A3)

ใช้ค่าของกลุ่ม: `VCC = 12 V`, `RC = 2.2 kΩ = 2200 Ω`, `β = 100`, `VBE = 0.70 V`
A3: `RB = 1 MΩ = 1,000,000 Ω`, `RE = 1 kΩ = 1000 Ω`

```
IB  = (VCC - VBE) / [RB + (β + 1)RE]
    = (12 - 0.70) / [1,000,000 + (101)(1000)]
    = 11.30 / 1,101,000 = 1.026340e-5 A = 0.01026340 mA
IC  = β·IB   = 100 × 0.01026340 mA = 1.026340 mA
IE  = (β+1)IB = 101 × 0.01026340 mA = 1.036603 mA
VE  = IE·RE  = 1.036603 mA × 1000 Ω = 1.036603 V
VC  = VCC - IC·RC = 12 - (1.026340 mA)(2200 Ω) = 9.742053 V
VCE = VC - VE = 9.742053 - 1.036603 = 8.705450 V
```

A4 ทำนายก่อนรัน: เมื่อ `RE` เพิ่มเป็น `2000 Ω` ตัวหาร `RB + (β+1)RE` เพิ่มขึ้น → `IB` และ `IC` **ลดลง** ค่าอ้างอิง `IC = 0.940100 mA`, `VCE = 8.032779 V`

A1 หมายเหตุ: ใบงานระบุให้เทียบกับ "ผล Lab 2 ก่อนแก้" แต่ไม่มีค่าก่อนแก้แนบมา จึงเทียบกับค่าอ้างอิงอิสระของ Divider แทน (`VTH = 2.163934 V`, `RTH = 18032.7869 Ω`, `IC = 1.229858 mA`, `VCE = 8.052155 V`)

## ผล A1–A5

| ID | วิธีตรวจ | อินพุต | ค่าคาดหมาย | ผลที่เห็นพร้อมหน่วย | สถานะ | หลักฐาน |
|---|---|---|---|---|---|---|
| A1 · โหมดเดิม | Playwright MCP (`navigate` → `snapshot` → `fill_form` → `click` → `snapshot`) | Divider · VCC 12 V, R1 100000 ohm, R2 22000 ohm, RC 2200 ohm, RE 1000 ohm, beta 100, VBE 0.70 V | IC 1.229858 mA · VCE 8.052155 V (Δ≤0.01 mA / 0.02 V) | `DC Operating Point · Voltage-divider bias` · **IC = 1.2299 mA**, **VCE = 8.052 V**, `Active` (ΔIC 0.000042 mA, ΔVCE 0.000155 V) | **PASS\*** | `page-2026-11-17T10-43-24-682Z.yml` |
| A2 · Fixed | Playwright MCP (`select_option('fixed')` → snapshot ใหม่ → `fill_form` → `click` → snapshot ใหม่) | Fixed · VCC 12 V, RB 1000000 ohm, RC 2200 ohm, beta 100, VBE 0.70 V (ไม่กรอก RE) | IC 1.130000 mA · VCE 9.514000 V | `DC Operating Point · Fixed bias` · **IC = 1.1300 mA**, **VCE = 9.514 V**, VE = 0.000 V, ภาพวงจรไม่มี RE (Δ = 0) | **PASS** | `page-2026-11-17T10-43-39-010Z.yml` |
| A3 · Emitter | Playwright MCP (`select_option('emitter')` → snapshot ใหม่ → `fill_form` → `click` → snapshot ใหม่) | Emitter · VCC 12 V, RB 1000000 ohm, RC 2200 ohm, RE 1000 ohm, beta 100, VBE 0.70 V | IC 1.026340 mA · VCE 8.705450 V | `DC Operating Point · Emitter bias` · **IC = 1.0263 mA**, **VCE = 8.705 V**, VE = 1.037 V (ΔIC 0.000040 mA, ΔVCE 0.000450 V) | **PASS** | `page-2026-11-17T10-43-56-837Z.yml` |
| A4 · เปลี่ยนค่าเดียว | Playwright MCP (คงโหมด Emitter → `fill_form` เฉพาะ RE → `click` → snapshot ใหม่) | Emitter · เหมือน A3 ทุกค่า เปลี่ยน **RE 1000 → 2000 ohm** | ทำนาย IC ลดลง · อ้างอิง IC 0.940100 mA · VCE 8.032779 V | `DC Operating Point · Emitter bias`, RE = 2000 ohm · **IC = 0.9401 mA** (ลดจาก 1.0263 mA ✅), **VCE = 8.033 V**, VE = 1.899 V (ΔIC 0, ΔVCE 0.000221 V) | **PASS** | `page-2026-11-17T10-44-07-999Z.yml` |
| A5 · อินพุตผิด | Playwright MCP (`select_option('fixed')` → snapshot ใหม่ → `fill_form(RB=0)` → `click` → snapshot ใหม่) | Fixed · RB = 0 ohm | มีข้อความให้แก้ RB, เว็บไม่ล่ม, ไม่แสดงผลเดิมเป็นผลรอบนี้ | ข้อความบนฟอร์ม **"RB must be greater than 0."** · ไม่มีหัวข้อ `DC Operating Point` และไม่มีตารางผลใน snapshot | **PASS** | `page-2026-11-17T10-44-22-799Z.yml` · ภาพหน้าจอ [evidence/A5-fixed-rb0.png](evidence/A5-fixed-rb0.png) |

\* PASS ต่อค่าอ้างอิงอิสระ ประเด็น "ผลก่อนแก้" ยังต้องให้ TA ยืนยัน

ข้อความผลที่คัดจาก snapshot (หลักฐานอย่างน้อยหนึ่งกรณี):

```yaml
# A3 หลังกด Calculate
- heading "DC Operating Point · Emitter bias" [level=2]
- row: cell "IC" / cell "1.0263" / cell "mA"
- row: cell "VCE" / cell "8.705" / cell "V"

# A5 หลังกด Calculate
- spinbutton "RB (ohm) · fixed / emitter": "0"
- paragraph: RB must be greater than 0.
# ไม่มี heading "DC Operating Point" ใน snapshot นี้
```

## บทบาท MCP และการไล่ข้อมูล (trace หนึ่งรอบ)

`OpenCode (MCP client)` → `Playwright MCP (MCP server)` → `Browser` → HTTP → `Flask + Python` → HTTP response → `Snapshot` กลับไปยัง OpenCode เพื่อเทียบกับค่าคาดหมายของกลุ่ม เบราว์เซอร์และ Flask คุยกันผ่าน HTTP ส่วน OpenCode กับ Playwright คุยผ่าน MCP ต่างชั้นกัน

จุดในโค้ดที่เกี่ยวข้อง (อ้างอิงเพื่ออธิบายเส้นทางข้อมูล ไม่ได้ใช้เป็นค่าคาดหมาย):

- `app.py:61–92` — อ่าน `mode` จากฟอร์ม, เรียก `parse_for_mode`, เลือก solver, และรัน cross-check เฉพาะ Divider
- `bias_modes.py:66–115` — `parse_for_mode` ตรวจเฉพาะฟิลด์ของโหมดนั้น (`FIELDS_BY_MODE`) และคืนค่าเป็น float ในหน่วย SI (V, Ω) ข้อความ `RB must be greater than 0.` เกิดจาก `_POSITIVE_LABELS`
- `bias_modes.py:182–196` — `solve_fixed` ใช้ `IB=(VCC−VBE)/RB`
- `bias_modes.py:199–214` — `solve_emitter` ใช้ `IB=(VCC−VBE)/(RB+(β+1)RE)` และคำนวณ `VE=IE·RE`
- `bias_modes.py:127–150` — `_result` ส่งผลเป็น `dict` ที่มีหน่วยในชื่อคีย์ (`*_ma`, `*_v`) โดยแปลง A → mA ด้วย `*1000.0`
- `bias_modes.py:217–223` — `solve(mode, values)` เลือกฟังก์ชันตามโหมด
- `templates/index.html` — ตัวเลือก Bias mode, ป้ายช่อง `· divider` / `· fixed / emitter`, และ `<link rel="icon" href="data:,">` ที่แก้ console 404 favicon

## สิ่งที่ AI สร้าง / นักศึกษาตรวจ

- **AI สร้าง:** ฟังก์ชัน `solve_fixed`, `solve_emitter`, `_result`, `FIELDS_BY_MODE`, `parse_for_mode` ใน `bias_modes.py`; การเลือกโหมดใน `app.py`; ฟอร์ม/ภาพวงจรตามโหมดใน `templates/index.html`
- **นักศึกษาตรวจ:** สมการและหน่วยเทียบกับ Engineering Electronics ผ่านค่าอ้างอิงอิสระข้างบน; ผล Divider เดิมยังตรงกับสมการเดิม (A1); Fixed ไม่ใช้ RE (A2); Emitter ใช้ RE และทิศทางเมื่อเพิ่ม RE (A3→A4); ข้อความตรวจอินพุตผิด (A5); ทวนผลด้วยตนเองอย่างน้อยหนึ่งกรณีผ่าน browser จริง

## GitHub / Commit

- Repository: https://github.com/SentineI1/GitLab
- Commit ของฟีเจอร์ Lab 3: `ac59a8b` (add fixed and emitter bias modes), `cebf0e1` (fixed/emitter diagrams), `9ca9343` (explicit emitter diagram branch), `2f69e93` (plan docs)
- Commit ของรายงานนี้: ดู `git log -1` หลัง push

---

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

That verification was HTTP-level against the live Flask server, including the
rendered HTML, the base64 PNG data URIs, and the error states. A later
graphical-browser acceptance pass is recorded in the next section; the
"no graphical browser tool" statement applied only at the time of this earlier
check.

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
Ran 70 tests in 1.509s
OK
```

---

# Lab 4 — Browser acceptance B1–B8

**Date:** 2026-11-24
**App:** `http://127.0.0.1:5000/`, Flask started with
`.\.venv\Scripts\python.exe -m flask --app app run --port 5000`
**Tool:** local Playwright 1.65.1 + installed Google Chrome channel, not
Playwright MCP (the MCP server was not connected in this harness). This was a
real browser: real navigations, real form fills/selects, real button submits,
aria snapshots, and screenshots. Screenshots were **not** used as the only
engineering evidence; DOM values, netlists, ngspice log excerpts, and plot PNG
hashes were also captured.

No application code was changed during this B1–B8 acceptance pass. The only
changes after the pass are documentation and selected evidence files.

## Method for every case

`fresh navigation → body ariaSnapshot → select/fill exact values → real submit
→ waitForLoadState('networkidle') → new ariaSnapshot → read DOM/netlist/log/plot
→ compare with independent or recorded reference → screenshot`.

A new browser context was used for B1, B2, B3, B4, B5, B6, B7a, B7b, B8
desktop and B8 mobile. B1 switched modes inside its one case and snapshotted
after each Calculate submit. The raw machine-readable result is
[`evidence/B1-B8-report.json`](evidence/B1-B8-report.json).

## Pass criteria

- **B1:** `|ΔIC| ≤ 0.01 mA` and `|ΔVCE| ≤ 0.02 V` against the independent Lab 3
  references above; the heading must change with the selected mode.
- **B2:** ngspice `.op` values equal the recorded run to six decimals; badge
  `Simulation complete`, exit code 0, model line and log visible.
- **B3:** changing only `RE` must change the netlist, operating point/gain and
  the plot bytes in the expected direction.
- **B4/B5/B6:** values must be traceable to real `.print` tables in the shown
  netlist/log; axes and units must be present; source changes must change the
  waveform and PNG hash.
- **B7:** invalid input or invalid engine path must show an error, no success
  badge and no plot.
- **B8:** `documentElement.scrollWidth == clientWidth` at both viewports,
  readable plots/units/buttons, and working mode switch.

## Inputs used

B1 uses the Lab 3 A1–A3 values (β = 100). B2–B8 use the handout CE fixture:
VCC 12 V, R1 100 kΩ, R2 22 kΩ, RC 2.2 kΩ, RE 1 kΩ (2 kΩ only in B3 after),
β = 150, analytical VBE = 0.7 V, RL 10 kΩ, Cin/Cout 10 µF, source 10 mV peak
at 1 kHz (20 mV only in B6 after). These are typed into the form; the page's
initial defaults are different, so defaults were not relied on.

## Results

| Case | Expected / reference | Observed in real browser (units) | Status | Evidence |
| --- | --- | --- | --- | --- |
| **B1 Divider** | Lab 3 A1: IC 1.229858 mA, VCE 8.052155 V, heading `Voltage-divider bias` | IC **1.2299 mA**, VCE **8.052 V**; ΔIC +0.000042 mA, ΔVCE −0.000155 V; heading `DC Operating Point · Voltage-divider bias` | **PASS** | `B1-fresh.yml`, `B1-divider-before-calculate.yml`, `B1-divider-updated.yml`, [`B1-divider.png`](evidence/B1-divider.png) |
| **B1 Fixed** | Lab 3 A2: IC 1.130000 mA, VCE 9.514000 V, fixed heading | IC **1.1300 mA**, VCE **9.514 V**, VE 0.000 V; Δ = 0; heading `DC Operating Point · Fixed bias` | **PASS** | `B1-fixed-before-calculate.yml`, `B1-fixed-updated.yml`, [`B1-fixed.png`](evidence/B1-fixed.png) |
| **B1 Emitter** | Lab 3 A3: IC 1.026340 mA, VCE 8.705450 V, emitter heading | IC **1.0263 mA**, VCE **8.705 V**, VE 1.037 V; ΔIC −0.000040 mA, ΔVCE −0.000450 V; heading `DC Operating Point · Emitter bias` | **PASS** | `B1-emitter-before-calculate.yml`, `B1-emitter-updated.yml`, [`B1-emitter.png`](evidence/B1-emitter.png) |
| **B2 DC SPICE** | Recorded ngspice run: VB 2.013016 V, VE 1.352006 V, VC 9.044000 V, VCE 7.691994 V, IC 1.344126 mA | Badge `Simulation complete`, `DC operating point`, exit code 0; VB **2.013016 V**, VE **1.352006 V**, VC **9.044000 V**, VCE **7.691994 V**, IC **1.344126 mA**; all deltas 0 | **PASS** | `B2-fresh.yml`, `B2-updated.yml`, [`B2-dc-spice.png`](evidence/B2-dc-spice.png), `B2-netlist.txt`, `B2-log.txt` in the raw report |
| **B3 Change RE** | Only RE 1000 → 2000 Ω; independent analytical direction: IC 1.299098 → 0.686149 mA, VCE 7.834226 → 9.109026 V, gain decreases | DC: IC **1.344126 → 0.715678 mA**, VCE **7.691994 → 8.985421 V**. AC midband gain **4.895 → −1.112 dB**. Netlist `RE emit 0 1000` → `RE emit 0 2000`; AC PNG SHA256 `9a21d8…` → `2f18ae…` | **PASS** | [`B3-before_re1000_ac.png`](evidence/B3-before_re1000_ac.png), [`B3-after_re2000_ac.png`](evidence/B3-after_re2000_ac.png), snapshots/netlists/logs in raw report |
| **B4 AC / Bode** | Real `.ac dec 20 1 10Meg`; midband 4.895 dB, lower −3 dB 1.3097692877710334 Hz, upper `not determined in sweep range`, gain ref `V(output) / V(base)`, phase from `vp()` in degrees | Same four displayed rows with correct units (`dB`, `Hz`, `—`). Netlist contains `.print ac vdb(output)`, `vp(output)`, `vdb(base)`, `vp(base)`. Browser log excerpt parsed 36 numeric rows; full-run phase at midband −179.735° is recorded in the AC section above. Plot PNG 868×648, SHA256 `9a21d8df…` | **PASS** | `B4-updated.yml`, [`B4-ac-bode.png`](evidence/B4-ac-bode.png), `B4-netlist.txt`, `B4-log.txt` in the raw report |
| **B5 Transient** | Real `.tran 10u 5m 0 10u`; 508 samples, 5.000 ms, 10 mV peak at 1 kHz, inversion | `Transient samples` **508 points**, `Time span` **5.000 ms**, input `V(input) before Cin`, output `V(output) across RL`. Excerpt peaks |Vin| **0.00999845 V**, |Vout| **0.01758687 V**; Vin/Vout correlation **−0.999999** (180° inversion). Plot SHA256 `316ac0ff…` | **PASS** | `B5-updated.yml`, [`B5-tran-waveform.png`](evidence/B5-tran-waveform.png), `B5-netlist.txt`, `B5-log.txt` in the raw report |
| **B6 Change source** | Amplitude 10 → 20 mV peak at 1 kHz; waveform peaks roughly double and plot bytes change | Netlist `SIN(0 0.01 1000)` → `SIN(0 0.02 1000)`; peak Vin **0.00999845 → 0.01999690 V**, peak Vout **0.01758687 → 0.03518732 V**; both 508 points / 5.000 ms; correlation −0.999999 both runs; PNG SHA256 `316ac0ff…` → `75256a27…` | **PASS** | [`B6-source-10mv.png`](evidence/B6-source-10mv.png), [`B6-source-20mv.png`](evidence/B6-source-20mv.png), netlists/logs in raw report |
| **B7a Invalid RE** | RE = 0 Ω → visible field error, no hang, no fake success/plot | Field error **"RE must be greater than 0."**, no `Simulation complete` badge, plot absent | **PASS** | `B7a-updated.yml`, [`B7-invalid-re.png`](evidence/B7-invalid-re.png) |
| **B7b Engine fail** | Explicit invalid `NGSPICE_PATH` → visible error with path, no plot | Badge `Simulation error`; message `ngspice not found at NGSPICE_PATH: C:\nope\ngspice.exe`; detail `Set NGSPICE_PATH to the ngspice_con.exe executable or leave it unset.`; plot absent | **PASS** | `B7b-updated.yml`, [`B7-engine-fail.png`](evidence/B7-engine-fail.png). Separate Flask on port 5001, stopped after the run |
| **B8 Desktop 1280×800** | No critical clipping, graph/units/buttons readable, mode switch works | viewport/scrollWidth **1280/1280**; AC plot 868×648 in a 772 px container (no scroll needed); switch to Emitter → `DC Operating Point · Emitter bias`, no field errors | **PASS** | `B8-desktop-ac-updated.yml`, [`B8-desktop-ac.png`](evidence/B8-desktop-ac.png) |
| **B8 Mobile 390×844** | Same content at phone width; graph may use its intended scroll container | viewport/scrollWidth **390/390**; buttons full-width 348 px; plot container client 346 px / scroll 629 px (intentional horizontal plot scroll); switch to Fixed → `DC Operating Point · Fixed bias`, no field errors | **PASS** | `B8-mobile-ac-updated.yml`, [`B8-mobile-ac.png`](evidence/B8-mobile-ac.png) |

All B1–B8 subcases were **PASS** in the final run.

## First finding and correction

The first B1 divider run used β = 150 (the app's default) and produced
IC 1.2991 mA / VCE 7.834 V, which failed against the Lab 3 A1 reference. This
was an input mistake in the acceptance script, not an application defect: the
handout asks for the original Lab 3 value set. The script was corrected to
β = 100 and B1 was rerun; the three B1 rows above are from that rerun. No code
was changed.

## Why B4/B5/B6 are real runs, not mock plots

- **B4:** the shown netlist contains `.ac dec 20 1 10Meg` and four `.print ac`
  tables; the browser log excerpt contains real numeric rows; the PNG is
  generated from parsed arrays. The full run recorded earlier in this file has
  141 AC points, while the browser `<details>` intentionally shows only the
  last 1500 characters (36 numeric rows in that excerpt).
- **B5:** the shown netlist contains `.tran 10u 5m 0 10u` and
  `.print tran v(input) v(output)`; the table reports 508 parsed samples and
  5.000 ms; the log excerpt's final rows run from `t = 4.732800e-03` to
  `5.000000e-03 s` with Vin/Vout columns and give correlation −0.999999.
- **B6:** changing only the form amplitude changed the `SIN(0 …)` netlist line,
  the parsed log peaks, and the PNG hash. A fixed/mock trace could not change
  all three.
- **B3 (supporting):** changing only RE changed the netlist line, DC operating
  point, AC gain, and AC PNG hash in the expected direction.

## UI before/after

The UI polish commit `51b14b1` changed grouping, provenance chips, error
callouts and responsive layout; it did not change equations, netlist, parser or
plot data. Before/after browser screenshots:
[`ui-before-desktop-ac.png`](evidence/ui-before-desktop-ac.png) →
[`ui-after-desktop-ac.png`](evidence/ui-after-desktop-ac.png) and
[`ui-before-mobile-ac.png`](evidence/ui-before-mobile-ac.png) →
[`ui-after-mobile-ac.png`](evidence/ui-after-mobile-ac.png).

The `impeccable` skill was not exposed in this harness, so the UI review and
polish were done manually against the handout's readability criteria; the
before/after screenshots are the evidence, not a claim that that skill ran.

## Limitations kept visible

- Playwright MCP was unavailable; the accepted browser is local
  Playwright 1.65.1 + Chrome channel, not MCP. This is stated rather than
  disguised.
- The page shows only the last 1500 characters of the ngspice log. Browser B5
  peak |Vout| is 0.01758687 V from that excerpt; the earlier full-run value is
  0.01758797 V, a 1.1×10⁻⁶ V difference caused by the truncated excerpt, well
  inside the 2×10⁻⁶ V acceptance tolerance used here.
- B7b used a second Flask instance with an explicitly broken `NGSPICE_PATH`;
  it was a real browser run, but not against the default port 5000 instance.
- B4's phase is plotted from real `vp()` tables and converted in Python; the
  page has no separate numeric phase row.
- Mobile B8 uses the designed horizontal scroll inside the plot container;
  the page itself has no horizontal overflow.

## Reproduce

```powershell
.\.venv\Scripts\python.exe -m flask --app app run --port 5000
```

Open <http://127.0.0.1:5000/>, type the fixture values listed above, select
`dc`/`ac`/`tran`, then press **Run Simulation**. The netlist and log are in the
page's `<details>` sections. Full machine-readable observations are in
[`evidence/B1-B8-report.json`](evidence/B1-B8-report.json).

## Commits

Lab 4 implementation: `402217e` (ngspice adapter), `8b63078` (web SPICE runs
and plots), engine/parser review fixes through `8e64fbf`, UI polish `51b14b1`.
Repository: <https://github.com/SentineI1/GitLab>.

## Test suite after the acceptance pass

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -t .
```

```
Ran 70 tests
OK
```

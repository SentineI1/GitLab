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
Ran 70 tests in 1.509s
OK
```

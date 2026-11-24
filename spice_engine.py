"""ngspice adapter for the reference CE voltage-divider amplifier.

The module owns exactly three things: build a netlist from validated values,
run ngspice as an external process, and parse the ``.print`` tables it emits.
It never invents a result: a missing table, an ``Error:`` line, a bad exit code
or a timeout all raise :class:`SimulationError` with the engine detail intact.

Units in the returned data follow the project convention: volts, milliamps,
hertz, seconds, decibels and degrees.
"""

from __future__ import annotations

import math
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

__all__ = [
    "CUTOFF_TEXT",
    "RunResult",
    "SimulationError",
    "build_netlist",
    "check_run",
    "cutoff_frequencies",
    "parse_ac",
    "parse_op",
    "parse_tran",
    "resolve_ngspice",
    "run",
    "simulate",
]

CIN = "10u"
COUT = "10u"
RL = "10k"
CUTOFF_TEXT = "not determined in sweep range"
MODEL = ".model CEQ NPN(IS=1E-14 BF={beta:g} VAF=100)"

_REPO_BINARY = (
    Path(__file__).resolve().parent
    / "tools"
    / "ngspice"
    / "Spice64"
    / "bin"
    / "ngspice_con.exe"
)
_ANALYSES = ("dc", "ac", "tran")
_ERROR_RE = re.compile(r"(?im)^\s*(?:error|fatal error):|run simulation\(s\) aborted")


class SimulationError(Exception):
    """A user-facing engine failure with the raw engine detail attached."""

    def __init__(self, message: str, detail: str = "") -> None:
        super().__init__(message)
        self.detail = detail


@dataclass(frozen=True)
class RunResult:
    analysis: str
    netlist: str
    stdout: str
    returncode: int
    exe: str


def _num(value: float) -> str:
    return f"{float(value):g}"


def resolve_ngspice() -> str:
    """Find the console ngspice binary; an explicit env override is final."""
    override = os.environ.get("NGSPICE_PATH")
    if override:
        if os.path.isfile(override) and os.access(override, os.X_OK):
            return override
        raise SimulationError(
            f"ngspice not found at NGSPICE_PATH: {override}",
            "Set NGSPICE_PATH to the ngspice_con.exe executable or leave it unset.",
        )

    candidates = [
        str(_REPO_BINARY),
        shutil.which("ngspice_con.exe") or "",
        shutil.which("ngspice") or "",
    ]
    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            return candidate
    raise SimulationError(
        "ngspice executable not found",
        "Tried: " + ", ".join(c for c in candidates if c) + f" (repo path: {_REPO_BINARY})",
    )


def check_run(result: RunResult) -> None:
    """Raise on any engine-reported failure, including exit code 0 with Error:."""
    excerpt = result.stdout[-1500:]
    if result.returncode != 0:
        raise SimulationError(
            f"ngspice exited with code {result.returncode}", excerpt
        )
    if _ERROR_RE.search(result.stdout):
        raise SimulationError("ngspice reported an error in its output", excerpt)


def build_netlist(analysis: str, values: Mapping[str, float]) -> str:
    """Build one analysis netlist for the reference CE voltage divider."""
    if analysis not in _ANALYSES:
        raise SimulationError(f"unknown analysis: {analysis!r}")

    amplitude_v = float(values["amplitude_mv"]) / 1000.0
    frequency = float(values["frequency_hz"])
    source = f"Vs input 0 DC 0 AC {_num(amplitude_v)} SIN(0 {_num(amplitude_v)} {_num(frequency)})"

    lines = [
        "* CE voltage-divider amplifier, reference circuit",
        f"VCC vcc 0 DC {_num(values['vcc'])}",
        f"R1 vcc base {_num(values['r1'])}",
        f"R2 base 0 {_num(values['r2'])}",
        f"RC vcc collect {_num(values['rc'])}",
        f"RE emit 0 {_num(values['re'])}",
        "Q1 collect base emit CEQ",
        MODEL.format(beta=float(values["beta"])),
        f"Cin input base {CIN}",
        f"Cout collect output {COUT}",
        f"RL output 0 {RL}",
        source,
    ]

    if analysis == "dc":
        lines += [".op", ".print op v(base) v(emit) v(collect) @q1[ic]"]
    elif analysis == "ac":
        lines += [
            ".ac dec 20 1 10Meg",
            ".print ac vdb(output)",
            ".print ac vp(output)",
            ".print ac vdb(base)",
            ".print ac vp(base)",
        ]
    else:
        step = "10u" if frequency <= 1000 else _num(max(1e-9, 1.0 / (frequency * 20)))
        lines += [
            f".tran {step} 5m 0 {step}",
            ".print tran v(input) v(output)",
        ]

    lines.append(".end")
    return "\n".join(lines) + "\n"


def run(
    analysis: str,
    values: Mapping[str, float],
    exe: str | None = None,
    timeout: int = 20,
) -> RunResult:
    """Execute one netlist in a temp directory and capture its console output."""
    netlist = build_netlist(analysis, values)
    executable = exe or resolve_ngspice()
    with tempfile.TemporaryDirectory(prefix="ce-ngspice-") as directory:
        netlist_path = Path(directory) / "ce.cir"
        netlist_path.write_text(netlist, encoding="utf-8")
        try:
            process = subprocess.run(
                [executable, "-b", str(netlist_path)],
                cwd=directory,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise SimulationError(
                f"ngspice timed out after {timeout} s", str(exc)
            ) from exc
        except OSError as exc:
            raise SimulationError(f"could not start ngspice: {exc}", executable) from exc
        output = (process.stdout or "") + "\n" + (process.stderr or "")
        return RunResult(analysis, netlist, output, process.returncode, executable)


def _excerpt(text: str) -> str:
    return text[-1500:]


def parse_table(text: str, marker: str) -> list[list[float]]:
    """Read one numeric ``Index ...`` table identified by its header marker."""
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if not line.lstrip().startswith("Index") or marker not in line:
            continue
        rows: list[list[float]] = []
        for raw in lines[index + 1 :]:
            stripped = raw.strip()
            if not stripped or stripped.startswith("---"):
                continue
            try:
                rows.append([float(part) for part in stripped.split()])
            except ValueError:
                break
        if not rows:
            raise SimulationError(f"ngspice table {marker!r} is empty", _excerpt(text))
        return rows
    raise SimulationError(f"ngspice table {marker!r} is missing", _excerpt(text))


def _column(rows: list[list[float]], column: int, marker: str) -> list[float]:
    try:
        return [row[column] for row in rows]
    except IndexError as exc:
        raise SimulationError(
            f"ngspice table {marker!r} has too few columns", _excerpt(str(rows))
        ) from exc


def parse_op(text: str) -> dict:
    rows = parse_table(text, "v(base)")
    if len(rows) != 1:
        raise SimulationError("DC table must contain one operating point", _excerpt(text))
    row = rows[0]
    if len(row) < 5:
        raise SimulationError("DC table is missing v(base)/v(emit)/v(collect)/@q1[ic]", _excerpt(text))
    vb, ve, vc, ic = row[1], row[2], row[3], row[4]
    return {
        "vb_v": vb,
        "ve_v": ve,
        "vc_v": vc,
        "vce_v": vc - ve,
        "ic_ma": ic * 1000.0,
    }


def _interpolate(f1: float, g1: float, f2: float, g2: float, target: float) -> float:
    if g2 == g1 or f1 <= 0 or f2 <= 0:
        return f1
    fraction = (target - g1) / (g2 - g1)
    return 10 ** (math.log10(f1) + fraction * (math.log10(f2) - math.log10(f1)))


def cutoff_frequencies(
    frequencies: Sequence[float], gain_db: Sequence[float]
) -> tuple[float | None, float | None]:
    """Find -3 dB crossings relative to the midband maximum, if they exist."""
    if len(frequencies) < 2 or len(frequencies) != len(gain_db):
        return None, None
    target = max(gain_db) - 3.0
    low = high = None
    for i in range(1, len(gain_db)):
        before, after = gain_db[i - 1], gain_db[i]
        f_before, f_after = frequencies[i - 1], frequencies[i]
        if before < target <= after:
            low = _interpolate(f_before, before, f_after, after, target)
        if before >= target > after:
            high = _interpolate(f_before, before, f_after, after, target)
    return low, high


def parse_ac(text: str) -> dict:
    out_db = parse_table(text, "vdb(output)")
    out_phase = parse_table(text, "vp(output)")
    base_db = parse_table(text, "vdb(base)")
    base_phase = parse_table(text, "vp(base)")
    frequencies = _column(out_db, 1, "vdb(output)")
    if not all(len(table) == len(out_db) for table in (out_phase, base_db, base_phase)):
        raise SimulationError("AC tables have different point counts", _excerpt(text))

    # AC tables carry [index, frequency, value]; the value is column 2.
    gain_db = [
        out - base
        for out, base in zip(
            _column(out_db, 2, "vdb(output)"), _column(base_db, 2, "vdb(base)")
        )
    ]
    phase_deg = [
        ((out - base) * 180.0 / math.pi + 180.0) % 360.0 - 180.0
        for out, base in zip(
            _column(out_phase, 2, "vp(output)"), _column(base_phase, 2, "vp(base)")
        )
    ]
    low, high = cutoff_frequencies(frequencies, gain_db)
    return {
        "frequency_hz": frequencies,
        "gain_db": gain_db,
        "phase_deg": phase_deg,
        "midband_gain_db": max(gain_db),
        "f_low_hz": CUTOFF_TEXT if low is None else low,
        "f_high_hz": CUTOFF_TEXT if high is None else high,
        "vin_node": "base",
        "vout_node": "output",
    }


def parse_tran(text: str) -> dict:
    rows = parse_table(text, "v(input)")
    return {
        "time_s": _column(rows, 1, "v(input)"),
        "vin_v": _column(rows, 2, "v(input)"),
        "vout_v": _column(rows, 3, "v(input)"),
    }


def simulate(
    analysis: str,
    values: Mapping[str, float],
    exe: str | None = None,
    timeout: int = 20,
) -> dict:
    """Build, run, validate and parse one analysis in a single call."""
    result = run(analysis, values, exe=exe, timeout=timeout)
    check_run(result)
    parsers = {"dc": parse_op, "ac": parse_ac, "tran": parse_tran}
    data = parsers[analysis](result.stdout)
    return {
        "status": "success",
        "analysis": analysis,
        "netlist": result.netlist,
        "log": result.stdout,
        "model": MODEL.format(beta=float(values["beta"])),
        "exe": result.exe,
        "returncode": result.returncode,
        "data": data,
    }

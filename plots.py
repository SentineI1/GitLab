"""Render parsed ngspice arrays as PNG data URIs.

The plotting layer never synthesizes points: every value drawn here comes from
the ``.print`` tables parsed by :mod:`spice_engine`. If a figure cannot be
drawn, the renderer returns ``None`` so the page can say "plot unavailable"
while still showing the real numbers and the engine log.
"""

from __future__ import annotations

import base64
import io
import logging

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt  # noqa: E402  (Agg must be selected first)

__all__ = ["ac_plot", "tran_plot", "tran_window"]

_LOGGER = logging.getLogger(__name__)


def _as_uri(fig) -> str:
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


def _crossings(data: dict) -> list[float]:
    values = []
    for key in ("f_low_hz", "f_high_hz"):
        value = data.get(key)
        if isinstance(value, (int, float)):
            values.append(float(value))
    return values


def ac_plot(data: dict) -> str | None:
    """Gain/phase versus frequency, both from the real AC sweep arrays."""
    fig = None
    try:
        frequencies = data["frequency_hz"]
        gain_db = data["gain_db"]
        phase_deg = data["phase_deg"]

        fig, (gain_ax, phase_ax) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
        gain_ax.semilogx(
            frequencies, gain_db, color="#1f6feb",
            label="ngspice: 20 log10 |V(output)/V(base)|",
        )
        gain_ax.set_ylabel("Gain (dB)")
        gain_ax.set_title("AC response — ngspice, model CEQ")
        gain_ax.grid(True, which="both", alpha=0.3)
        gain_ax.legend(loc="lower left", fontsize=8)

        phase_ax.semilogx(
            frequencies, phase_deg, color="#b54708",
            label="ngspice: phase of V(output)/V(base)",
        )
        phase_ax.set_xlabel("Frequency (Hz)")
        phase_ax.set_ylabel("Phase (deg)")
        phase_ax.grid(True, which="both", alpha=0.3)
        phase_ax.legend(loc="lower left", fontsize=8)

        for index, frequency in enumerate(_crossings(data)):
            label = "-3 dB crossing" if index == 0 else None
            for ax in (gain_ax, phase_ax):
                ax.axvline(frequency, color="#5b6570", linestyle="--",
                           linewidth=1, alpha=0.7, label=label)
            label = None

        fig.tight_layout()
        return _as_uri(fig)
    except Exception:
        _LOGGER.exception("could not render SPICE plot")
        if fig is not None:
            plt.close(fig)
        return None


def tran_window(data: dict) -> dict:
    """Select the first five source periods of real samples (no fabrication)."""
    times = data["time_s"]
    count = len(times)
    frequency = data.get("frequency_hz")
    if frequency and frequency > 0:
        limit = 5.0 / float(frequency)
        end = next((i for i, value in enumerate(times) if value > limit), count)
        end = max(1, min(end, count))
    else:
        end = count
    return {
        "time_s": times[:end],
        "vin_v": data["vin_v"][:end],
        "vout_v": data["vout_v"][:end],
    }


def tran_plot(data: dict) -> str | None:
    """Input and output waveforms versus time from the real transient samples."""
    fig = None
    try:
        window = tran_window(data)
        time_ms = [seconds * 1000.0 for seconds in window["time_s"]]
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(time_ms, window["vin_v"], color="#5b6570",
                label="ngspice: V(input), source side of Cin")
        ax.plot(time_ms, window["vout_v"], color="#1f6feb",
                label="ngspice: V(output), across RL")
        ax.set_xlabel("Time (ms)")
        ax.set_ylabel("Voltage (V)")
        ax.set_title("Transient waveforms — ngspice, model CEQ")
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)
        fig.tight_layout()
        return _as_uri(fig)
    except Exception:
        _LOGGER.exception("could not render SPICE plot")
        if fig is not None:
            plt.close(fig)
        return None

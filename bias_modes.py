"""Bias-mode solvers for the single-supply common-emitter stage.

Three bias networks share one transistor model: a fixed base-emitter drop
``VBE`` and ``IC = beta * IB``. Every solver returns a plain ``dict`` whose
keys carry their unit: ``*_ma`` for milliamps, ``*_v`` for volts, and
``*_ohm`` for ohms. The same key always means the same quantity, whatever
the mode, so the page can render one table for all three.

The divider solver delegates to :func:`bjt_bias.analyze`, so the original
divider numbers and the existing tests are untouched.
"""

from __future__ import annotations

from typing import Mapping

from bjt_bias import (
    ACTIVE_MESSAGE,
    BiasInputError,
    BiasInputs,
    CUTOFF_MESSAGE,
    SATURATION_MESSAGE,
    VCE_SAT_V,
    _parse_field,
    analyze,
    parse_inputs,
)

__all__ = [
    "FIELDS_BY_MODE",
    "MODES",
    "MODE_LABELS",
    "parse_for_mode",
    "solve",
    "solve_divider",
    "solve_emitter",
    "solve_fixed",
]

MODES = ("divider", "fixed", "emitter")

MODE_LABELS = {
    "divider": "Voltage-divider bias",
    "fixed": "Fixed bias",
    "emitter": "Emitter bias",
}

# The form fields each mode reads. Other submitted fields are ignored.
FIELDS_BY_MODE = {
    "divider": ("vcc", "r1", "r2", "rc", "re", "beta", "vbe"),
    "fixed": ("vcc", "rb", "rc", "beta", "vbe"),
    "emitter": ("vcc", "rb", "rc", "re", "beta", "vbe"),
}

_POSITIVE_LABELS = {
    "vcc": "VCC",
    "r1": "R1",
    "r2": "R2",
    "rb": "RB",
    "rc": "RC",
    "re": "RE",
    "beta": "beta",
}


def parse_for_mode(mode: str, form: Mapping[str, str]) -> dict[str, float]:
    """Validate one mode's fields and return them as floats in SI units.

    Only the fields in ``FIELDS_BY_MODE[mode]`` are read; anything else in
    the submitted form is ignored. Raises ``BiasInputError`` with one message
    per invalid field.
    """
    if mode not in MODES:
        raise ValueError(f"unknown bias mode: {mode!r}")

    if mode == "divider":
        inputs = parse_inputs(form)
        return {
            "vcc": inputs.vcc_v,
            "r1": inputs.r1_ohm,
            "r2": inputs.r2_ohm,
            "rc": inputs.rc_ohm,
            "re": inputs.re_ohm,
            "beta": inputs.beta,
            "vbe": inputs.vbe_v,
        }

    errors: dict[str, str] = {}
    values: dict[str, float] = {}

    for name in FIELDS_BY_MODE[mode]:
        if name == "vbe":
            continue
        number, message = _parse_field(form.get(name))
        if message is not None:
            errors[name] = message
        elif number <= 0:
            errors[name] = f"{_POSITIVE_LABELS[name]} must be greater than 0."
        else:
            values[name] = number

    vbe, message = _parse_field(form.get("vbe"))
    if message is not None:
        errors["vbe"] = message
    elif vbe <= 0:
        errors["vbe"] = "VBE must be greater than 0."
    elif "vcc" in values and vbe >= values["vcc"]:
        errors["vbe"] = "VBE must be less than VCC."
    else:
        values["vbe"] = vbe

    if errors:
        raise BiasInputError(errors)

    return values


def _classify(ib: float, vce: float) -> tuple[str, str]:
    """Classify a fixed/emitter solution with the divider's thresholds."""
    if ib <= 0:
        return "cutoff", CUTOFF_MESSAGE
    if vce < VCE_SAT_V:
        return "saturation", SATURATION_MESSAGE
    return "active", ACTIVE_MESSAGE


def _result(
    mode: str,
    ib: float,
    ic: float,
    ie: float,
    vb: float,
    vc: float,
    ve: float,
    vce: float,
) -> dict:
    """Build the unit-tagged result dict shared by the fixed/emitter modes."""
    region, message = _classify(ib, vce)
    return {
        "mode": mode,
        "ib_ma": ib * 1000.0,
        "ic_ma": ic * 1000.0,
        "ie_ma": ie * 1000.0,
        "vb_v": vb,
        "vc_v": vc,
        "ve_v": ve,
        "vce_v": vce,
        "region": region,
        "message": message,
    }


def solve_divider(values: Mapping[str, float]) -> dict:
    """Voltage-divider bias, produced by the original ``bjt_bias.analyze``."""
    result = analyze(
        BiasInputs(
            vcc_v=values["vcc"],
            r1_ohm=values["r1"],
            r2_ohm=values["r2"],
            rc_ohm=values["rc"],
            re_ohm=values["re"],
            beta=values["beta"],
            vbe_v=values["vbe"],
        )
    )
    return {
        "mode": "divider",
        "vbb_v": result.vbb_v,
        "rb_ohm": result.rb_ohm,
        "ib_ma": result.ib_ma,
        "ic_ma": result.ic_ma,
        "ie_ma": result.ie_ma,
        "vb_v": result.vb_v,
        "vc_v": result.vc_v,
        "ve_v": result.ve_v,
        "vce_v": result.vce_v,
        "region": result.region,
        "message": result.message,
    }


def solve_fixed(values: Mapping[str, float]) -> dict:
    """Fixed bias: RB from VCC to base, RC to collector, emitter grounded."""
    vcc = values["vcc"]
    rb = values["rb"]
    rc = values["rc"]
    beta = values["beta"]
    vbe = values["vbe"]

    ib = (vcc - vbe) / rb
    ic = beta * ib
    ie = (1.0 + beta) * ib
    ve = 0.0
    vb = vbe
    vc = vcc - ic * rc
    return _result("fixed", ib, ic, ie, vb, vc, ve, vc - ve)


def solve_emitter(values: Mapping[str, float]) -> dict:
    """Emitter bias: RB from VCC to base, RE to ground, RC to collector."""
    vcc = values["vcc"]
    rb = values["rb"]
    rc = values["rc"]
    re = values["re"]
    beta = values["beta"]
    vbe = values["vbe"]

    ib = (vcc - vbe) / (rb + (1.0 + beta) * re)
    ic = beta * ib
    ie = (1.0 + beta) * ib
    ve = ie * re
    vb = ve + vbe
    vc = vcc - ic * rc
    return _result("emitter", ib, ic, ie, vb, vc, ve, vc - ve)


def solve(mode: str, values: Mapping[str, float]) -> dict:
    """Solve one mode; ``mode`` must be one of :data:`MODES`."""
    return {
        "divider": solve_divider,
        "fixed": solve_fixed,
        "emitter": solve_emitter,
    }[mode](values)

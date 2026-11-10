"""Input validation and DC bias analysis for the BJT common-emitter circuit.

`parse_inputs` turns the raw form mapping submitted by the browser into a
validated `BiasInputs` record. Every bad field is reported in a single
`BiasInputError` so the user can fix them all at once.

`analyze` solves the operating point with the Thevenin equivalent of the
base divider and classifies the transistor as active, cutoff, or saturated.
"""

import math
from dataclasses import dataclass
from typing import Mapping

__all__ = [
    "BiasInputError",
    "BiasInputs",
    "BiasResult",
    "VCE_SAT_V",
    "analyze",
    "parse_inputs",
]

# Form field names, in the order they appear in the form.
FIELDS = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")

# Fields that must be strictly positive, with the label used in the message.
POSITIVE_FIELDS = (
    ("vcc", "VCC"),
    ("r1", "R1"),
    ("r2", "R2"),
    ("rc", "RC"),
    ("re", "RE"),
    ("beta", "beta"),
)

BLANK_MESSAGE = "Enter a value."
NUMBER_MESSAGE = "Enter a finite number."

# Collector-emitter voltage below which the transistor is saturated.
VCE_SAT_V = 0.2

CUTOFF_MESSAGE = (
    "Cutoff: the base-emitter junction is not forward biased; the transistor is off."
)
SATURATION_MESSAGE = (
    "Saturation: VCE is below VCE(sat); "
    "the active-region result is not the true operating point."
)
ACTIVE_MESSAGE = "Active: the transistor is in the active region."


class BiasInputError(ValueError):
    """Raised when one or more form fields fail validation.

    `errors` maps a form field name (`vcc`, `r1`, ...) to the message that
    belongs next to that field.
    """

    def __init__(self, errors: Mapping[str, str]) -> None:
        self.errors = dict(errors)
        super().__init__(
            "; ".join(f"{name}: {message}" for name, message in self.errors.items())
        )


@dataclass(frozen=True)
class BiasInputs:
    """Validated circuit inputs, in SI units (volts, ohms)."""

    vcc_v: float
    r1_ohm: float
    r2_ohm: float
    rc_ohm: float
    re_ohm: float
    beta: float
    vbe_v: float


def _parse_field(raw: object) -> tuple[float | None, str | None]:
    """Return (number, error message) for one submitted field value.

    The number is None when the field is blank, not a number, or not finite.
    """
    text = "" if raw is None else str(raw).strip()
    if not text:
        return None, BLANK_MESSAGE
    try:
        number = float(text)
    except ValueError:
        return None, NUMBER_MESSAGE
    if not math.isfinite(number):
        return None, NUMBER_MESSAGE
    return number, None


def parse_inputs(form: Mapping[str, str]) -> BiasInputs:
    """Validate a submitted form and return the parsed inputs.

    Raises `BiasInputError` holding one message per invalid field.
    """
    errors: dict[str, str] = {}
    values: dict[str, float] = {}

    for name in FIELDS:
        number, message = _parse_field(form.get(name))
        if message is not None:
            errors[name] = message
        else:
            values[name] = number

    for name, label in POSITIVE_FIELDS:
        number = values.get(name)
        if number is not None and number <= 0:
            errors[name] = f"{label} must be greater than 0."

    vbe = values.get("vbe")
    if vbe is not None:
        if vbe <= 0:
            errors["vbe"] = "VBE must be greater than 0."
        else:
            # The upper bound is only meaningful once VCC has parsed.
            vcc = values.get("vcc")
            if vcc is not None and vbe >= vcc:
                errors["vbe"] = "VBE must be less than VCC."

    if errors:
        raise BiasInputError(errors)

    return BiasInputs(
        vcc_v=values["vcc"],
        r1_ohm=values["r1"],
        r2_ohm=values["r2"],
        rc_ohm=values["rc"],
        re_ohm=values["re"],
        beta=values["beta"],
        vbe_v=values["vbe"],
    )


@dataclass(frozen=True)
class BiasResult:
    """Solved operating point of the common-emitter stage.

    Currents are in mA, voltages in volts, and `rb_ohm` in ohms. `region` is
    one of "active", "cutoff", or "saturation"; `message` explains that choice
    for the user.
    """

    vbb_v: float
    rb_ohm: float
    ib_ma: float
    ic_ma: float
    ie_ma: float
    vb_v: float
    vc_v: float
    ve_v: float
    vce_v: float
    region: str
    message: str


def analyze(inputs: BiasInputs) -> BiasResult:
    """Solve the DC operating point and classify the transistor region.

    The base divider is replaced by its Thevenin equivalent (VBB, RB) and the
    base loop is solved with the beta model of the transistor. The resulting
    VCE is then checked against `VCE_SAT_V` to classify the region. No value
    is clamped: outside the active region the numbers are the raw solution of
    the same equations, and the message says so.
    """
    vcc = inputs.vcc_v
    r1 = inputs.r1_ohm
    r2 = inputs.r2_ohm
    rc = inputs.rc_ohm
    re = inputs.re_ohm
    beta = inputs.beta
    vbe = inputs.vbe_v

    vbb = vcc * r2 / (r1 + r2)
    rb = r1 * r2 / (r1 + r2)
    ib = (vbb - vbe) / (rb + (1 + beta) * re)
    ic = beta * ib
    ie = (1 + beta) * ib
    ve = ie * re
    vb = ve + vbe
    vc = vcc - ic * rc
    vce = vc - ve

    if vbb <= vbe:
        region = "cutoff"
        message = CUTOFF_MESSAGE
    elif vce < VCE_SAT_V:
        region = "saturation"
        message = SATURATION_MESSAGE
    else:
        region = "active"
        message = ACTIVE_MESSAGE

    return BiasResult(
        vbb_v=vbb,
        rb_ohm=rb,
        ib_ma=ib * 1000,
        ic_ma=ic * 1000,
        ie_ma=ie * 1000,
        vb_v=vb,
        vc_v=vc,
        ve_v=ve,
        vce_v=vce,
        region=region,
        message=message,
    )

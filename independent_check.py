"""Independent cross-check of the BJT bias operating point.

`bjt_bias.analyze` reduces the base divider to a Thevenin equivalent and then
solves one base loop. `independent_check.solve` instead writes Kirchhoff's
current law straight into the base node. The two paths share no algebra, so
agreement between them is evidence that the operating point is right.

Only the `BiasInputs` type is shared with `bjt_bias`, and only for typing:
the import below is never executed at runtime, so this module has no runtime
dependency on the module it is checking.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only, never imported at runtime
    from bjt_bias import BiasInputs

__all__ = [
    "CURRENT_FLOOR_MA",
    "RELATIVE_TOLERANCE",
    "VOLTAGE_FLOOR_V",
    "Comparison",
    "IndependentResult",
    "compare",
    "solve",
]

# Absolute floors below which a value counts as zero. Currents are compared in
# mA and voltages in volts, so the two floors are not the same number.
CURRENT_FLOOR_MA = 1e-9
VOLTAGE_FLOOR_V = 1e-12

# Relative tolerance applied to values above the floor.
RELATIVE_TOLERANCE = 1e-6


@dataclass(frozen=True)
class IndependentResult:
    """Operating point from the base-node KCL solve.

    `ic_ma` is in mA; every other field is in volts.
    """

    ic_ma: float
    vce_v: float
    vb_v: float
    ve_v: float
    vc_v: float


@dataclass(frozen=True)
class Comparison:
    """Difference between the Thevenin solve and the base-node KCL solve.

    `ic_delta_ma` is in mA and `vce_delta_v` in volts; the `*_relative` fields
    are dimensionless ratios. The `*_match` flags say whether the two methods
    agree within tolerance.
    """

    ic_delta_ma: float
    ic_relative: float
    vce_delta_v: float
    vce_relative: float
    ic_match: bool
    vce_match: bool


def solve(inputs: BiasInputs) -> IndependentResult:
    """Solve the operating point from the base-node KCL equation.

    The base-emitter branch is seen from the base node as the VBE source in
    series with `(1 + beta) * RE`: the base current flowing through that
    branch drops `(1 + beta) * RE` volts across RE, because the emitter
    current is `(1 + beta)` times the base current. Writing KCL at the base
    node therefore gives

        (VCC - VB) / R1 = VB / R2 + (VB - VBE) / ((1 + beta) * RE)

    which is solved below for VB. The remaining node voltages follow from the
    branch currents. Nothing is clamped: outside the active region the
    numbers are the raw solution of these equations, exactly as in the
    Thevenin path, so the two methods stay comparable.
    """
    vcc = inputs.vcc_v
    r1 = inputs.r1_ohm
    r2 = inputs.r2_ohm
    rc = inputs.rc_ohm
    re = inputs.re_ohm
    beta = inputs.beta
    vbe = inputs.vbe_v

    base_branch_ohm = (1.0 + beta) * re

    # KCL at the base node, written with conductances.
    conductance_sum = 1.0 / r1 + 1.0 / r2 + 1.0 / base_branch_ohm
    vb = (vcc / r1 + vbe / base_branch_ohm) / conductance_sum

    ve = vb - vbe
    ie = ve / re
    ib = ie / (1.0 + beta)
    ic = beta * ib
    vc = vcc - ic * rc
    vce = vc - ve

    return IndependentResult(
        ic_ma=ic * 1000.0,
        vce_v=vce,
        vb_v=vb,
        ve_v=ve,
        vc_v=vc,
    )


def _compare_pair(a: float, b: float, floor: float) -> tuple[float, float, bool]:
    """Compare two numbers against an absolute floor.

    Returns `(delta, relative, match)`. Two values match when both are at or
    below the floor (they are both zero for practical purposes) or when their
    relative difference is within tolerance. The relative difference is 0.0
    when both values sit below the floor, because the ratio would be
    meaningless there.
    """
    delta = abs(a - b)
    if abs(a) <= floor and abs(b) <= floor:
        return delta, 0.0, True
    relative = delta / max(abs(a), abs(b))
    return delta, relative, relative <= RELATIVE_TOLERANCE


def compare(
    ic_ma_thevenin: float,
    ic_ma_nodal: float,
    vce_v_thevenin: float,
    vce_v_nodal: float,
) -> Comparison:
    """Compare the Thevenin solution with the base-node KCL solution.

    Currents are in mA and voltages in volts.
    """
    ic_delta, ic_relative, ic_match = _compare_pair(
        ic_ma_thevenin, ic_ma_nodal, CURRENT_FLOOR_MA
    )
    vce_delta, vce_relative, vce_match = _compare_pair(
        vce_v_thevenin, vce_v_nodal, VOLTAGE_FLOOR_V
    )
    return Comparison(
        ic_delta_ma=ic_delta,
        ic_relative=ic_relative,
        vce_delta_v=vce_delta,
        vce_relative=vce_relative,
        ic_match=ic_match,
        vce_match=vce_match,
    )

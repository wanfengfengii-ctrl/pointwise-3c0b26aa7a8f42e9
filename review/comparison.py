from fractions import Fraction

from calibration.evidence import FrozenEvidence


def count_qualifying_specimens(evidence: FrozenEvidence, candidate: Fraction) -> int:
    target_magnitude = abs(evidence.target.at(candidate))
    return 1 + sum(
        abs(residual.at(candidate)) >= target_magnitude for _, residual in evidence.originals
    )


def comparison_breakpoints(evidence: FrozenEvidence) -> tuple[Fraction, ...]:
    """Collect the exact points where the qualifying count can change.

    The count changes only where some original's residual magnitude ties the
    target's. With affine residuals r(c) = a + b*c, the tie |r(c)| = |t(c)|
    is the pair of linear equations r(c) == t(c) and r(c) == -t(c), each
    contributing at most one rational point. An original whose residual is
    identically ±the target's ties everywhere and adds no point.
    """
    target = evidence.target
    points = set()
    for _, residual in evidence.originals:
        for slope_delta, intercept_delta in (
            (residual.slope - target.slope, residual.intercept - target.intercept),
            (residual.slope + target.slope, residual.intercept + target.intercept),
        ):
            if slope_delta:
                points.add(-intercept_delta / slope_delta)
    return tuple(sorted(points))

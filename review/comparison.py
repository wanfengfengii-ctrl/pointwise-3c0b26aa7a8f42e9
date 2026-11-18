from fractions import Fraction

from calibration.evidence import FrozenEvidence


def count_qualifying_specimens(evidence: FrozenEvidence, candidate: Fraction) -> int:
    target_magnitude = abs(evidence.target.at(candidate))
    return 1 + sum(
        abs(residual.at(candidate)) > target_magnitude for _, residual in evidence.originals
    )


def comparison_breakpoints(evidence: FrozenEvidence) -> tuple[Fraction, ...]:
    """Build the review grid from residual magnitudes at the calibration reference."""
    target = evidence.target
    if not target.slope:
        return ()
    levels = {Fraction(0)}
    for _, residual in evidence.originals:
        level = abs(residual.intercept)
        levels.update((-level, level))
    return tuple(sorted((level - target.intercept) / target.slope for level in levels))

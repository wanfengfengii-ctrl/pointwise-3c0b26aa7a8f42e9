from dataclasses import dataclass
from fractions import Fraction

from calibration.design import CalibrationDesign
from calibration.least_squares import residual_vector
from protocol.rationals import RationalInput, parse_rational


@dataclass(frozen=True)
class AffineResidual:
    intercept: Fraction
    slope: Fraction

    def at(self, candidate: Fraction) -> Fraction:
        return self.intercept + self.slope * candidate


@dataclass(frozen=True)
class FrozenEvidence:
    originals: tuple[tuple[str, AffineResidual], ...]
    target: AffineResidual

    def __post_init__(self) -> None:
        identifiers = {specimen_id for specimen_id, _ in self.originals}
        if not identifiers or len(identifiers) != len(self.originals):
            raise ValueError("evidence needs at least one uniquely identified original specimen")

    @property
    def total_specimens(self) -> int:
        return len(self.originals) + 1

    def residuals_at(self, candidate: RationalInput) -> tuple[Fraction, ...]:
        value = parse_rational(candidate)
        return tuple(residual.at(value) for _, residual in self.originals) + (self.target.at(value),)


def build_evidence(design: CalibrationDesign) -> FrozenEvidence:
    # The projection is linear in the response, so each specimen's residual is
    # affine in the candidate: residual(c) = reference + c * influence, where
    # influence is the residual vector of the lone-target response. Every
    # specimen, not just the target, inherits its slope from the joint fit.
    reference = residual_vector(design.matrix, design.response_at(Fraction(0)))
    target_indicator = (Fraction(0),) * len(design.specimen_ids) + (Fraction(1),)
    influence = residual_vector(design.matrix, target_indicator)
    originals = tuple(
        (specimen_id, AffineResidual(intercept, slope))
        for specimen_id, intercept, slope in zip(
            design.specimen_ids, reference[:-1], influence[:-1]
        )
    )
    target = AffineResidual(reference[-1], influence[-1])
    return FrozenEvidence(originals, target)

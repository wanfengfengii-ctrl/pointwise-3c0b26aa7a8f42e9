from fractions import Fraction

from review.comparison import comparison_breakpoints, count_qualifying_specimens
from review.region_set import CandidateSet, ClosedRegion
from review.request import IssueRequest


def find_candidate_set(request: IssueRequest) -> CandidateSet:
    evidence = request.calibration.evidence
    if request.threshold == 1:
        return CandidateSet((ClosedRegion(None, None),))

    points = comparison_breakpoints(evidence)
    if not points:
        if count_qualifying_specimens(evidence, Fraction(0)) >= request.threshold:
            return CandidateSet((ClosedRegion(None, None),))
        return CandidateSet(())

    accepted = [
        point for point in points
        if count_qualifying_specimens(evidence, point) >= request.threshold
    ]
    if not accepted:
        return CandidateSet(())
    return CandidateSet((ClosedRegion(accepted[0], accepted[-1]),))

from fractions import Fraction

from review.comparison import comparison_breakpoints, count_qualifying_specimens
from review.region_set import CandidateSet, ClosedRegion
from review.request import IssueRequest


def find_candidate_set(request: IssueRequest) -> CandidateSet:
    evidence = request.calibration.evidence
    if request.threshold == 1:
        # The target always counts itself, so every candidate qualifies.
        return CandidateSet((ClosedRegion(None, None),))

    points = comparison_breakpoints(evidence)
    if not points:
        if count_qualifying_specimens(evidence, Fraction(0)) >= request.threshold:
            return CandidateSet((ClosedRegion(None, None),))
        return CandidateSet(())

    regions = []
    # The count is constant on each open piece between consecutive tie points,
    # so one rational probe decides the whole piece. A qualifying piece is
    # closed: the count at a tie point never drops below either neighbour, so
    # the piece's endpoints qualify as well and belong to its closure.
    probes = [points[0] - 1]
    probes.extend((left + right) / 2 for left, right in zip(points, points[1:]))
    probes.append(points[-1] + 1)
    bounds = (None, *points, None)
    for index, probe in enumerate(probes):
        if count_qualifying_specimens(evidence, probe) >= request.threshold:
            regions.append(ClosedRegion(bounds[index], bounds[index + 1]))
    # Tie points themselves: closed components keep boundary ties and any
    # isolated point whose neighbours fall below the threshold.
    for point in points:
        if count_qualifying_specimens(evidence, point) >= request.threshold:
            regions.append(ClosedRegion(point, point))
    if not regions:
        return CandidateSet(())
    return CandidateSet(tuple(regions))

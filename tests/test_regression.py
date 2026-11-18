import json
from fractions import Fraction as F

from calibration.evidence import AffineResidual, FrozenEvidence
from calibration.publish import freeze_calibration
from calibration.store import CalibrationStore
from cohort.retirement import retire_cohort
from handoff.export import export_report
from handoff.lookup import read_report
from handoff.transactions import write_transaction
from review.comparison import count_qualifying_specimens
from review.issue import issue_report
from review.region_set import ClosedRegion
from tests.support import DatabaseTestCase, measurement


class IncidentRegressionTests(DatabaseTestCase):
    """The shift-handoff accident: same-speed A=-1, B=1, k=2 must issue [-3,3]."""

    def freeze_incident(self):
        return self.freeze_line((0, 0), (-1, 1), 0)

    def test_incident_report(self):
        _, source_id, calibration_id = self.freeze_incident()
        retire_cohort(self.db, source_id)
        self.reopen()
        report = issue_report(self.db, calibration_id, 2)
        self.assertEqual(report.candidates.regions, (ClosedRegion(-3, 3),))
        exported = json.loads(export_report(self.db, report.report_id))
        self.assertEqual(exported["candidate_regions"], [[[-3, 1], [3, 1]]])
        membership = [candidate in report.candidates for candidate in (2, 3, 4)]
        self.assertEqual(membership, [True, True, False])
        self.assertEqual(read_report(self.db, report.report_id), report)

    def test_independent_sealed_copy_agrees(self):
        _, source_id, calibration_id = self.freeze_incident()
        first = export_report(self.db, issue_report(self.db, calibration_id, 2).report_id)
        retire_cohort(self.db, source_id)
        self.reopen()
        second = export_report(self.db, issue_report(self.db, calibration_id, 2).report_id)
        self.assertEqual(json.loads(first)["candidate_regions"], [[[-3, 1], [3, 1]]])
        self.assertEqual(
            json.loads(second)["candidate_regions"], json.loads(first)["candidate_regions"]
        )

    def test_frozen_evidence_recomputes_signed_residuals(self):
        _, _, calibration_id = self.freeze_incident()
        evidence = CalibrationStore(self.db).get_calibration(calibration_id).evidence
        # The candidate flows through the joint fit: originals keep slopes -1/3.
        self.assertEqual(
            evidence.originals,
            (
                ("A", AffineResidual(F(-1), F(-1, 3))),
                ("B", AffineResidual(F(1), F(-1, 3))),
            ),
        )
        self.assertEqual(evidence.target, AffineResidual(F(0), F(2, 3)))
        self.assertEqual(evidence.residuals_at(2), (F(-5, 3), F(1, 3), F(4, 3)))
        self.assertEqual(evidence.residuals_at(3), (F(-2), F(0), F(2)))
        self.assertEqual(evidence.residuals_at(F(1, 2)), (F(-7, 6), F(5, 6), F(1, 3)))

    def test_tied_boundary_counts_both_sides(self):
        _, _, calibration_id = self.freeze_incident()
        evidence = CalibrationStore(self.db).get_calibration(calibration_id).evidence
        # At candidate 3 the A and target magnitudes tie at 2; both count.
        self.assertEqual(count_qualifying_specimens(evidence, F(3)), 2)
        self.assertEqual(count_qualifying_specimens(evidence, F(2)), 2)
        self.assertEqual(count_qualifying_specimens(evidence, F(4)), 1)
        for k, expected in ((2, (ClosedRegion(-3, 3),)), (3, (ClosedRegion(-1, 1),))):
            with self.subTest(k=k):
                self.assertEqual(issue_report(self.db, calibration_id, k).candidates.regions, expected)


class RegionShapeTests(DatabaseTestCase):
    """Empty set, whole axis, and exact rational endpoints survive the pipeline."""

    def insert_evidence(self, originals, target):
        protocol_id, source_id = self.line_cohort()
        evidence = FrozenEvidence(tuple(originals), target)
        with write_transaction(self.db):
            calibration_id = CalibrationStore(self.db).insert_calibration(
                source_id, protocol_id, (F(0),), evidence
            )
        return calibration_id

    def test_empty_set(self):
        # The constant target residual 5 strictly dominates the zero original.
        calibration_id = self.insert_evidence(
            (("A", AffineResidual(F(0), F(0))),), AffineResidual(F(5), F(0))
        )
        report = issue_report(self.db, calibration_id, 2)
        self.assertEqual(report.candidates.regions, ())
        self.assertEqual(report.candidates.to_payload(), [])
        exported = json.loads(export_report(self.db, report.report_id))
        self.assertEqual(exported["candidate_regions"], [])
        self.assertNotIn(0, read_report(self.db, report.report_id).candidates)

    def test_whole_axis_from_vanishing_target(self):
        calibration_id = self.insert_evidence(
            (("A", AffineResidual(F(1), F(2))),), AffineResidual(F(0), F(0))
        )
        report = issue_report(self.db, calibration_id, 2)
        self.assertEqual(report.candidates.regions, (ClosedRegion(None, None),))
        exported = json.loads(export_report(self.db, report.report_id))
        self.assertEqual(exported["candidate_regions"], [[None, None]])

    def test_isolated_point_and_ray_keep_exact_endpoints(self):
        # Slopes 1 and -1 against the zero target tie only at the origin.
        calibration_id = self.insert_evidence(
            (("A", AffineResidual(F(0), F(1))), ("B", AffineResidual(F(0), F(-1)))),
            AffineResidual(F(0), F(0)),
        )
        report = issue_report(self.db, calibration_id, 3)
        self.assertEqual(report.candidates.regions, (ClosedRegion(None, None),))
        # A single dominant original leaves a closed ray with a rational end.
        calibration_id = self.insert_evidence(
            (("A", AffineResidual(F(1), F(1))),), AffineResidual(F(0), F(1))
        )
        report = issue_report(self.db, calibration_id, 2)
        self.assertEqual(report.candidates.regions, (ClosedRegion(F(-1, 2), None),))
        exported = json.loads(export_report(self.db, report.report_id))
        self.assertEqual(exported["candidate_regions"], [[[-1, 2], None]])

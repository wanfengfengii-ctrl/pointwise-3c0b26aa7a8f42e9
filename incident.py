import json
import sqlite3
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

from calibration.publish import freeze_calibration
from cohort.intake import record_cohort
from cohort.retirement import retire_cohort
from handoff.database import open_database
from handoff.export import export_report
from handoff.lookup import read_report
from protocol.catalog import register_protocol
from review.issue import issue_report


def check_report(db: sqlite3.Connection, calibration_id: int, threshold: int) -> int:
    report = issue_report(db, calibration_id, threshold)
    stored = read_report(db, report.report_id)
    exported = json.loads(export_report(db, report.report_id))
    expected = {
        "candidate_regions": [[[-3, 1], [3, 1]]],
        "membership_2_3_4": [True, True, False],
    }
    actual = {
        "candidate_regions": exported["candidate_regions"],
        "membership_2_3_4": [value in stored.candidates for value in (2, 3, 4)],
    }
    result = json.dumps({"actual": actual, "expected": expected}, sort_keys=True)
    if actual != expected:
        print("THICKNESS_SET_MISMATCH " + result)
        return 1
    print(result)
    return 0


def main() -> int:
    sample_path = Path(__file__).with_name("sample.json")
    sample = json.loads(sample_path.read_text(encoding="utf-8"))
    with TemporaryDirectory() as directory:
        path = Path(directory) / "lab.sqlite3"
        with closing(open_database(path)) as db:
            protocol_id = register_protocol(db, **sample["protocol"])
            source_id = record_cohort(db, protocol_id, sample["measurements"])
            calibration_id = freeze_calibration(db, source_id, sample["target_conditions"])
            retire_cohort(db, source_id)
        with closing(open_database(path)) as db:
            return check_report(db, calibration_id, sample["threshold"])


if __name__ == "__main__":
    raise SystemExit(main())

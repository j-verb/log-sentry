import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from log_sentry.analyzer import analyze
from log_sentry.cli import main
from log_sentry.journal import parse_entries


class ParseEntriesTests(unittest.TestCase):
    def test_parses_json_lines_and_skips_blank_lines(self):
        entries = parse_entries(['{"MESSAGE":"hello"}\n', "\n"])

        self.assertEqual(entries, [{"MESSAGE": "hello"}])

    def test_reports_malformed_json_with_line_number(self):
        with self.assertRaisesRegex(ValueError, "line 2"):
            parse_entries(['{"MESSAGE":"valid"}\n', "{bad json}\n"])

    def test_rejects_non_object_json(self):
        with self.assertRaisesRegex(ValueError, "Expected a JSON object"):
            parse_entries([json.dumps(["not", "an", "entry"])])


class AnalyzeTests(unittest.TestCase):
    def test_detects_critical_entries(self):
        alerts = analyze(
            [{"PRIORITY": "2", "_SYSTEMD_UNIT": "example.service", "MESSAGE": "failed"}]
        )

        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].severity, "CRITICAL")
        self.assertIn("failed", alerts[0].details)

    def test_detects_repeated_errors_per_service(self):
        entries = [
            {"PRIORITY": "3", "_SYSTEMD_UNIT": "worker.service", "MESSAGE": "error"}
            for _ in range(3)
        ]

        alerts = analyze(entries, repeat_threshold=3)

        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].title, "Repeated errors from worker.service")

    def test_does_not_alert_below_threshold_or_for_invalid_priority(self):
        alerts = analyze(
            [
                {"PRIORITY": "3", "_SYSTEMD_UNIT": "worker.service"},
                {"PRIORITY": "8", "_SYSTEMD_UNIT": "other.service"},
            ],
            repeat_threshold=2,
        )

        self.assertEqual(alerts, [])


class CliTests(unittest.TestCase):
    def test_input_file_reports_alerts_with_nonzero_status(self):
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "journal.jsonl"
            input_path.write_text(
                json.dumps(
                    {
                        "PRIORITY": "2",
                        "_SYSTEMD_UNIT": "example.service",
                        "MESSAGE": "service failed",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            output = io.StringIO()

            with contextlib.redirect_stdout(output):
                status = main(["--input", str(input_path)])

        self.assertEqual(status, 1)
        self.assertIn("[CRITICAL]", output.getvalue())

    def test_input_file_with_no_alerts_exits_successfully(self):
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "journal.jsonl"
            input_path.write_text('{"PRIORITY":"6","MESSAGE":"info"}\n', encoding="utf-8")
            output = io.StringIO()

            with contextlib.redirect_stdout(output):
                status = main(["--input", str(input_path)])

        self.assertEqual(status, 0)
        self.assertIn("No anomalies detected.", output.getvalue())


if __name__ == "__main__":
    unittest.main()

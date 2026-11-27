"""Run the test suite in topic order and write a Markdown checklist with links to each test."""

import sys
import unittest
from dataclasses import dataclass, field
from inspect import getsourcefile, getsourcelines, unwrap
from os.path import relpath
from pathlib import Path
from textwrap import indent
from urllib.parse import quote


_REPORT_ICONS = {
    "PASS": "✅",
    "FAIL": "❌",
    "ERROR": "❌",
    "SKIP": "⏭️",
    "EXPECTED FAILURE": "⚠️",
    "UNEXPECTED PASS": "❌",
}


@dataclass
class TestReportEntry:
    """One test result and the individual input cases shown beneath it."""

    description: str
    status: str = "PASS"
    detail: str = ""
    subtests: list[tuple[str, str, str]] = field(default_factory=list)


def _test_source_url(test, destination: Path) -> str | None:
    test = getattr(test, "test_case", None) or test
    method_name = test.id().rsplit(".", 1)[-1]
    method = getattr(test, method_name, None)
    if method is None:
        return None

    try:
        method = unwrap(method)
        source_file = getsourcefile(method)
        if source_file is None:
            return None
        _, line = getsourcelines(method)
        relative_path = Path(relpath(source_file, start=destination.parent)).as_posix()
    except (OSError, TypeError, ValueError):
        return None

    return f"{quote(relative_path)}#L{line}"


def _link_label(label: str, url: str | None) -> str:
    return f"[{label}]({url})" if url else label


def _group_title(group: str) -> str:
    return group.removeprefix("test_").replace("_", " ").strip().capitalize()


class ChecklistResult(unittest.TextTestResult):
    """Collect checklist entries for the terminal and Markdown report."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._report_groups: dict[tuple[str, str], dict[unittest.TestCase, TestReportEntry]] = {}
        self._console_section = None

    def _report(self, test, marker, status, detail=""):
        entry = self._report_entry(test)
        entry.status = status
        entry.detail = detail
        self._write_console(test, marker, status, detail)

    def _report_entry(self, test) -> TestReportEntry:
        module = type(test).__module__
        package, _, topic = module.partition(".")
        if package in ("quantum", "application"):
            section = f"{package.capitalize()} tests"
            title = _group_title(topic.rsplit(".", 1)[-1])
        else:
            section = "Test runner"
            title = _group_title(module.rsplit(".", 1)[-1])
        group = (section, title)
        if group not in self._report_groups:
            if self._report_groups:
                self.stream.writeln()
            if section != self._console_section:
                self.stream.writeln(section)
                self.stream.writeln()
                self._console_section = section
            self.stream.writeln(title)
            self._report_groups[group] = {}
        entries = self._report_groups[group]
        if test not in entries:
            entries[test] = TestReportEntry(test.shortDescription() or str(test))
        return entries[test]

    def _record_subtest(self, test, subtest, status, detail=""):
        entry = self._report_entry(test)
        label = str(subtest).removeprefix(f"{test} ")
        entry.subtests.append((status, label, detail))
        if status in ("FAIL", "ERROR"):
            entry.status = status
            entry.detail = " (subtest failed)"
        elif status == "SKIP" and entry.status == "PASS":
            entry.status = status
            entry.detail = " (subtest skipped)"

    def _write_console(self, test, marker, status, detail):
        description = test.shortDescription() or str(test)
        try:
            self.stream.writeln(f"{marker} {description}{detail}")
        except UnicodeEncodeError:
            encoding = self.stream.encoding
            text = f"{description}{detail}".encode(encoding, errors="backslashreplace")
            self.stream.writeln(f"[{status}] {text.decode(encoding)}")

    def addSuccess(self, test):
        super().addSuccess(test)
        self._report(test, "✓", "PASS")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._report(test, "✗", "FAIL")

    def addError(self, test, err):
        super().addError(test, err)
        self._report(test, "✗", "ERROR", " (error)")

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        detail = f" (skipped: {reason})"
        parent = getattr(test, "test_case", None)
        if parent is None:
            self._report(test, "–", "SKIP", detail)
        else:
            self._record_subtest(parent, test, "SKIP", detail)
            self._write_console(test, "–", "SKIP", detail)

    def addExpectedFailure(self, test, err):
        super().addExpectedFailure(test, err)
        self._report(test, "–", "EXPECTED FAILURE", " (expected failure)")

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self._report(test, "✗", "UNEXPECTED PASS", " (unexpected pass)")

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is None:
            self._record_subtest(test, subtest, "PASS")
        else:
            status = "FAIL" if issubclass(err[0], test.failureException) else "ERROR"
            self._record_subtest(test, subtest, status)
            self._write_console(test, "✗", status, " (subtest failed)")

    def write_markdown(self, destination: Path) -> None:
        outcome = "✅ Passed" if self.wasSuccessful() else "❌ Failed"
        count = f"{self.testsRun} {'test' if self.testsRun == 1 else 'tests'}"
        lines = ["# Test results", "", f"**{outcome}** · {count} run"]
        previous_section = None
        for (section, title), entries in self._report_groups.items():
            if section != previous_section:
                lines.extend(("", f"## {section}"))
                previous_section = section
            lines.extend(("", f"### {title}", ""))
            for test, entry in entries.items():
                source = _test_source_url(test, destination)
                label = _link_label(entry.description, source)
                icon = _REPORT_ICONS[entry.status]
                lines.append(f"- {icon} **{label}**{entry.detail}")
                for status, description, detail in entry.subtests:
                    subtest_label = _link_label(f"`{description}`", source)
                    lines.append(f"  - {_REPORT_ICONS[status]} {subtest_label}{detail}")

        failures = [*self.failures, *self.errors]
        if failures:
            lines.extend(("", "## Failure details"))
        for test, traceback in failures:
            label = _link_label(str(test), _test_source_url(test, destination))
            lines.extend(("", f"### {label}", "", indent(traceback.rstrip(), "    ")))

        destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


class ChecklistRunner(unittest.TextTestRunner):
    """Print each test's short description and collect the results for the report."""

    resultclass = ChecklistResult

    def __init__(self, *, stream=None):
        super().__init__(stream=stream, verbosity=0)


def _checklist_order(suite: unittest.TestSuite) -> tuple[bool, int]:
    first_topics = ("test_gate_properties", "test_gates", "test_circuit_equivalences", "test_circuit_results")
    # Discovery nests test classes inside each module's suite.
    test = suite
    while isinstance(test, unittest.TestSuite):
        test = next(iter(test), None)
    package, _, topic = type(test).__module__.partition(".")
    priority = first_topics.index(topic) if topic in first_topics else len(first_topics)
    return package != "quantum", priority


def main() -> int:
    test_directory = Path(__file__).resolve().parent
    discovered = unittest.defaultTestLoader.discover(str(test_directory))
    suite = unittest.TestSuite(sorted(discovered, key=_checklist_order))
    runner = ChecklistRunner(stream=sys.stdout)
    result = runner.run(suite)
    report_path = test_directory / "test_results.md"
    result.write_markdown(report_path)
    print(f"Markdown report saved to {report_path}")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())

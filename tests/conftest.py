"""pytest configuration: write a timestamped log of every test run to
outputs/logs/pytest_<stamp>.log so runs leave a record, like the other tools."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

_RESULTS: list[tuple[str, str, str]] = []


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call" or (rep.when == "setup" and rep.outcome != "passed"):
        detail = ""
        if rep.failed:
            detail = str(rep.longrepr).strip().splitlines()[-1]
        _RESULTS.append((item.nodeid, rep.outcome.upper(), detail))


def pytest_sessionfinish(session, exitstatus):
    root = Path(session.config.rootpath)
    out = root / "outputs" / "logs"
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%dT%H%M")
    path = out / f"pytest_{stamp}.log"
    n_pass = sum(1 for _, o, _ in _RESULTS if o == "PASSED")
    n_fail = len(_RESULTS) - n_pass
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(f"# pytest run {stamp}   exit status {exitstatus}\n")
        fh.write(f"# {n_pass} passed, {n_fail} failed/other, {len(_RESULTS)} total\n\n")
        for nodeid, outcome, detail in _RESULTS:
            fh.write(f"{outcome:<8} {nodeid}\n")
            if detail:
                fh.write(f"         {detail}\n")
    session.config._test_log_path = path


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    p = getattr(config, "_test_log_path", None)
    if p:
        terminalreporter.write_line(f"log written to {p}")

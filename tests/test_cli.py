"""Step 5 (v2) test cases from PLANNING.md: history/apps CLI and renderers."""

from datetime import datetime

from backspace_tracker.__main__ import main
from backspace_tracker.counter import Category, Counter
from backspace_tracker.reporter import NO_SESSIONS_HINT, render_apps, render_history
from backspace_tracker.storage import Storage


def make_stats(records, duration=120.0):
    clock_values = iter([0.0, duration])
    counter = Counter(clock=lambda: next(clock_values))
    counter.start()
    for category, app in records:
        counter.record(category, app=app)
    return counter.stop()


def seeded_storage(tmp_path):
    storage = Storage(tmp_path / "sessions.db")
    storage.save_session(
        datetime(2026, 6, 6, 14, 30),
        make_stats(
            [(Category.BACKSPACE, "Code.exe")] * 4
            + [(Category.OTHER, "Code.exe")] * 4
            + [(Category.CTRL_Z, "notepad.exe")] * 2
        ),
    )
    storage.save_session(
        datetime(2026, 6, 7, 9, 0),
        make_stats([(Category.BACKSPACE, "Code.exe"), (Category.OTHER, "chrome.exe")]),
    )
    return storage


def test_render_history_includes_sessions_and_v1_formatting(tmp_path):
    out = render_history(seeded_storage(tmp_path).load_sessions())
    assert "2026-06-06 14:30:00" in out
    assert "2026-06-07 09:00:00" in out
    assert "2m 00s" in out  # v1 duration formatting reused
    assert "60.0%" in out  # session 1: 6 corrections / 10 keys
    assert "3.0/min" in out  # session 1: 6 corrections / 2 min


def test_render_apps_aggregates_across_sessions(tmp_path):
    out = render_apps(seeded_storage(tmp_path).load_sessions())
    # Code.exe: 4+1 corrections of 9 keys across both sessions
    assert "Code.exe" in out
    assert "corr      5" in out
    assert "notepad.exe" in out
    assert "chrome.exe" in out


def test_render_apps_sorted_by_corrections(tmp_path):
    out = render_apps(seeded_storage(tmp_path).load_sessions())
    assert out.index("Code.exe") < out.index("notepad.exe") < out.index("chrome.exe")


def test_empty_db_friendly_message(tmp_path):
    storage = Storage(tmp_path / "fresh.db")
    assert render_history(storage.load_sessions()) == NO_SESSIONS_HINT
    assert render_apps(storage.load_sessions()) == NO_SESSIONS_HINT


def test_cli_history_end_to_end(tmp_path, capsys):
    seeded_storage(tmp_path)
    main(["history", "--db", str(tmp_path / "sessions.db")])
    out = capsys.readouterr().out
    assert "Session history" in out
    assert "2026-06-06 14:30:00" in out


def test_cli_apps_end_to_end(tmp_path, capsys):
    seeded_storage(tmp_path)
    main(["apps", "--db", str(tmp_path / "sessions.db")])
    assert "Code.exe" in capsys.readouterr().out


def test_bare_invocation_runs_tracker(monkeypatch):
    import backspace_tracker.app as app_module

    called = []
    monkeypatch.setattr(app_module, "run", lambda: called.append(True))
    main([])
    assert called == [True]

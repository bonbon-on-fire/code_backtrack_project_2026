# Backspace Tracker — Planning

## Overview
A lightweight Windows app that counts correction keystrokes (Backspace, Delete, etc.)
from the moment it's started to the moment it's stopped. Purpose: measure how often
corrections happen while coding, and over time, whether that rate changes.

## Goals
- [ ] Count correction keys globally while the app is running
- [ ] Global hotkey (Ctrl+Shift+Backspace) toggles recording on/off — minimal usage friction
- [ ] Show a session summary (counts, duration, corrections/minute)
- [ ] Compute correction ratio (correction keys ÷ total keystrokes)
- [ ] Persist session history to spot trends over time
- [ ] Per-app breakdown (e.g., VS Code vs terminal vs browser)

## Non-Goals
- Logging *which* keys are pressed or reconstructing typed text — this is a
  **counter, not a keylogger**. Only aggregate numbers are ever stored.
- Cross-platform support (Windows-only for now)
- Cloud sync / accounts

## Tech Stack
- **Python 3.12+**
- **pynput** — global keyboard hook
- **SQLite** (stdlib `sqlite3`) — session persistence (v2)
- Console app for v1; tray app (e.g., `pystray`) considered for v3

## Architecture
```
┌─────────────┐    key events    ┌──────────────┐    aggregates    ┌─────────────┐
│ pynput hook │ ───────────────► │ Counter core │ ───────────────► │ Reporter    │
│ (listener)  │                  │ (in-memory   │                  │ (console /  │
└─────────────┘                  │  tallies)    │                  │  summary)   │
                                 └──────┬───────┘                  └─────────────┘
                                        │ on exit / interval
                                        ▼
                                 ┌──────────────┐
                                 │ SQLite store │  (v2)
                                 └──────────────┘
```
- **Listener**: subscribes to global key events; immediately reduces each event to a
  category (backspace / ctrl+backspace / delete / ctrl+delete / other) and discards it.
- **Counter core**: in-memory tallies per category + total keystrokes + timestamps.
- **Reporter**: live console line while running; full summary on Ctrl+C.

### Keys tracked
| Key | Meaning |
|-----|---------|
| Backspace | single-char correction |
| Ctrl+Backspace | word-level correction |
| Delete | forward delete |
| Ctrl+Delete | forward word delete |
| Ctrl+Z | undo (heaviest correction) — counted as its own category |
| (all other keys) | counted only toward total, never identified |

## Milestones
| # | Milestone | Status |
|---|-----------|--------|
| 1 | **v1 — Counter**: console app, global hotkey (Ctrl+Shift+Backspace) starts/stops a session, count correction keys + total keystrokes, summary on stop | ☐ |
| 2 | **v2 — Insight**: SQLite session history, correction ratio, per-app filtering/breakdown (active-window process name) | ☐ |
| 3 | **v3 — Daily driver**: tray icon with live count, trend charts, burst detection (N+ backspaces in a row = rewrite vs typo) | ☐ |

## v1 Build Order
- [ ] **1. Scaffolding** — `pyproject.toml` (Python 3.12+, pynput), package layout under
  `src/backspace_tracker/`, `.gitignore`, README stub
- [ ] **2. Counter core** (`counter.py`) — `Category` enum, `Counter` class with tallies,
  timestamps, derived stats (duration, corrections/min, correction ratio). Pure logic,
  zero I/O, unit tests alongside
- [ ] **3. Event classification** (`listener.py`, logic half) — (key, modifier state) →
  `Category` mapping, modifier tracking. Tested with synthetic events; key cases:
  Ctrl+Backspace → counted, Ctrl+Shift+Backspace → toggle (never counted)
- [ ] **4. Live wiring** — real `pynput.Listener`, hotkey toggles idle ↔ recording,
  Ctrl+C clean exit
- [ ] **5. Reporter** (`reporter.py`) — live in-place status line while recording,
  summary table on session stop
- [ ] **6. End-to-end smoke test** — toggle on, type across apps, hold Backspace,
  Ctrl+Z, toggle off; verify summary matches actual usage

## Decisions
- **Hotkey**: Ctrl+Shift+Backspace toggles recording. The app launches idle; the hotkey
  starts a session, pressing it again stops and prints the summary. The hotkey press
  itself is never counted (Shift check happens before Ctrl+Backspace classification).
- **Ctrl+Z**: counted as its own category (cheap to add; data can't be retrofitted).
- **Key-repeat**: every repeat counts — each repeat deletes a real character, so it's
  genuine correction volume. No thresholding in v1.

## Open Questions
- Burst threshold (v3): how many consecutive backspaces counts as a "rewrite"?
  Starting guess: ≥10 — tune once v2 session data exists.

## Notes
- v1 counts everywhere; the user controls data quality by only running it while coding.
  Per-app filtering arrives in v2.
- Privacy principle: no key identities or sequences are ever written to disk — only
  category counts and timestamps.

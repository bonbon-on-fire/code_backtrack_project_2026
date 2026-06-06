# Backspace Tracker — Planning

## Overview
A lightweight Windows app that counts correction keystrokes (Backspace, Delete, etc.)
from the moment it's started to the moment it's stopped. Purpose: measure how often
corrections happen while coding, and over time, whether that rate changes.

## Goals
- [ ] Count correction keys globally while the app is running
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
| Ctrl+Z | undo (heaviest correction) — *maybe, decide in v1* |
| (all other keys) | counted only toward total, never identified |

## Milestones
| # | Milestone | Status |
|---|-----------|--------|
| 1 | **v1 — Counter**: console app, start/stop, count correction keys + total keystrokes, summary on exit | ☐ |
| 2 | **v2 — Insight**: SQLite session history, correction ratio, per-app filtering/breakdown (active-window process name) | ☐ |
| 3 | **v3 — Daily driver**: tray icon with live count, trend charts, burst detection (N+ backspaces in a row = rewrite vs typo) | ☐ |

## Open Questions
- Count Ctrl+Z as a correction, separately, or not at all?
- Burst threshold: how many consecutive backspaces counts as a "rewrite"?
- Should holding Backspace (key-repeat) count each repeat, or once?

## Notes
- v1 counts everywhere; the user controls data quality by only running it while coding.
  Per-app filtering arrives in v2.
- Privacy principle: no key identities or sequences are ever written to disk — only
  category counts and timestamps.

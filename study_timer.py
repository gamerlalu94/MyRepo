"""Study timer logger with non-blocking Enter handling.

Behavior improvements:
 - Press Enter to start a 4-minute timer. While the timer is running, pressing Enter ends the current timer (records elapsed time) and immediately starts a new timer.
 - To exit the whole session, type a single exit letter (configured at start) then press Enter.
 - The script records per-question durations and logs a session row into a per-subject CSV.
"""

from __future__ import annotations

import csv
import sys
import time
from datetime import datetime
from pathlib import Path

from queue import Queue, Empty
from threading import Thread

try:
    import msvcrt
except Exception:  # not on Windows or not available
    msvcrt = None

# Cross-platform beep helper: prefer winsound on Windows, fall back to terminal bell.
try:
    import winsound
except Exception:
    winsound = None


def do_beep() -> None:
    """Emit a short beep. Uses winsound.Beep on Windows when available, otherwise prints the ASCII bell."""
    if winsound:
        try:
            # frequency 1000 Hz, duration 150 ms
            winsound.Beep(1000, 150)
        except Exception:
            print("\a", end="", flush=True)
    else:
        print("\a", end="", flush=True)


def start_input_thread(input_queue: Queue) -> Thread:
    """Start a background thread that reads lines from stdin and pushes them to the queue.

    This approach works across terminals (PowerShell, terminals that buffer stdin) and avoids msvcrt pitfalls.
    """

    def reader() -> None:
        try:
            while True:
                line = sys.stdin.readline()
                if line == "":
                    # EOF
                    break
                # push the raw line (without trailing newline)
                input_queue.put(line.rstrip("\r\n"))
        except Exception:
            pass

    t = Thread(target=reader, daemon=True)
    t.start()
    return t


def start_key_thread(input_queue: Queue) -> Thread:
    """Start a background thread that reads single keypresses via msvcrt and assembles lines.

    This is preferred on Windows TTYs so single Enter and characters are captured immediately.
    """

    def reader() -> None:
        buf: list[str] = []
        try:
            while True:
                ch = msvcrt.getwch() # type: ignore
                # handle Ctrl+C
                if ch == "\x03":
                    raise KeyboardInterrupt
                # Enter
                if ch == "\r" or ch == "\n":
                    line = "".join(buf)
                    input_queue.put(line)
                    buf = []
                    continue
                # Backspace
                if ch in ("\x08", "\x7f"):
                    if buf:
                        buf.pop()
                    continue
                # Regular char
                buf.append(ch)
        except Exception:
            # thread exits on error or when console closes
            pass

    t = Thread(target=reader, daemon=True)
    t.start()
    return t


CSV_HEADERS = [
    "datetime",
    "session_wall_seconds",
    "questions_started",
    "questions_attempted",
    "questions_correct",
    "per_question_durations_seconds",
]
DEFAULT_DURATION_SECONDS = 4 * 60  # 4 minutes


def ensure_csv(path: Path) -> None:
    if not path.exists():
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)


def append_session(
    path: Path,
    wall_seconds: int,
    started: int,
    attempted: int,
    correct: int,
    durations: list[int],
) -> None:
    now = datetime.now().isoformat(sep=" ", timespec="seconds")
    durations_str = ";".join(str(int(d)) for d in durations)
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([now, wall_seconds, started, attempted, correct, durations_str])


def prompt_int(prompt: str, default: int | None = None, iq: Queue | None = None) -> int:
    """Prompt for an integer.

    If an input queue `iq` is provided, read the user's response from the queue (this is used when
    a background key-thread is active and consumes stdin). Otherwise fall back to built-in input().
    """
    while True:
        try:
            if iq is None:
                s = input(prompt).strip()
            else:
                # print prompt and block until a line is available from the input queue
                print(prompt, end="", flush=True)
                s = iq.get()
                # echo the line for visibility
                print(s)

            if s == "" and default is not None:
                return default
            val = int(s)
            if val < 0:
                print("Please enter a non-negative integer.")
                continue
            return val
        except ValueError:
            print("Please enter an integer.")


class Session:
    def __init__(self, duration_seconds: int = DEFAULT_DURATION_SECONDS) -> None:
        self.duration_seconds = duration_seconds
        self.current_start: float | None = None
        self.per_question_durations: list[int] = []
        self.started_count = 0

    def start(self) -> None:
        self.current_start = time.monotonic()
        self.started_count += 1
        print(f"\nTimer started (question #{self.started_count}).")

    def end(self) -> int:
        if self.current_start is None:
            return 0
        elapsed = int(time.monotonic() - self.current_start)
        self.per_question_durations.append(elapsed)
        self.current_start = None
        print(f"\nTimer ended — elapsed {elapsed}s.")
        return elapsed

    def is_running(self) -> bool:
        return self.current_start is not None

    def elapsed_since_start(self) -> int:
        if self.current_start is None:
            return 0
        return int(time.monotonic() - self.current_start)


def interactive_loop(subject: str, csv_path: Path, exit_letter: str) -> None:
    session = Session()
    session_start_wall = None
    # alarm_active tracks whether the timer exceeded the configured duration and is beeping
    alarm_active = False
    last_beep_time = 0.0

    print(f"Subject: {subject}")
    print("Instructions:")
    print(" - Press Enter to start a 4-minute timer.")
    print(" - While a timer is running, press Enter to end the current timer and immediately start a new one.")
    print(f" - To exit the session type '{exit_letter}' then press Enter. (Typing the letter then pressing Enter is required.)")

    # start reader thread and queue
    iq: Queue[str] = Queue()
    key_thread = None
    input_thread = None

    # prefer keypress reader on Windows TTY
    if msvcrt is not None and sys.stdin.isatty():
        try:
            key_thread = start_key_thread(iq)
            print("[input mode] using msvcrt key reader")
        except Exception:
            input_thread = start_input_thread(iq)
            print("[input mode] fallback to stdin line reader")
    else:
        input_thread = start_input_thread(iq)
        print("[input mode] using stdin line reader")

    buffer = ""  # stores typed line until processed
    try:
        while True:
            try:
                # non-blocking check for input lines
                line = iq.get_nowait()
            except Empty:
                line = None

            if line is not None:
                # a full line was entered (Enter pressed)
                if line.strip().lower() == exit_letter.lower():
                    print("\nExiting session.")
                    break

                # empty line means plain Enter
                if line == "":
                    if not session.is_running():
                        if session_start_wall is None:
                            session_start_wall = time.monotonic()
                        session.start()
                    else:
                        session.end()
                        # stop any active alarm/beeping if we were overdue
                        alarm_active = False
                        # immediately start a new timer
                        session.start()
                else:
                    # non-empty line that isn't exit letter — ignore or could be used for notes
                    print(f"Received input: {line}")

            # display timer if running
            if session.is_running():
                remaining = session.duration_seconds - session.elapsed_since_start()
                if remaining < 0:
                    remaining = 0
                mins, secs = divmod(max(0, remaining), 60)
                print(f"\rTime left: {mins:02d}:{secs:02d} (press Enter to end and start next) ", end="", flush=True)

                # when duration reached, enter alarm mode and beep until the user presses Enter
                if session.elapsed_since_start() >= session.duration_seconds:
                    if not alarm_active:
                        print("\nTimer exceeded full duration; beeping until Enter is pressed to end the question.")
                        alarm_active = True
                        last_beep_time = 0.0
                    now = time.monotonic()
                    # beep once per second while overdue
                    if now - last_beep_time >= 1.0:
                        do_beep()
                        last_beep_time = now

            time.sleep(0.15)

    except KeyboardInterrupt:
        print("\nSession interrupted by user (Ctrl+C).")

    # session end: finalize
    if session_start_wall is None:
        wall_seconds = 0
    else:
        wall_seconds = int(time.monotonic() - session_start_wall)

    attempted = len(session.per_question_durations)
    started = session.started_count

    print(f"Session ended. Questions started: {started}, attempted (ended): {attempted}.")
    # how many question timings exceeded the configured per-question duration?
    late_after_4min = sum(1 for d in session.per_question_durations if d > session.duration_seconds)
    print(f"Questions ended after the {session.duration_seconds}s limit: {late_after_4min}")

    if attempted == 0:
        print("No question timings were recorded. Nothing will be logged.")
        return

    wrong = prompt_int("How many questions were wrong? ", iq=iq)
    correct = max(0, attempted - wrong)

    append_session(csv_path, wall_seconds, started, attempted, correct, session.per_question_durations)
    print(f"Logged session to {csv_path}. Correct: {correct}, Wrong: {wrong}.")

    # show summary/stats for this subject CSV after logging
    try:
        compute_and_print_stats(csv_path)
    except Exception as exc:  # don't crash the program for stats errors
        print(f"Could not compute stats: {exc}")


def main() -> int:
    print("Study Timer Logger — improved")
    # quick check: ensure we're running in an interactive terminal where stdin is a TTY
    if not sys.stdin or not sys.stdin.isatty():
        print("No interactive stdin detected. Please run this program in the VS Code Integrated Terminal or an external terminal (not the Debug Console).")
        return 1

    subject = input("Enter subject name (used for CSV filename): ").strip()
    if not subject:
        print("Subject cannot be empty.")
        return 1

    exit_letter = input("Choose a single letter to use for exiting the session (press Enter for default 'q'): ").strip()
    if exit_letter == "":
        exit_letter = "q"
    exit_letter = exit_letter[0]

    # sanitize filename
    safe_name = "".join(c for c in subject if c.isalnum() or c in ("-", "_")).strip()
    if not safe_name:
        safe_name = "subject"

    csv_filename = f"sessions_{safe_name}.csv"
    csv_path = Path(__file__).parent.joinpath(csv_filename)
    ensure_csv(csv_path)

    interactive_loop(subject, csv_path, exit_letter)
    return 0


def compute_and_print_stats(csv_path: Path) -> None:
    """Read the subject CSV and print summary statistics.

    Stats printed:
      - number of sessions
      - total questions attempted (sum)
      - total correct and overall accuracy
      - average question duration (across all recorded questions)
      - fastest and slowest question durations
      - per-session accuracy (date -> accuracy)
    """
    if not csv_path.exists():
        print("No CSV found for stats.")
        return

    sessions = []
    all_durations: list[int] = []
    total_attempted = 0
    total_correct = 0

    with csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # parse fields defensively
            try:
                date = row.get("datetime", "")
                attempted = int(row.get("questions_attempted", "0") or 0)
                correct = int(row.get("questions_correct", "0") or 0)
                durations_field = row.get("per_question_durations_seconds", "") or ""
                durations = [int(x) for x in durations_field.split(";") if x.strip()]
            except Exception:
                # skip malformed rows
                continue

            sessions.append((date, attempted, correct, durations))
            total_attempted += attempted
            total_correct += correct
            all_durations.extend(durations)

    num_sessions = len(sessions)
    print("\n--- Subject summary ---")
    print(f"Sessions recorded: {num_sessions}")
    print(f"Total questions attempted: {total_attempted}")
    print(f"Total correct: {total_correct}")
    if total_attempted > 0:
        accuracy = total_correct / total_attempted * 100
        print(f"Overall accuracy: {accuracy:.1f}%")
    else:
        print("Overall accuracy: N/A (no attempted questions)")

    if all_durations:
        avg_dur = sum(all_durations) / len(all_durations)
        fastest = min(all_durations)
        slowest = max(all_durations)
        print(f"Average question duration: {avg_dur:.1f}s")
        print(f"Fastest question: {fastest}s, Slowest question: {slowest}s")
        late_total = sum(1 for d in all_durations if d > DEFAULT_DURATION_SECONDS)
        print(f"Questions finished after {DEFAULT_DURATION_SECONDS}s: {late_total}")
    else:
        print("No per-question durations recorded yet.")

    # per-session accuracy trend (print last 10 sessions)
    if sessions:
        print("\nPer-session accuracy (most recent first):")
        for date, attempted, correct, durations in reversed(sessions[-10:]):
            acc = (correct / attempted * 100) if attempted > 0 else None
            acc_str = f"{acc:.1f}%" if acc is not None else "N/A"
            avg_q = (sum(durations) / len(durations)) if durations else None
            avg_q_str = f"{avg_q:.1f}s" if avg_q is not None else "-"
            print(f"{date} | attempted={attempted} correct={correct} acc={acc_str} avg_q={avg_q_str}")
    print("--- end summary ---\n")


if __name__ == "__main__":
    raise SystemExit(main())

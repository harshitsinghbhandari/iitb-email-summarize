#!/usr/bin/env python3
"""Evaluate live Ollama deadline function calling across sample emails."""

from __future__ import annotations

from dataclasses import dataclass
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from deadline_tools.function_calling import DEADLINE_FUNCTION_MODEL, call_deadline_tool  # noqa: E402


@dataclass(frozen=True)
class DeadlineCase:
    name: str
    expected_title: str
    expected_due_date: str
    content: str


CASES = [
    DeadlineCase(
        name="assignment_submission",
        expected_title="CS 101 Assignment 4",
        expected_due_date="2026-04-30",
        content=(
            "Subject: CS 101 Assignment 4\n\n"
            "Please submit Assignment 4 on Moodle by 11:59 PM on April 30, 2026. "
            "Late submissions will not be accepted."
        ),
    ),
    DeadlineCase(
        name="fee_payment",
        expected_title="Hostel fee payment",
        expected_due_date="2026-05-02",
        content=(
            "Subject: Hostel Fee Payment Reminder\n\n"
            "All students must complete hostel fee payment before May 2, 2026. "
            "The payment portal will close after the deadline."
        ),
    ),
    DeadlineCase(
        name="project_proposal",
        expected_title="Project proposal submission",
        expected_due_date="2026-05-10",
        content=(
            "Subject: Project Proposal Deadline\n\n"
            "Teams should email their project proposal PDF to the course instructor by "
            "May 10, 2026."
        ),
    ),
    DeadlineCase(
        name="workshop_registration",
        expected_title="AI workshop registration",
        expected_due_date="2026-04-28",
        content=(
            "Subject: Register for AI Tools Workshop\n\n"
            "Registration for the AI Tools Workshop closes on April 28, 2026. "
            "Seats are limited and confirmation will be sent later."
        ),
    ),
    DeadlineCase(
        name="scholarship_application",
        expected_title="Merit scholarship application",
        expected_due_date="2026-05-15",
        content=(
            "Subject: Merit Scholarship Applications Open\n\n"
            "Eligible students should upload the completed merit scholarship application "
            "form by 5 PM on May 15, 2026."
        ),
    ),
    DeadlineCase(
        name="event_abstract",
        expected_title="Research symposium abstract",
        expected_due_date="2026-06-01",
        content=(
            "Subject: Research Symposium Call for Abstracts\n\n"
            "Submit your research symposium abstract by June 1, 2026 through the "
            "department portal."
        ),
    ),
    DeadlineCase(
        name="lab_makeup",
        expected_title="Physics lab makeup request",
        expected_due_date="2026-05-05",
        content=(
            "Subject: Physics Lab Makeup Slot\n\n"
            "Students who missed Lab 6 must request a makeup slot no later than May 5, 2026."
        ),
    ),
    DeadlineCase(
        name="placement_profile",
        expected_title="Placement profile update",
        expected_due_date="2026-04-29",
        content=(
            "Subject: Update Placement Profile\n\n"
            "Please update your placement profile and resume by April 29, 2026 so companies "
            "can view the latest information."
        ),
    ),
]


def main() -> int:
    print(f"Model: {DEADLINE_FUNCTION_MODEL}")
    print(f"Cases: {len(CASES)}\n")

    due_date_correct = 0
    no_call_count = 0

    for index, case in enumerate(CASES, start=1):
        print(f"{index}. {case.name}")
        print(f"   Expected title: {case.expected_title}")
        print(f"   Expected date:  {case.expected_due_date}")

        try:
            deadline = call_deadline_tool(case.content, timeout=120)
        except Exception as exc:
            print(f"   ERROR: {exc}\n")
            continue

        if deadline is None:
            no_call_count += 1
            print("   Actual: no function call\n")
            continue

        date_ok = deadline.due_date == case.expected_due_date
        due_date_correct += int(date_ok)

        print(f"   Actual title:   {deadline.title}")
        print(f"   Actual date:    {deadline.due_date} {'OK' if date_ok else 'WRONG'}")
        print(f"   Source text:    {deadline.source_text}")
        print(f"   Confidence:     {deadline.confidence}\n")

    print("Summary")
    print(f"Due dates correct: {due_date_correct}/{len(CASES)}")
    print(f"No function call:  {no_call_count}/{len(CASES)}")
    print("Title correctness: inspect Actual title vs Expected title above.")
    return 0 if due_date_correct == len(CASES) and no_call_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

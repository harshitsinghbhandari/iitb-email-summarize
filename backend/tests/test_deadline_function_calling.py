import json
from unittest.mock import Mock, patch

from deadline_tools.function_calling import (
    DEADLINE_FUNCTION_MODEL,
    build_deadline_payload,
    call_deadline_tool,
    extract_deadline_call,
)


def test_payload_uses_functiongemma_deadline_tool():
    payload = build_deadline_payload("Submit the form by April 30, 2026.")

    assert payload["model"] == DEADLINE_FUNCTION_MODEL
    assert payload["model"] == "functiongemma:270m"
    assert payload["stream"] is False
    assert payload["tools"][0]["function"]["name"] == "record_deadline"
    assert "due_date" in payload["tools"][0]["function"]["parameters"]["required"]


def test_extract_deadline_call_from_dict_arguments():
    response_data = {
        "message": {
            "tool_calls": [
                {
                    "function": {
                        "name": "record_deadline",
                        "arguments": {
                            "title": "Assignment 4",
                            "due_date": "2026-04-30",
                            "source_text": "Submit Assignment 4 by April 30, 2026.",
                            "action_required": True,
                            "confidence": 0.93,
                        },
                    }
                }
            ]
        }
    }

    deadline = extract_deadline_call(response_data)

    assert deadline is not None
    assert deadline.title == "Assignment 4"
    assert deadline.due_date == "2026-04-30"
    assert deadline.action_required is True
    assert deadline.confidence == 0.93


def test_extract_deadline_call_from_json_string_arguments():
    response_data = {
        "message": {
            "tool_calls": [
                {
                    "function": {
                        "name": "record_deadline",
                        "arguments": json.dumps(
                            {
                                "title": "Fee payment",
                                "due_date": "2026-05-02",
                                "source_text": "Pay fees before May 2, 2026.",
                                "action_required": True,
                                "confidence": 0.8,
                            }
                        ),
                    }
                }
            ]
        }
    }

    deadline = extract_deadline_call(response_data)

    assert deadline is not None
    assert deadline.title == "Fee payment"
    assert deadline.due_date == "2026-05-02"


def test_extract_deadline_call_returns_none_without_tool_call():
    assert extract_deadline_call({"message": {"content": "No deadline found."}}) is None


def test_extract_deadline_call_returns_none_for_incomplete_arguments():
    response_data = {
        "message": {
            "tool_calls": [
                {
                    "function": {
                        "name": "record_deadline",
                        "arguments": {"due_date": "2026-05-10"},
                    }
                }
            ]
        }
    }

    assert extract_deadline_call(response_data) is None


def test_extract_deadline_call_returns_none_for_invalid_json_arguments():
    response_data = {
        "message": {
            "tool_calls": [
                {
                    "function": {
                        "name": "record_deadline",
                        "arguments": "{bad json",
                    }
                }
            ]
        }
    }

    assert extract_deadline_call(response_data) is None


@patch("deadline_tools.function_calling.requests.post")
def test_call_deadline_tool_posts_to_ollama_chat(mock_post):
    response = Mock()
    response.json.return_value = {
        "message": {
            "tool_calls": [
                {
                    "function": {
                        "name": "record_deadline",
                        "arguments": {
                            "title": "Project proposal",
                            "due_date": "2026-05-10",
                            "source_text": "Proposal due May 10.",
                            "action_required": True,
                            "confidence": 0.9,
                        },
                    }
                }
            ]
        }
    }
    mock_post.return_value = response

    deadline = call_deadline_tool("Proposal due May 10.", timeout=7)

    assert deadline is not None
    assert deadline.title == "Project proposal"
    response.raise_for_status.assert_called_once_with()
    mock_post.assert_called_once()
    assert mock_post.call_args.kwargs["json"]["model"] == "functiongemma:270m"
    assert mock_post.call_args.kwargs["json"]["tools"][0]["function"]["name"] == "record_deadline"
    assert mock_post.call_args.kwargs["timeout"] == 7

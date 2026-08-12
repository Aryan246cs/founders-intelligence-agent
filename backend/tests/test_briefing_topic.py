"""
Topic extraction feeds the briefing title, which is what appears on the
dashboard and the Briefings list — so a wrong match is visible to every user.
"""

from __future__ import annotations

import pytest

from agents.briefing_agent import _extract_topic_from_request


@pytest.mark.parametrize(
    "request_text, expected",
    [
        ("Monitor OpenAI and Anthropic on enterprise AI", "Enterprise AI"),
        ("Monitor Zomato, Swiggy and Zepto on quick commerce", "Quick Commerce"),
        ("Monitor Byjus and Unacademy on edtech", "EdTech"),
        ("Monitor Figma and Notion on saas pricing", "SaaS"),
        ("Monitor Razorpay and PhonePe on fintech", "Fintech"),
    ],
)
def test_known_domains_get_their_display_label(request_text, expected):
    assert _extract_topic_from_request(request_text) == expected


@pytest.mark.parametrize(
    "request_text, not_expected",
    [
        # 'ai' is a substring of both — a bare `in` test matched it and titled
        # nearly every briefing "Ai Intelligence".
        ("Monitor Zomato and Swiggy on retail delivery trends", "AI"),
        ("Monitor Shopify on ecommerce supply chain", "AI"),
    ],
)
def test_substrings_do_not_match_across_word_boundaries(request_text, not_expected):
    assert _extract_topic_from_request(request_text) != not_expected


def test_longest_keyword_wins():
    """'enterprise ai' must beat the shorter 'ai' that it contains."""
    assert _extract_topic_from_request("a briefing on enterprise ai") == "Enterprise AI"


def test_unknown_topic_falls_back_to_the_request_text():
    assert _extract_topic_from_request("Monitor Stripe and Adyen") == (
        "Monitor Stripe and Adyen"
    )

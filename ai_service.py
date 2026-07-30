"""Groq AI integration for generating event plans.

Featured prompt-engineering principle: FEW-SHOT PROMPTING.
We give the model two complete worked examples (input -> ideal JSON output)
before the real request. Seeing the exact shape and quality we expect makes
the model return consistent, well-structured plans instead of free-form prose.
"""
import json
from groq import Groq
from config import Config

# The client is created lazily (on first use) instead of at import time, so a
# missing key or library issue produces a catchable error at request time
# rather than crashing the whole app on startup.
_client = None


def _get_client():
    global _client
    if _client is None:
        _client = Groq(api_key=Config.GROQ_API_KEY)
    return _client

# The JSON shape every plan must follow. We describe it once and the few-shot
# examples below demonstrate it, so the model reliably matches it.
_JSON_SHAPE = """{
  "summary": "one-paragraph overview of the event",
  "timeline": [{"time": "HH:MM", "activity": "what happens"}],
  "budget_breakdown": [{"item": "category", "amount": 0, "note": "detail"}],
  "checklist": [{"task": "thing to do", "owner": "who", "deadline": "when"}],
  "vendor_suggestions": [{"type": "vendor category", "why": "reason"}],
  "tips": ["short practical tip"]
}"""

# --- FEW-SHOT EXAMPLES ---------------------------------------------------
# Each example is a (user request, ideal assistant answer) pair. They are fed
# to the model as prior turns so it learns the pattern by demonstration.
_FEWSHOT = [
    {
        "role": "user",
        "content": (
            "Event type: Birthday Party\nDate: 2025-08-15\nGuests: 20\n"
            "Budget: 500 USD\nLocation: Home backyard\nNotes: Kid turning 8, superhero theme"
        ),
    },
    {
        "role": "assistant",
        "content": json.dumps({
            "summary": "A superhero-themed 8th birthday party for 20 guests in a home backyard, kept lively and low-cost with DIY decor and simple catering.",
            "timeline": [
                {"time": "15:00", "activity": "Guests arrive, welcome with superhero capes"},
                {"time": "15:30", "activity": "Games: obstacle 'training course'"},
                {"time": "16:15", "activity": "Cake and snacks"},
                {"time": "16:45", "activity": "Pinata and gift opening"},
                {"time": "17:30", "activity": "Goodbye party favors"},
            ],
            "budget_breakdown": [
                {"item": "Food & snacks", "amount": 180, "note": "Pizza, fruit, juice"},
                {"item": "Cake", "amount": 60, "note": "Superhero themed"},
                {"item": "Decorations", "amount": 90, "note": "Balloons, banners, DIY capes"},
                {"item": "Games & pinata", "amount": 70, "note": "Prizes included"},
                {"item": "Party favors", "amount": 60, "note": "20 goodie bags"},
                {"item": "Buffer", "amount": 40, "note": "Unexpected costs"},
            ],
            "checklist": [
                {"task": "Send invitations", "owner": "Parent", "deadline": "3 weeks before"},
                {"task": "Order cake", "owner": "Parent", "deadline": "1 week before"},
                {"task": "Buy decorations", "owner": "Parent", "deadline": "4 days before"},
                {"task": "Prepare games", "owner": "Parent", "deadline": "1 day before"},
            ],
            "vendor_suggestions": [
                {"type": "Local bakery", "why": "Affordable themed cakes"},
                {"type": "Party rental shop", "why": "Tables, chairs, and pinata"},
            ],
            "tips": [
                "Prepare a rain backup plan for the backyard",
                "Assign one adult per 5 kids for supervision",
            ],
        }),
    },
    {
        "role": "user",
        "content": (
            "Event type: Corporate Conference\nDate: 2025-10-02\nGuests: 150\n"
            "Budget: 25000 USD\nLocation: Downtown hotel\nNotes: One-day tech conference with keynote and workshops"
        ),
    },
    {
        "role": "assistant",
        "content": json.dumps({
            "summary": "A one-day 150-person tech conference at a downtown hotel featuring a keynote, parallel workshops, and catered networking.",
            "timeline": [
                {"time": "08:30", "activity": "Registration and coffee"},
                {"time": "09:30", "activity": "Opening keynote"},
                {"time": "11:00", "activity": "Workshop session A"},
                {"time": "12:30", "activity": "Networking lunch"},
                {"time": "14:00", "activity": "Workshop session B"},
                {"time": "16:00", "activity": "Panel discussion"},
                {"time": "17:30", "activity": "Closing remarks and networking drinks"},
            ],
            "budget_breakdown": [
                {"item": "Venue & AV", "amount": 9000, "note": "Main hall + 2 breakout rooms"},
                {"item": "Catering", "amount": 7500, "note": "Coffee, lunch, drinks for 150"},
                {"item": "Speakers", "amount": 4000, "note": "Keynote honorarium + travel"},
                {"item": "Marketing & materials", "amount": 2500, "note": "Badges, signage, program"},
                {"item": "Staff & registration", "amount": 1500, "note": "Temp staff for the day"},
                {"item": "Buffer", "amount": 500, "note": "Contingency"},
            ],
            "checklist": [
                {"task": "Confirm venue contract", "owner": "Event lead", "deadline": "8 weeks before"},
                {"task": "Book speakers", "owner": "Program chair", "deadline": "6 weeks before"},
                {"task": "Open registration", "owner": "Marketing", "deadline": "5 weeks before"},
                {"task": "Finalize catering headcount", "owner": "Ops", "deadline": "1 week before"},
            ],
            "vendor_suggestions": [
                {"type": "AV production company", "why": "Reliable sound and streaming"},
                {"type": "Hotel catering", "why": "On-site convenience for 150 guests"},
                {"type": "Badge/printing service", "why": "Professional attendee materials"},
            ],
            "tips": [
                "Send calendar invites with the agenda one week ahead",
                "Have a tech rehearsal the evening before",
            ],
        }),
    },
]


def _build_messages(details: dict):
    """Assemble system + few-shot examples + the real user request."""
    system = (
        "You are a professional event planner. Given event details, produce a "
        "complete, realistic plan. Always respond with ONLY valid JSON matching "
        "this exact shape (no markdown, no commentary):\n" + _JSON_SHAPE
    )

    user_request = (
        f"Event type: {details.get('event_type', 'N/A')}\n"
        f"Date: {details.get('event_date', 'N/A')}\n"
        f"Guests: {details.get('guest_count', 'N/A')}\n"
        f"Budget: {details.get('budget', 'N/A')} USD\n"
        f"Location: {details.get('location', 'N/A')}\n"
        f"Notes: {details.get('notes', 'None')}"
    )

    messages = [{"role": "system", "content": system}]
    messages.extend(_FEWSHOT)  # the demonstrations
    messages.append({"role": "user", "content": user_request})
    return messages


def generate_plan(details: dict) -> dict:
    """Call Groq and return the parsed plan as a dict.

    Raises RuntimeError with a readable message if the call or parsing fails.
    """
    if not Config.GROQ_API_KEY or Config.GROQ_API_KEY.startswith("your_"):
        raise RuntimeError("GROQ_API_KEY is not set. Add it to your .env file.")

    messages = _build_messages(details)
    try:
        completion = _get_client().chat.completions.create(
            model=Config.GROQ_MODEL,
            messages=messages,
            temperature=0.7,
            response_format={"type": "json_object"},  # ask Groq for strict JSON
        )
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Groq API call failed: {exc}") from exc

    raw = completion.choices[0].message.content
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Model did not return valid JSON: {exc}") from exc

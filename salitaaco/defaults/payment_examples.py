# Made-up payments for looking at the design of the payment pages while they
# have no backend. They are shown only when DEBUG is on and the page is opened
# with ?halimbawa=1 (see utils/plans.py), under a notice that says they are not
# real. Delete this file when payments are saved for real.

from datetime import date

from .plans import APPROVED, PENDING, REJECTED

EXAMPLE_TRANSACTIONS = [
    {
        "reference": "HALIMBAWA-003",
        "date": date(2026, 10, 12),
        "guardian": "Halimbawang Magulang",
        "username": "halimbawa1",
        "plan": "SalitAACo Plus",
        "amount": 149,
        "status": PENDING,
        "note": "",
    },
    {
        "reference": "HALIMBAWA-002",
        "date": date(2026, 10, 5),
        "guardian": "Isa Pang Halimbawa",
        "username": "halimbawa2",
        "plan": "SalitAACo Plus",
        "amount": 149,
        "status": APPROVED,
        "note": "",
    },
    {
        "reference": "HALIMBAWA-001",
        "date": date(2026, 9, 28),
        "guardian": "Halimbawang Magulang",
        "username": "halimbawa1",
        "plan": "SalitAACo Plus",
        "amount": 149,
        "status": REJECTED,
        "note": "Malabo ang larawan ng bayad.",
    },
]

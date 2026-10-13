from django.conf import settings

from salitaaco.defaults.payment_examples import EXAMPLE_TRANSACTIONS
from salitaaco.defaults.plans import DEFAULT_PLAN, PAYMENT_STATUSES, PLANS

EXAMPLE_PARAMETER = "halimbawa"


def offered_plans():
    """The plans guardians can choose from."""
    return [plan for plan in PLANS if plan["offered"]]


def current_plan(guardian):
    """
    The plan a guardian is on. Nothing is saved about subscriptions yet, so it
    is the free plan for everyone; this is where the real answer will come from.
    """
    return next(plan for plan in PLANS if plan["key"] == DEFAULT_PLAN)


def examples_can_be_shown():
    """Made-up payments are for looking at the design during development, never on a live site."""
    return settings.DEBUG


def examples_requested(request):
    return examples_can_be_shown() and request.GET.get(EXAMPLE_PARAMETER) == "1"


def transactions(request, status=None):
    """
    The payments a payment page lists, newest first, each with its status's
    name. No payment is saved yet, so the list is empty unless the made-up
    examples were asked for.
    """
    names = dict(PAYMENT_STATUSES)
    rows = [
        {**row, "status_name": names[row["status"]]}
        for row in (EXAMPLE_TRANSACTIONS if examples_requested(request) else [])
    ]
    return [row for row in rows if status is None or row["status"] == status]

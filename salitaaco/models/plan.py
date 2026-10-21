from django.db import models

from salitaaco.defaults.plans import DEFAULT_PLAN, FREE_PERIOD, PAID_PERIOD


class Plan(models.Model):
    """
    A plan a guardian can be on, as the plan page, the public website and Mga
    Subscription show it. An admin edits the name, price, features and whether
    it is offered; plans are not added or deleted. The default plan (Free)
    always costs nothing and is always offered.
    """
    plan_id = models.AutoField(primary_key=True)
    # How the code names a plan (defaults/plans.py); never shown and never edited.
    key = models.SlugField(max_length=20, unique=True)
    name = models.CharField(max_length=60)
    # Whole pesos, per month for a paid plan.
    price = models.PositiveIntegerField(default=0)
    # One feature per line.
    features = models.TextField(blank=True)
    # A plan that is not offered cannot be chosen any more, but stays with whoever is on it.
    offered = models.BooleanField(default=True)
    # The order the plans are shown in.
    position = models.PositiveSmallIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["position", "plan_id"]

    @property
    def is_default(self):
        return self.key == DEFAULT_PLAN

    @property
    def is_free(self):
        return self.price == 0

    @property
    def period(self):
        return FREE_PERIOD if self.is_free else PAID_PERIOD

    @property
    def feature_list(self):
        return [line.strip() for line in self.features.splitlines() if line.strip()]

    def __str__(self):
        return self.name

# pylint: disable=invalid-name
"""Model definition for the WeightLog entity."""
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class WeightLog(models.Model):
    """A single weight measurement logged by a user."""

    user = models.ForeignKey(User, related_name="weight_logs", on_delete=models.CASCADE)
    date = models.DateField(default=timezone.localdate)
    weight = models.DecimalField(
        max_digits=5, decimal_places=2, null=True,
        help_text="Weight in kilogrammes", default=0,
    )

    @property
    def weight_in_lbs(self):
        """Return the weight converted from kg to lbs."""
        if self.weight > 0:
            return self.weight / Decimal('0.45359237')
        return self.weight

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class WeightLog(models.Model):
    user = models.ForeignKey(User, related_name="weight_logs", on_delete=models.CASCADE)
    date = models.DateField(default=timezone.localdate)
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, help_text="Weight in kilogrammes", default=0)

    @property
    def weight_in_lbs(self):
        if self.weight > 0:
            return self.weight / Decimal('0.45359237')
        else:
            return self.weight
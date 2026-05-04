from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    timezone = models.CharField(max_length=64, default="UTC")
    first_name = models.TextField(max_length=64, null=False, default="")
    last_name = models.TextField(max_length=64, null=False, default="")
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, help_text="Weight in kilogrammes", default=0)
    height = models.IntegerField(help_text="Height in centimeters", null=True, default=0)

    @property
    def weight_in_lbs(self):
        if self.weight > 0:
            return self.weight / Decimal('0.45359237')
        else:
            return self.weight

    @property
    def height_in_meters(self):
        if self.height > 0:
            return self.height / 100
        else:
            return self.height

    @property
    def height_in_feet_inches(self):
        if self.height and self.height > 0:
            total_inches = self.height / 2.54
            feet = int(total_inches // 12)
            inches = round(total_inches % 12)
            return f"{feet}'{inches}\""
        return None

    def __str__(self):
        return f"{self.user.username} profile"

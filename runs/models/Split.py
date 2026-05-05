from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from .Workout import Workout


class Split(models.Model):
    workout = models.ForeignKey(Workout, related_name="splits", on_delete=models.CASCADE)
    distance = models.IntegerField(
        null=True,
        help_text="Distance in km",
        validators=[MinValueValidator(1)]
    )
    duration_minutes = models.IntegerField(
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(59)]
    )
    duration_seconds = models.IntegerField(
        null=True,
        help_text="Duration in seconds",
        validators=[MinValueValidator(1), MaxValueValidator(59)]
    )

    def _total_seconds(self):
        return (
            (self.duration_minutes or 0) * 60
            + (self.duration_seconds or 0)
        )

    @property
    def distance_meters(self):
        return self.distance * 1000

    @property
    def split_pace(self):
        total = self._total_seconds()
        if self.distance and self.distance > 0 and total > 0:
            pace_seconds_per_km = total / self.distance

            minutes = int(pace_seconds_per_km // 60)
            seconds = int(pace_seconds_per_km % 60)

            return f"{minutes}:{seconds:02d}"
        return "0:00"

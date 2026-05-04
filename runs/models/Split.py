from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from .Workout import Workout


class Split(models.Model):
    workout = models.ForeignKey(Workout, related_name="splits", on_delete=models.CASCADE)
    distance_meters = models.IntegerField(
        null=True,
        help_text="Distance in meters",
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

    @property
    def duration_minutes(self):
        return self.duration_seconds / 60

    @property
    def distance_kilometers(self):
        return self.distance_meters / 1000

    @property
    def split_pace(self):
        if self.distance_meters and self.distance_meters > 0:
            pace_seconds_per_km = self.duration_seconds / self.distance_kilometers

            minutes = int(pace_seconds_per_km // 60)
            seconds = int(pace_seconds_per_km % 60)

            return f"{minutes}:{seconds:02d}"
        return "00:00"

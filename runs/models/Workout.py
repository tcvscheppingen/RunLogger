from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class Workout(models.Model):
    user = models.ForeignKey(User, related_name="workouts", on_delete=models.CASCADE)
    date = models.DateField(default=timezone.localdate)
    distance = models.FloatField(
        null=True,
        help_text="Distance in kilometers",
        validators=[MinValueValidator(0.01)]
    )
    duration_hours = models.IntegerField(
        null=True,
        validators=[MinValueValidator(0)]
    )
    duration_minutes = models.IntegerField(
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(59)]
    )
    duration_seconds = models.IntegerField(
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(59)]
    )
    notes = models.TextField(blank=True, null=True)
    rpe = models.IntegerField(
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Rate of Perceived Exertion (1-10)",
        default=5
    )

    def _total_seconds(self):
        return (
            (self.duration_hours or 0) * 3600
            + (self.duration_minutes or 0) * 60
            + (self.duration_seconds or 0)
        )

    @property
    def session_load(self):
        return (self._total_seconds() / 60) * self.rpe

    @property
    def pace(self):
        if self.distance and self.distance > 0:
            pace_seconds_per_km = self._total_seconds() / self.distance
            minutes = int(pace_seconds_per_km // 60)
            seconds = int(pace_seconds_per_km % 60)
            return f"{minutes}:{seconds:02d}"
        return "0:00"

    def __str__(self):
        return f"{self.date} - {self.distance}km"

    @property
    def duration_display(self):
        total = self._total_seconds()
        hours = total // 3600
        minutes = (total % 3600) // 60
        seconds = total % 60
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        return f"{minutes}m {seconds}s"
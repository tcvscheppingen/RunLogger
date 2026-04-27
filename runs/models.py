from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class Workout(models.Model):
    user = models.ForeignKey(User, related_name="workouts", on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    distance = models.FloatField(
        help_text="Distance in kilometers",
        validators=[MinValueValidator(0.01)]
    )
    duration_minutes = models.IntegerField(
        validators=[MinValueValidator(1)]
    )
    notes = models.TextField(blank=True, null=True)
    rpe = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Rate of Perceived Exertion (1-10)",
        default=5
    )

    @property
    def session_load(self):
        return self.duration_minutes * self.rpe

    @property
    def pace(self):
        if self.distance and self.distance > 0:
            total_seconds = self.duration_minutes * 60
            pace_seconds_per_km = total_seconds / self.distance
            
            minutes = int(pace_seconds_per_km // 60)
            seconds = int(pace_seconds_per_km % 60)
            
            return f"{minutes}:{seconds:02d}"
        return "0:00"

        def __str__(self):
            return f"{self.date} - {self.distance}km"

    @property
    def duration_display(self):
        total_seconds = int(self.duration_minutes * 60)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        return f"{minutes}m {seconds}s"

class Split(models.Model):
    workout = models.ForeignKey(Workout, related_name="splits", on_delete=models.CASCADE)
    distance_meters = models.IntegerField(
        help_text="Distance in meters",
        validators=[MinValueValidator(1)]
    )
    duration_seconds = models.IntegerField(
        help_text="Duration in seconds",
        validators=[MinValueValidator(1)]
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


    
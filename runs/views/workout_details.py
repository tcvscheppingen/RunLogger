"""View for displaying and updating individual workouts."""
import logging
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from runs.models import Workout

logger = logging.getLogger(__name__)

@login_required
def workout_details(request, pk):
    """View the details of a workout."""
    workout = get_object_or_404(Workout, pk=pk)
    if workout.user != request.user:
        logger.warning(
            "Unauthorized GET request by user %s on workout %s", 
            request.user, pk)
        return HttpResponseForbidden("Access is forbidden")
    context = {
        'workout': workout,
    }

    return render(request, 'runs/workout_details.html', context)

"""View for displaying and updating individual workouts."""
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from runs.models import Workout
from runs.forms import SplitForm

logger = logging.getLogger(__name__)

@login_required
def workout_details(request, pk):
    """View the details of a workout and handle adding splits."""
    workout = get_object_or_404(Workout, pk=pk)
    if workout.user != request.user:
        logger.warning(
            "Unauthorized request by user %s on workout %s",
            request.user, pk)
        return HttpResponseForbidden("Access is forbidden")

    if request.method == "POST":
        form = SplitForm(request.POST)
        if form.is_valid():
            split = form.save(commit=False)
            split.duration_minutes = form.cleaned_data.get('minutes') or 0
            split.duration_seconds = form.cleaned_data.get('seconds') or 0
            split.workout = workout
            split.save()
            return redirect('workout_details', pk=pk)
    else:
        form = SplitForm()

    context = {
        'workout': workout,
        'splits': workout.splits.all(),
        'form': form,
    }

    return render(request, 'runs/workout_details.html', context)

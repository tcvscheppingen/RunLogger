"""Views for deleting individual workout entries and splits."""
import logging
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from runs.models import Workout, Split

logger = logging.getLogger(__name__)


@login_required
def delete_run(request, pk):
    """Delete a workout owned by the current user, or return 403 if unauthorized."""
    if request.method == "POST":
        run = get_object_or_404(Workout, pk=pk)
        if run.user == request.user:
            run.delete()
        else:
            logger.warning(
                "Unauthorized delete attempt by user %s on workout %s", request.user, pk)
            return HttpResponseForbidden("Access is forbidden")
    return redirect('dashboard')


@login_required
def delete_split(request, pk):
    """Delete a split owned by the current user, or return 403 if unauthorized."""
    if request.method == "POST":
        split = get_object_or_404(Split, pk=pk)
        workout_pk = split.workout.pk
        if split.workout.user == request.user:
            split.delete()
        else:
            logger.warning(
                "Unauthorized delete attempt by user %s on split %s", request.user, pk)
            return HttpResponseForbidden("Access is forbidden")
        return redirect('workout_details', pk=workout_pk)
    return redirect('dashboard')

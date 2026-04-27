import json
import logging
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, F
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .models import Workout
from .forms import WorkoutForm
from runs.utils import calculate_training_metrics_for_date
from django.http import HttpResponseForbidden

logger = logging.getLogger(__name__)


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Automatically log them in
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'runs/register.html', {'form': form})


@login_required
def dashboard(request):
    # Handle the form
    if request.method == "POST":
        form = WorkoutForm(request.POST)
        if form.is_valid():
            workout = form.save(commit=False)

            # Use .get() to avoid errors if a field is somehow missing
            h = form.cleaned_data.get('hours') or 0
            m = form.cleaned_data.get('minutes') or 0
            s = form.cleaned_data.get('seconds') or 0

            workout.duration_minutes = float(
                h * 60) + float(m) + (float(s) / 60.0)
            workout.user = request.user
            workout.save()
            return redirect('dashboard')
    else:
        form = WorkoutForm()

    # Get current time for filtering
    now = timezone.now()

    # Calculate Monthly Stats
    monthly_workouts = Workout.objects.filter(
        date__year=now.year, date__month=now.month)

    # .aggregate returns a dictionary, e.g., {'distance__sum': 42.5}
    total_distance = monthly_workouts.aggregate(
        Sum('distance'))['distance__sum'] or 0
    total_runs = monthly_workouts.count()

    workouts = request.user.workouts.all().order_by('-date')

    current_metrics = calculate_training_metrics_for_date(
        request.user, timezone.now().date())

    dates = []
    atl_data = []
    ctl_data = []

    today = timezone.now().date()
    for i in range(29, -1, -1):
        day = today - timedelta(days=i)
        dates.append(day.strftime('%b %d'))

        # Simple rolling average logic for the chart
        # In a production app, you might pre-calculate this in a separate table
        metrics = calculate_training_metrics_for_date(request.user, day)
        atl_data.append(metrics['atl'])
        ctl_data.append(metrics['ctl'])

    context = {
        'workouts': workouts,
        'metrics': current_metrics,
        'form': form,
        'total_distance': round(total_distance, 2),
        'total_runs': total_runs,
        'current_month': now.strftime('%B'),
        'chart_dates': dates,
        'chart_atl': atl_data,
        'chart_ctl': ctl_data,
        'ctl_info': "Chronic Training Load: Your 6-week rolling average of stress. This represents your long-term 'base' or aerobic engine.",
        'atl_info': "Acute Training Load: Your 7-day rolling average of stress. This tracks your recent fatigue and how hard you've worked this week.",
        'status_info': "Training Ratio (ATL/CTL): 0.8–1.3 is Productive; over 1.5 is the Danger Zone (high injury risk).",
        'rpe_info': "Rate of Perceived Exertion: A 1-10 scale of how hard the run felt. 1 is a light walk, 10 is an all-out max effort.",
    }

    return render(request, 'runs/dashboard.html', context)


@login_required
def delete_run(request, pk):
    if request.method == "POST":
        run = get_object_or_404(Workout, pk=pk)
        if run.user == request.user:
            run.delete()
        else:
            logger.warning(
                "Unauthorized delete attempt by user %s on workout %s", request.user, pk)
            return HttpResponseForbidden("Access is forbidden")
    return redirect('dashboard')

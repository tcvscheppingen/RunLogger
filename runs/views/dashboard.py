from datetime import timedelta
from django.shortcuts import render, redirect
from django.db.models import Sum
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from runs.models import Workout
from runs.forms import WorkoutForm
from runs.utils import calculate_training_metrics_for_date


@login_required
def dashboard(request):
    if request.method == "POST":
        form = WorkoutForm(request.POST)
        if form.is_valid():
            workout = form.save(commit=False)

            h = form.cleaned_data.get('hours') or 0
            m = form.cleaned_data.get('minutes') or 0
            s = form.cleaned_data.get('seconds') or 0

            workout.duration_hours = h
            workout.duration_minutes = m
            workout.duration_seconds = s
            workout.user = request.user
            workout.save()
            return redirect('dashboard')
    else:
        form = WorkoutForm()

    now = timezone.now()

    monthly_workouts = Workout.objects.filter(
        date__year=now.year, date__month=now.month, user=request.user)

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

        metrics = calculate_training_metrics_for_date(request.user, day)
        atl_data.append(metrics['atl'])
        ctl_data.append(metrics['ctl'])

    has_baseline = request.user.workouts.filter(
        date__lt=today - timedelta(days=7)
    ).exists()

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
        'has_baseline': has_baseline,
        'ctl_info': "Chronic Training Load: Your 6-week rolling average of stress. This represents your long-term 'base' or aerobic engine.",
        'atl_info': "Acute Training Load: Your 7-day rolling average of stress. This tracks your recent fatigue and how hard you've worked this week.",
        'status_info': "Training Ratio (ATL/CTL): 0.8–1.3 is Productive; over 1.5 is the Danger Zone (high injury risk).",
        'rpe_info': "Rate of Perceived Exertion: A 1-10 scale of how hard the run felt. 1 is a light walk, 10 is an all-out max effort.",
    }

    return render(request, 'runs/dashboard.html', context)

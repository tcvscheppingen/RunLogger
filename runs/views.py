import csv
import io
import json
import logging
from datetime import timedelta, date as date_type
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, F
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Workout
from .forms import WorkoutForm
from runs.utils import calculate_training_metrics_for_date
from django.http import HttpResponse, HttpResponseForbidden

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

            workout.duration_hours = h
            workout.duration_minutes = m
            workout.duration_seconds = s
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
def export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="runs_export.csv"'

    writer = csv.writer(response)
    writer.writerow(['date', 'distance_km', 'duration_hours', 'duration_minutes', 'duration_seconds', 'notes', 'rpe'])

    for workout in Workout.objects.filter(user=request.user).order_by('-date'):
        writer.writerow([
            workout.date,
            workout.distance,
            workout.duration_hours or 0,
            workout.duration_minutes or 0,
            workout.duration_seconds or 0,
            workout.notes or '',
            workout.rpe,
        ])

    return response


@login_required
def import_csv(request):
    if request.method != 'POST':
        return redirect('dashboard')

    csv_file = request.FILES.get('csv_file')
    if not csv_file:
        messages.warning(request, 'No file was uploaded.')
        return redirect('dashboard')

    try:
        text = csv_file.read().decode('utf-8')
    except UnicodeDecodeError:
        messages.warning(request, 'Could not read the file — make sure it is a UTF-8 encoded CSV.')
        return redirect('dashboard')

    reader = csv.DictReader(io.StringIO(text))
    imported = 0
    skipped = 0
    to_create = []

    for row in reader:
        try:
            row_date = date_type.fromisoformat(row['date'].strip())

            distance = float(row['distance_km'])
            if distance < 0.01:
                raise ValueError

            hours = int(row.get('duration_hours') or 0)
            minutes = int(row.get('duration_minutes') or 0)
            seconds = int(row.get('duration_seconds') or 0)
            if hours < 0 or minutes < 0 or seconds < 0:
                raise ValueError

            rpe = int(row['rpe'])
            if not (1 <= rpe <= 10):
                raise ValueError

            notes = row.get('notes', '') or ''

            to_create.append(Workout(
                user=request.user,
                date=row_date,
                distance=distance,
                duration_hours=hours,
                duration_minutes=minutes,
                duration_seconds=seconds,
                notes=notes,
                rpe=rpe,
            ))
            imported += 1
        except (KeyError, ValueError, AttributeError):
            skipped += 1

    if to_create:
        Workout.objects.bulk_create(to_create)

    msg = f'Imported {imported} run{"s" if imported != 1 else ""}.'
    if skipped:
        msg += f' {skipped} row{"s" if skipped != 1 else ""} skipped due to invalid data.'
        messages.warning(request, msg)
    else:
        messages.success(request, msg)

    return redirect('dashboard')


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

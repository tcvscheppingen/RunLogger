"""Views for CSV export and import of workout data."""
import csv
import io
from datetime import date as date_type
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from runs.models import Workout


def _sanitize_csv_value(value):
    """Prefix formulae-triggering characters to prevent CSV injection in spreadsheets."""
    if isinstance(value, str) and value and value[0] in ('=', '+', '-', '@', '\t', '\r'):
        return "'" + value
    return value


@login_required
def export_csv(request):
    """Return a CSV file containing all workouts for the logged-in user."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="runs_export.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'date', 'distance_km', 'duration_hours',
        'duration_minutes', 'duration_seconds', 'notes', 'rpe',
    ])

    for workout in Workout.objects.filter(user=request.user).order_by('-date'):
        writer.writerow([
            workout.date,
            workout.distance,
            workout.duration_hours or 0,
            workout.duration_minutes or 0,
            workout.duration_seconds or 0,
            _sanitize_csv_value(workout.notes or ''),
            workout.rpe,
        ])

    return response


@login_required
def import_csv(request):
    """Import workouts from an uploaded CSV file into the user's account."""
    if request.method != 'POST':
        return redirect('dashboard')

    csv_file = request.FILES.get('csv_file')
    if not csv_file:
        messages.warning(request, 'No file was uploaded.')
        return redirect('dashboard')

    max_size = 5 * 1024 * 1024  # 5 MB
    if csv_file.size > max_size:
        messages.warning(request, 'File too large — maximum size is 5 MB.')
        return redirect('dashboard')

    if not csv_file.name.lower().endswith('.csv'):
        messages.warning(request, 'Only .csv files are accepted.')
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
            if rpe < 1 or rpe > 10:
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

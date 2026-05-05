"""Utility functions for training load calculations."""
from datetime import timedelta
from django.db.models import Sum, F


def calculate_training_metrics_for_date(user, target_date):
    """Return ATL, CTL, TSB and training ratio for a user on a given date."""
    # Acute: 7 days | Chronic: 42 days
    def get_load_for_period(days):
        start_date = target_date - timedelta(days=days)
        # We calculate: duration * rpe for every run in this window
        total_minutes = (
            F('duration_hours') * 60
            + F('duration_minutes')
            + F('duration_seconds') / 60.0
        )
        result = user.workouts.filter(
            date__gt=start_date,
            date__lte=target_date
        ).aggregate(
            total=Sum(total_minutes * F('rpe'))
        )['total'] or 0
        return result / days

    atl = get_load_for_period(7)
    ctl = get_load_for_period(42)
    ratio = atl / ctl if ctl > 0 else 0

    return {
        'atl': round(atl, 1),
        'ctl': round(ctl, 1),
        'tsb': round(ctl - atl, 1),
        'ratio': round(ratio, 2)
    }

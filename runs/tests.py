from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Workout
from .forms import WorkoutForm
from .utils import calculate_training_metrics_for_date
from datetime import date, timedelta


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_workout(user, **kwargs):
    defaults = dict(distance=10.0, duration_minutes=60, rpe=5)
    defaults.update(kwargs)
    return Workout.objects.create(user=user, **defaults)


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

class WorkoutModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='runner', password='testpass123')

    def test_session_load(self):
        workout = make_workout(self.user, duration_minutes=30, rpe=8)
        self.assertEqual(workout.session_load, 240)

    def test_pace_round_minutes(self):
        # 60 min over 10 km → 6:00 /km
        workout = make_workout(self.user, distance=10.0, duration_minutes=60)
        self.assertEqual(workout.pace, '6:00')

    def test_pace_with_leftover_seconds(self):
        # 30 min over 8 km → 225 s/km → 3:45 /km
        workout = make_workout(self.user, distance=8.0, duration_minutes=30)
        self.assertEqual(workout.pace, '3:45')

    def test_pace_zero_distance_returns_placeholder(self):
        workout = make_workout(self.user, distance=0.0, duration_minutes=30)
        self.assertEqual(workout.pace, '0:00')

    def test_duration_display_with_hours(self):
        workout = make_workout(self.user, duration_minutes=90)
        self.assertEqual(workout.duration_display, '1h 30m 0s')

    def test_duration_display_minutes_only(self):
        workout = make_workout(self.user, duration_minutes=45)
        self.assertEqual(workout.duration_display, '45m 0s')

    def test_distance_validator_rejects_zero(self):
        workout = Workout(user=self.user, distance=0.0, duration_minutes=30, rpe=5)
        with self.assertRaises(ValidationError):
            workout.full_clean()

    def test_distance_validator_rejects_negative(self):
        workout = Workout(user=self.user, distance=-5.0, duration_minutes=30, rpe=5)
        with self.assertRaises(ValidationError):
            workout.full_clean()

    def test_distance_validator_accepts_positive(self):
        workout = Workout(user=self.user, distance=0.5, duration_minutes=30, rpe=5)
        try:
            workout.full_clean()
        except ValidationError as e:
            self.fail(f"Unexpected ValidationError for valid distance: {e}")

    def test_duration_validator_rejects_zero(self):
        workout = Workout(user=self.user, distance=5.0, duration_minutes=0, rpe=5)
        with self.assertRaises(ValidationError):
            workout.full_clean()

    def test_duration_validator_rejects_negative(self):
        workout = Workout(user=self.user, distance=5.0, duration_minutes=-10, rpe=5)
        with self.assertRaises(ValidationError):
            workout.full_clean()

    def test_rpe_validator_rejects_above_max(self):
        workout = Workout(user=self.user, distance=5.0, duration_minutes=30, rpe=11)
        with self.assertRaises(ValidationError):
            workout.full_clean()

    def test_rpe_validator_rejects_below_min(self):
        workout = Workout(user=self.user, distance=5.0, duration_minutes=30, rpe=0)
        with self.assertRaises(ValidationError):
            workout.full_clean()


# ---------------------------------------------------------------------------
# Form tests
# ---------------------------------------------------------------------------

class WorkoutFormTests(TestCase):
    def _post_data(self, **overrides):
        data = {'distance': '10', 'hours': '0', 'minutes': '30', 'seconds': '0', 'rpe': '5', 'notes': ''}
        data.update({k: str(v) for k, v in overrides.items()})
        return data

    def test_valid_form_is_accepted(self):
        self.assertTrue(WorkoutForm(data=self._post_data()).is_valid())

    def test_rpe_above_max_is_rejected(self):
        self.assertFalse(WorkoutForm(data=self._post_data(rpe=11)).is_valid())

    def test_rpe_below_min_is_rejected(self):
        self.assertFalse(WorkoutForm(data=self._post_data(rpe=0)).is_valid())

    def test_negative_distance_is_rejected(self):
        self.assertFalse(WorkoutForm(data=self._post_data(distance=-1)).is_valid())

    def test_negative_minutes_is_rejected(self):
        self.assertFalse(WorkoutForm(data=self._post_data(minutes=-1)).is_valid())

    def test_missing_distance_is_rejected(self):
        data = self._post_data()
        del data['distance']
        self.assertFalse(WorkoutForm(data=data).is_valid())

    def test_optional_notes_field_can_be_empty(self):
        form = WorkoutForm(data=self._post_data(notes=''))
        self.assertTrue(form.is_valid())


# ---------------------------------------------------------------------------
# Authorization tests
# ---------------------------------------------------------------------------

class AuthorizationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='runner', password='testpass123')
        self.other_user = User.objects.create_user(username='stranger', password='testpass123')

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")

    def test_delete_requires_login(self):
        run = make_workout(self.user)
        response = self.client.post(reverse('delete_run', args=[run.pk]))
        login_url = f"{reverse('login')}?next={reverse('delete_run', args=[run.pk])}"
        self.assertRedirects(response, login_url)
        self.assertTrue(Workout.objects.filter(pk=run.pk).exists())

    def test_user_cannot_delete_another_users_run(self):
        run = make_workout(self.other_user)
        self.client.login(username='runner', password='testpass123')
        response = self.client.post(reverse('delete_run', args=[run.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Workout.objects.filter(pk=run.pk).exists())

    def test_user_can_delete_own_run(self):
        run = make_workout(self.user)
        self.client.login(username='runner', password='testpass123')
        response = self.client.post(reverse('delete_run', args=[run.pk]))
        self.assertRedirects(response, reverse('dashboard'))
        self.assertFalse(Workout.objects.filter(pk=run.pk).exists())

    def test_delete_nonexistent_run_returns_404(self):
        self.client.login(username='runner', password='testpass123')
        response = self.client.post(reverse('delete_run', args=[99999]))
        self.assertEqual(response.status_code, 404)

    def test_delete_via_get_does_not_delete(self):
        run = make_workout(self.user)
        self.client.login(username='runner', password='testpass123')
        self.client.get(reverse('delete_run', args=[run.pk]))
        self.assertTrue(Workout.objects.filter(pk=run.pk).exists())


# ---------------------------------------------------------------------------
# Dashboard view tests
# ---------------------------------------------------------------------------

class DashboardViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='runner', password='testpass123')
        self.client.login(username='runner', password='testpass123')

    def _post_run(self, **overrides):
        data = {'distance': '10', 'hours': '0', 'minutes': '30', 'seconds': '0', 'rpe': '5', 'notes': ''}
        data.update({k: str(v) for k, v in overrides.items()})
        return self.client.post(reverse('dashboard'), data)

    def test_dashboard_renders_for_logged_in_user(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_post_creates_workout(self):
        self._post_run()
        self.assertEqual(Workout.objects.filter(user=self.user).count(), 1)

    def test_dashboard_post_assigns_workout_to_current_user(self):
        self._post_run(distance='5')
        run = Workout.objects.get(user=self.user)
        self.assertEqual(run.user, self.user)

    def test_dashboard_post_redirects_on_success(self):
        response = self._post_run()
        self.assertRedirects(response, reverse('dashboard'))

    def test_hh_mm_ss_conversion_to_decimal_minutes(self):
        # 1h 30m 0s = exactly 90 minutes (whole number avoids IntegerField truncation)
        self._post_run(distance='10', hours='1', minutes='30', seconds='0')
        run = Workout.objects.get(user=self.user)
        self.assertAlmostEqual(float(run.duration_minutes), 90.0, places=1)

    def test_invalid_rpe_not_saved_to_db(self):
        self._post_run(rpe='11')
        self.assertFalse(Workout.objects.filter(rpe=11).exists())

    def test_workouts_appear_in_context(self):
        make_workout(self.user)
        response = self.client.get(reverse('dashboard'))
        self.assertIn('workouts', response.context)
        self.assertEqual(len(response.context['workouts']), 1)

    def test_workouts_only_show_own_runs(self):
        other = User.objects.create_user(username='stranger', password='testpass123')
        make_workout(self.user)
        make_workout(other)
        response = self.client.get(reverse('dashboard'))
        # All workouts returned by the queryset should belong to the logged-in user
        for run in response.context['workouts']:
            self.assertEqual(run.user, self.user)

    def test_chart_context_variables_present(self):
        response = self.client.get(reverse('dashboard'))
        for key in ('chart_dates', 'chart_atl', 'chart_ctl'):
            self.assertIn(key, response.context)

    def test_total_distance_reflects_monthly_runs(self):
        make_workout(self.user, distance=5.0, duration_minutes=25)
        make_workout(self.user, distance=10.0, duration_minutes=50)
        response = self.client.get(reverse('dashboard'))
        self.assertAlmostEqual(response.context['total_distance'], 15.0, places=2)


# ---------------------------------------------------------------------------
# Registration tests
# ---------------------------------------------------------------------------

class RegistrationTests(TestCase):
    def setUp(self):
        self.client = Client()

    def _register(self, username='newrunner', pw='complexpass123!'):
        return self.client.post(reverse('register'), {
            'username': username,
            'password1': pw,
            'password2': pw,
        })

    def test_register_creates_user(self):
        self._register()
        self.assertTrue(User.objects.filter(username='newrunner').exists())

    def test_register_redirects_to_dashboard(self):
        response = self._register()
        self.assertRedirects(response, reverse('dashboard'))

    def test_register_logs_user_in_automatically(self):
        self._register()
        # If session is active, dashboard is accessible without redirect
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_mismatched_passwords_do_not_create_user(self):
        self.client.post(reverse('register'), {
            'username': 'newrunner',
            'password1': 'complexpass123!',
            'password2': 'different456!',
        })
        self.assertFalse(User.objects.filter(username='newrunner').exists())

    def test_duplicate_username_fails(self):
        User.objects.create_user(username='taken', password='testpass123')
        self._register(username='taken')
        self.assertEqual(User.objects.filter(username='taken').count(), 1)


# ---------------------------------------------------------------------------
# Training metrics (utils) tests
# ---------------------------------------------------------------------------

class TrainingMetricsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='runner', password='testpass123')

    def test_no_workouts_returns_all_zeros(self):
        metrics = calculate_training_metrics_for_date(self.user, date.today())
        self.assertEqual(metrics['atl'], 0.0)
        self.assertEqual(metrics['ctl'], 0.0)
        self.assertEqual(metrics['tsb'], 0.0)
        self.assertEqual(metrics['ratio'], 0)

    def test_single_workout_atl_and_ctl_values(self):
        # 60 min * RPE 10 = 600 load
        # ATL = 600 / 7 ≈ 85.7, CTL = 600 / 42 ≈ 14.3
        make_workout(self.user, distance=10, duration_minutes=60, rpe=10)
        metrics = calculate_training_metrics_for_date(self.user, date.today())
        self.assertAlmostEqual(metrics['atl'], 85.7, places=1)
        self.assertAlmostEqual(metrics['ctl'], 14.3, places=1)

    def test_ratio_is_overreaching_after_high_load(self):
        make_workout(self.user, distance=10, duration_minutes=60, rpe=10)
        metrics = calculate_training_metrics_for_date(self.user, date.today())
        self.assertGreater(metrics['ratio'], 1.5)

    def test_ratio_is_zero_with_no_workouts(self):
        metrics = calculate_training_metrics_for_date(self.user, date.today())
        self.assertEqual(metrics['ratio'], 0)

    def test_tsb_equals_ctl_minus_atl(self):
        make_workout(self.user, distance=10, duration_minutes=60, rpe=10)
        metrics = calculate_training_metrics_for_date(self.user, date.today())
        self.assertAlmostEqual(metrics['tsb'], metrics['ctl'] - metrics['atl'], places=1)

    def test_workout_beyond_atl_window_not_in_atl(self):
        # Workout 8 days ago falls outside the 7-day ATL window.
        # auto_now_add ignores create() kwargs, so we update() after creation.
        run = make_workout(self.user, distance=10, duration_minutes=60, rpe=10)
        Workout.objects.filter(pk=run.pk).update(date=date.today() - timedelta(days=8))
        metrics = calculate_training_metrics_for_date(self.user, date.today())
        self.assertEqual(metrics['atl'], 0.0)

    def test_workout_beyond_ctl_window_not_counted(self):
        # Workout 43 days ago falls outside the 42-day CTL window.
        run = make_workout(self.user, distance=10, duration_minutes=60, rpe=10)
        Workout.objects.filter(pk=run.pk).update(date=date.today() - timedelta(days=43))
        metrics = calculate_training_metrics_for_date(self.user, date.today())
        self.assertEqual(metrics['ctl'], 0.0)

    def test_metrics_isolated_per_user(self):
        other = User.objects.create_user(username='other', password='testpass123')
        make_workout(other, distance=10, duration_minutes=60, rpe=10)
        metrics = calculate_training_metrics_for_date(self.user, date.today())
        self.assertEqual(metrics['atl'], 0.0)
        self.assertEqual(metrics['ctl'], 0.0)

    def test_multiple_workouts_accumulate_load(self):
        # Two workouts of 300 load each (30 min * RPE 10) should equal
        # one workout of 600 load (60 min * RPE 10).
        make_workout(self.user, distance=5, duration_minutes=30, rpe=10)
        make_workout(self.user, distance=5, duration_minutes=30, rpe=10)
        two_runs = calculate_training_metrics_for_date(self.user, date.today())

        self.user.workouts.all().delete()
        make_workout(self.user, distance=10, duration_minutes=60, rpe=10)
        one_run = calculate_training_metrics_for_date(self.user, date.today())

        self.assertAlmostEqual(two_runs['atl'], one_run['atl'], places=1)
        self.assertAlmostEqual(two_runs['ctl'], one_run['ctl'], places=1)

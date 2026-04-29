import io
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Workout
from .forms import WorkoutForm
from .utils import calculate_training_metrics_for_date
from datetime import date, timedelta


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_workout(user, **kwargs):
    defaults = dict(distance=10.0, duration_hours=0, duration_minutes=60, duration_seconds=0, rpe=5)
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

    def _workout(self, **kwargs):
        defaults = dict(distance=5.0, duration_hours=0, duration_minutes=30, duration_seconds=0, rpe=5)
        defaults.update(kwargs)
        return Workout(user=self.user, **defaults)

    def test_distance_validator_rejects_zero(self):
        with self.assertRaises(ValidationError):
            self._workout(distance=0.0).full_clean()

    def test_distance_validator_rejects_negative(self):
        with self.assertRaises(ValidationError):
            self._workout(distance=-5.0).full_clean()

    def test_distance_validator_accepts_positive(self):
        try:
            self._workout(distance=0.5).full_clean()
        except ValidationError as e:
            self.fail(f"Unexpected ValidationError for valid distance: {e}")

    def test_duration_validator_rejects_negative(self):
        with self.assertRaises(ValidationError):
            self._workout(duration_minutes=-10).full_clean()

    def test_rpe_validator_rejects_above_max(self):
        with self.assertRaises(ValidationError):
            self._workout(rpe=11).full_clean()

    def test_rpe_validator_rejects_below_min(self):
        with self.assertRaises(ValidationError):
            self._workout(rpe=0).full_clean()


# ---------------------------------------------------------------------------
# Form tests
# ---------------------------------------------------------------------------

class WorkoutFormTests(TestCase):
    def _post_data(self, **overrides):
        data = {'date': '2026-01-01', 'distance': '10', 'hours': '0', 'minutes': '30', 'seconds': '0', 'rpe': '5', 'notes': ''}
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
        data = {'date': '2026-01-01', 'distance': '10', 'hours': '0', 'minutes': '30', 'seconds': '0', 'rpe': '5', 'notes': ''}
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

    def test_hh_mm_ss_stored_as_separate_components(self):
        self._post_run(distance='10', hours='1', minutes='30', seconds='0')
        run = Workout.objects.get(user=self.user)
        self.assertEqual(run.duration_hours, 1)
        self.assertEqual(run.duration_minutes, 30)
        self.assertEqual(run.duration_seconds, 0)
        self.assertEqual(run.duration_display, '1h 30m 0s')

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


# ---------------------------------------------------------------------------
# Export tests
# ---------------------------------------------------------------------------

def make_csv(rows, header='date,distance_km,duration_hours,duration_minutes,duration_seconds,notes,rpe'):
    lines = [header] + [','.join(str(v) for v in row) for row in rows]
    return SimpleUploadedFile('runs.csv', '\n'.join(lines).encode('utf-8'), content_type='text/csv')


class ExportCSVTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='runner', password='testpass123')
        self.client.login(username='runner', password='testpass123')

    def test_export_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('export_csv'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('export_csv')}")

    def test_export_returns_csv_content_type(self):
        response = self.client.get(reverse('export_csv'))
        self.assertEqual(response['Content-Type'], 'text/csv')

    def test_export_has_correct_header_row(self):
        response = self.client.get(reverse('export_csv'))
        first_line = response.content.decode('utf-8').splitlines()[0]
        self.assertEqual(first_line, 'date,distance_km,duration_hours,duration_minutes,duration_seconds,notes,rpe')

    def test_export_contains_workout_data(self):
        make_workout(self.user, distance=8.5, duration_hours=0, duration_minutes=40, duration_seconds=0, rpe=6)
        response = self.client.get(reverse('export_csv'))
        content = response.content.decode('utf-8')
        self.assertIn('8.5', content)
        self.assertIn('40', content)
        self.assertIn('6', content)

    def test_export_preserves_date(self):
        run = make_workout(self.user, distance=5.0, duration_minutes=25, rpe=5)
        Workout.objects.filter(pk=run.pk).update(date=date(2024, 3, 15))
        response = self.client.get(reverse('export_csv'))
        self.assertIn('2024-03-15', response.content.decode('utf-8'))

    def test_export_only_includes_own_workouts(self):
        other = User.objects.create_user(username='stranger', password='testpass123')
        make_workout(self.user, distance=5.0, duration_minutes=25, rpe=5)
        make_workout(other, distance=99.0, duration_minutes=25, rpe=5)
        response = self.client.get(reverse('export_csv'))
        content = response.content.decode('utf-8')
        data_rows = [l for l in content.splitlines() if l and not l.startswith('date')]
        self.assertEqual(len(data_rows), 1)
        self.assertNotIn('99.0', content)

    def test_export_empty_produces_only_header(self):
        response = self.client.get(reverse('export_csv'))
        lines = [l for l in response.content.decode('utf-8').splitlines() if l]
        self.assertEqual(len(lines), 1)


# ---------------------------------------------------------------------------
# Import tests
# ---------------------------------------------------------------------------

class ImportCSVTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='runner', password='testpass123')
        self.client.login(username='runner', password='testpass123')

    def _post_csv(self, csv_file):
        return self.client.post(reverse('import_csv'), {'csv_file': csv_file})

    def test_import_requires_login(self):
        self.client.logout()
        csv_file = make_csv([['2024-01-01', 10.0, 0, 60, 0, '', 5]])
        response = self.client.post(reverse('import_csv'), {'csv_file': csv_file})
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('import_csv')}")

    def test_import_get_redirects_to_dashboard(self):
        response = self.client.get(reverse('import_csv'))
        self.assertRedirects(response, reverse('dashboard'))

    def test_import_creates_workouts(self):
        csv_file = make_csv([
            ['2024-01-10', 10.0, 0, 60, 0, '', 5],
            ['2024-01-11', 5.0, 0, 30, 0, 'easy run', 3],
        ])
        self._post_csv(csv_file)
        self.assertEqual(Workout.objects.filter(user=self.user).count(), 2)

    def test_import_preserves_date_from_csv(self):
        csv_file = make_csv([['2023-06-15', 10.0, 0, 60, 0, '', 5]])
        self._post_csv(csv_file)
        run = Workout.objects.get(user=self.user)
        self.assertEqual(run.date, date(2023, 6, 15))

    def test_import_assigns_workouts_to_current_user(self):
        csv_file = make_csv([['2024-01-01', 10.0, 0, 60, 0, '', 5]])
        self._post_csv(csv_file)
        run = Workout.objects.get(user=self.user)
        self.assertEqual(run.user, self.user)

    def test_import_sets_all_fields_correctly(self):
        csv_file = make_csv([['2024-02-20', 12.5, 1, 15, 30, 'long run', 7]])
        self._post_csv(csv_file)
        run = Workout.objects.get(user=self.user)
        self.assertAlmostEqual(run.distance, 12.5)
        self.assertEqual(run.duration_hours, 1)
        self.assertEqual(run.duration_minutes, 15)
        self.assertEqual(run.duration_seconds, 30)
        self.assertEqual(run.notes, 'long run')
        self.assertEqual(run.rpe, 7)

    def test_import_shows_success_message(self):
        csv_file = make_csv([['2024-01-01', 10.0, 0, 60, 0, '', 5]])
        response = self._post_csv(csv_file)
        messages = [str(m) for m in response.wsgi_request._messages]
        self.assertTrue(any('Imported 1 run' in m for m in messages))

    def test_import_skips_invalid_rows_and_reports_count(self):
        csv_file = make_csv([
            ['2024-01-01', 10.0, 0, 60, 0, '', 5],   # valid
            ['not-a-date', 10.0, 0, 60, 0, '', 5],   # invalid date
            ['2024-01-03', -1.0, 0, 60, 0, '', 5],   # invalid distance
        ])
        self._post_csv(csv_file)
        self.assertEqual(Workout.objects.filter(user=self.user).count(), 1)

    def test_import_skips_rpe_out_of_range(self):
        csv_file = make_csv([
            ['2024-01-01', 10.0, 0, 60, 0, '', 11],  # rpe too high
            ['2024-01-02', 10.0, 0, 60, 0, '', 0],   # rpe too low
        ])
        self._post_csv(csv_file)
        self.assertEqual(Workout.objects.filter(user=self.user).count(), 0)

    def test_import_skips_distance_below_minimum(self):
        csv_file = make_csv([['2024-01-01', 0.001, 0, 60, 0, '', 5]])
        self._post_csv(csv_file)
        self.assertEqual(Workout.objects.filter(user=self.user).count(), 0)

    def test_import_shows_warning_when_rows_skipped(self):
        csv_file = make_csv([
            ['2024-01-01', 10.0, 0, 60, 0, '', 5],
            ['bad-row', 'x', 0, 0, 0, '', 5],
        ])
        response = self._post_csv(csv_file)
        msgs = [str(m) for m in response.wsgi_request._messages]
        self.assertTrue(any('skipped' in m for m in msgs))

    def test_import_no_file_shows_warning(self):
        response = self.client.post(reverse('import_csv'), {})
        msgs = [str(m) for m in response.wsgi_request._messages]
        self.assertTrue(any(m for m in msgs))
        self.assertEqual(Workout.objects.filter(user=self.user).count(), 0)

    def test_import_invalid_utf8_shows_warning(self):
        bad_file = SimpleUploadedFile('runs.csv', b'\xff\xfe bad bytes', content_type='text/csv')
        response = self._post_csv(bad_file)
        msgs = [str(m) for m in response.wsgi_request._messages]
        self.assertTrue(any(m for m in msgs))
        self.assertEqual(Workout.objects.filter(user=self.user).count(), 0)

    def test_import_redirects_to_dashboard_on_success(self):
        csv_file = make_csv([['2024-01-01', 10.0, 0, 60, 0, '', 5]])
        response = self._post_csv(csv_file)
        self.assertRedirects(response, reverse('dashboard'))

    def test_import_does_not_create_workouts_for_other_users(self):
        other = User.objects.create_user(username='stranger', password='testpass123')
        csv_file = make_csv([['2024-01-01', 10.0, 0, 60, 0, '', 5]])
        self._post_csv(csv_file)
        self.assertEqual(Workout.objects.filter(user=other).count(), 0)

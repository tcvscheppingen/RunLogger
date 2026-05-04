import zoneinfo
from django import forms
from django.utils import timezone
from .models import Workout, Split, UserProfile

_TIMEZONE_CHOICES = [(tz, tz) for tz in sorted(zoneinfo.available_timezones())]


class WorkoutForm(forms.ModelForm):
    hours = forms.IntegerField(
        min_value=0, required=False,
        widget=forms.NumberInput(
            attrs={'class': 'w-full rounded-md border-slate-300 shadow-sm', 'placeholder': '0'})
    )
    minutes = forms.IntegerField(
        min_value=0, max_value=59, required=False,
        widget=forms.NumberInput(
            attrs={'class': 'w-full rounded-md border-slate-300 shadow-sm', 'placeholder': '0'})
    )
    seconds = forms.IntegerField(
        min_value=0, max_value=59, required=False,
        widget=forms.NumberInput(
            attrs={'type': 'number', 'class': 'w-full rounded-md border-slate-300 shadow-sm', 'placeholder': '0'})
    )

    class Meta:
        model = Workout
        fields = ['date', 'distance', 'hours',
                  'minutes', 'seconds', 'notes', 'rpe']

        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': (
                    'w-full h-[42px] rounded-md border-slate-300 shadow-sm '
                    'focus:border-blue-500 focus:ring-blue-500 '
                    'dark:bg-slate-800 dark:border-slate-700 dark:text-slate-100'
                ),
                'placeholder': timezone.now().date(),
            }),
            'distance': forms.NumberInput(attrs={'class': 'w-full rounded-md border-slate-300 shadow-sm focus:border-blue-500 focus:ring-blue-500', 'placeholder': '0.0'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'w-full pl-2 rounded-md border-slate-300 shadow-sm focus:border-blue-500 focus:ring-blue-500', 'placeholder': 'How did it feel?'}),
            'rpe': forms.NumberInput(attrs={
                'type': 'range',
                'min': '0',
                'max': '10',
                'step': '1',
                'class': 'w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer'
            }),
        }


class SplitForm(forms.ModelForm):
    class Meta:
        model = Split

        fields = ['distance_meters', 'duration_seconds']


_input_classes = (
    'w-full rounded-md border-slate-300 shadow-sm '
    'focus:border-blue-500 focus:ring-blue-500 '
    'dark:bg-slate-800 dark:border-slate-700 dark:text-slate-100'
)


_select_classes = (
    'w-full rounded-md border border-slate-300 shadow-sm px-3 py-2 text-sm '
    'focus:border-blue-500 focus:ring-blue-500 '
    'dark:bg-slate-800 dark:border-slate-700 dark:text-slate-100'
)


class UserProfileForm(forms.ModelForm):
    timezone = forms.ChoiceField(
        choices=_TIMEZONE_CHOICES,
        widget=forms.Select(attrs={'class': _select_classes}),
    )

    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'weight', 'height', 'timezone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': _input_classes, 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': _input_classes, 'placeholder': 'e.g. van der Berg'}),
            'weight': forms.NumberInput(attrs={'class': _input_classes, 'placeholder': '70.00', 'step': '0.01'}),
            'height': forms.NumberInput(attrs={'class': _input_classes, 'placeholder': '180'}),
        }

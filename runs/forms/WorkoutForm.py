# pylint: disable=invalid-name
"""Form for logging a new workout."""
from django import forms
from django.utils import timezone
from runs.models import Workout
from runs.forms.fields import INPUT_CLASSES, FOCUS_CLASSES, minutes_field, seconds_field


class WorkoutForm(forms.ModelForm):
    """ModelForm for creating or editing a Workout, with separate h/m/s fields."""

    hours = forms.IntegerField(
        min_value=0, required=False,
        widget=forms.NumberInput(
            attrs={'class': INPUT_CLASSES, 'placeholder': '0'})
    )
    minutes = minutes_field()
    seconds = seconds_field()

    class Meta:
        """Meta options: model, fields and Tailwind-styled widgets."""

        model = Workout
        fields = ['date', 'distance', 'hours', 'minutes', 'seconds', 'notes', 'rpe']

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
            'distance': forms.NumberInput(
                attrs={'class': FOCUS_CLASSES, 'placeholder': '0.0'}
            ),
            'notes': forms.Textarea(
                attrs={
                    'rows': 3,
                    'class': (
                        'w-full pl-2 rounded-md border-slate-300 shadow-sm '
                        'focus:border-blue-500 focus:ring-blue-500'
                    ),
                    'placeholder': 'How did it feel?',
                }
            ),
            'rpe': forms.NumberInput(attrs={
                'type': 'range',
                'min': '0',
                'max': '10',
                'step': '1',
                'class': 'w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer',
            }),
        }

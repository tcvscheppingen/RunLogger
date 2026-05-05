# pylint: disable=invalid-name
"""Form for logging a new workout."""
from django import forms
from django.utils import timezone
from runs.models import Workout

_INPUT_CLASSES = 'w-full rounded-md border-slate-300 shadow-sm'
_FOCUS_CLASSES = f'{_INPUT_CLASSES} focus:border-blue-500 focus:ring-blue-500'


class WorkoutForm(forms.ModelForm):
    """ModelForm for creating or editing a Workout, with separate h/m/s fields."""

    hours = forms.IntegerField(
        min_value=0, required=False,
        widget=forms.NumberInput(
            attrs={'class': _INPUT_CLASSES, 'placeholder': '0'})
    )
    minutes = forms.IntegerField(
        min_value=0, max_value=59, required=False,
        widget=forms.NumberInput(
            attrs={'class': _INPUT_CLASSES, 'placeholder': '0'})
    )
    seconds = forms.IntegerField(
        min_value=0, max_value=59, required=False,
        widget=forms.NumberInput(
            attrs={'type': 'number', 'class': _INPUT_CLASSES, 'placeholder': '0'})
    )

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
                attrs={'class': _FOCUS_CLASSES, 'placeholder': '0.0'}
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

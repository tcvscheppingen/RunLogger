# pylint: disable=invalid-name
"""Form for editing a user's profile information."""
import zoneinfo
from django import forms
from runs.models import UserProfile

_INPUT_CLASSES = (
    'w-full rounded-md border-slate-300 shadow-sm '
    'focus:border-blue-500 focus:ring-blue-500 '
    'dark:bg-slate-800 dark:border-slate-700 dark:text-slate-100'
)

_SELECT_CLASSES = (
    'w-full rounded-md border border-slate-300 shadow-sm px-3 py-2 text-sm '
    'focus:border-blue-500 focus:ring-blue-500 '
    'dark:bg-slate-800 dark:border-slate-700 dark:text-slate-100'
)


class UserProfileForm(forms.ModelForm):
    """ModelForm for updating height, weight, timezone and name fields."""

    _TIMEZONE_CHOICES = [(tz, tz) for tz in sorted(zoneinfo.available_timezones())]

    timezone = forms.ChoiceField(
        choices=_TIMEZONE_CHOICES,
        widget=forms.Select(attrs={'class': _SELECT_CLASSES}),
    )

    class Meta:
        """Meta options: model, fields and Tailwind-styled widgets."""

        model = UserProfile
        fields = ['first_name', 'last_name', 'weight', 'height', 'timezone']
        widgets = {
            'first_name': forms.TextInput(
                attrs={'class': _INPUT_CLASSES, 'placeholder': 'First name'}
            ),
            'last_name': forms.TextInput(
                attrs={'class': _INPUT_CLASSES, 'placeholder': 'e.g. van der Berg'}
            ),
            'weight': forms.NumberInput(
                attrs={'class': _INPUT_CLASSES, 'placeholder': '70.00', 'step': '0.01'}
            ),
            'height': forms.NumberInput(
                attrs={'class': _INPUT_CLASSES, 'placeholder': '180'}
            ),
        }

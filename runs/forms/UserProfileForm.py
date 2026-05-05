import zoneinfo
from django import forms
from django.utils import timezone
from runs.models import UserProfile

_TIMEZONE_CHOICES = [(tz, tz) for tz in sorted(zoneinfo.available_timezones())]

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
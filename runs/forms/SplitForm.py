# pylint: disable=invalid-name
"""Form for adding splits to a workout"""
from django import forms
from runs.models import Split

_INPUT_CLASSES = 'w-full rounded-md border-slate-300 shadow-sm'
_FOCUS_CLASSES = f'{_INPUT_CLASSES} focus:border-blue-500 focus:ring-blue-500'

class SplitForm(forms.ModelForm):
    """ModelForm for updating Split fields"""

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

        model = Split
        fields = ['distance', 'minutes', 'seconds']
        widgets = {
            'distance': forms.NumberInput(
                attrs={'class': _FOCUS_CLASSES, 'placeholder': '0'}
            ),
        }

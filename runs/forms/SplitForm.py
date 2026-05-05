# pylint: disable=invalid-name
"""Form for adding splits to a workout"""
from django import forms
from runs.models import Split
from runs.forms.fields import FOCUS_CLASSES, minutes_field, seconds_field


class SplitForm(forms.ModelForm):
    """ModelForm for updating Split fields"""

    minutes = minutes_field()
    seconds = seconds_field()

    class Meta:
        """Meta options: model, fields and Tailwind-styled widgets."""

        model = Split
        fields = ['distance', 'minutes', 'seconds']
        widgets = {
            'distance': forms.NumberInput(
                attrs={'class': FOCUS_CLASSES, 'placeholder': '0'}
            ),
        }

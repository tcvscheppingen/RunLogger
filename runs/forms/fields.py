"""Shared form field definitions for the runs application."""
from django import forms

INPUT_CLASSES = 'w-full rounded-md border-slate-300 shadow-sm'
FOCUS_CLASSES = f'{INPUT_CLASSES} focus:border-blue-500 focus:ring-blue-500'


def minutes_field():
    """Return an IntegerField for minutes (0–59)."""
    return forms.IntegerField(
        min_value=0, max_value=59, required=False,
        widget=forms.NumberInput(
            attrs={'class': INPUT_CLASSES, 'placeholder': '0'})
    )


def seconds_field():
    """Return an IntegerField for seconds (0–59)."""
    return forms.IntegerField(
        min_value=0, max_value=59, required=False,
        widget=forms.NumberInput(
            attrs={'type': 'number', 'class': INPUT_CLASSES, 'placeholder': '0'})
    )

from django import forms
from .models import Workout, Split

class WorkoutForm(forms.ModelForm):
    # 1. Custom fields go OUTSIDE Meta
    hours = forms.IntegerField(
        min_value=0, initial=0, required=False,
        widget=forms.NumberInput(attrs={'class': 'w-full rounded-md border-slate-300 shadow-sm', 'placeholder': '0'})
    )
    minutes = forms.IntegerField(
        min_value=0, max_value=59, initial=0, required=False,
        widget=forms.NumberInput(attrs={'class': 'w-full rounded-md border-slate-300 shadow-sm', 'placeholder': '0'})
    )
    seconds = forms.IntegerField(
        min_value=0, max_value=59, initial=0, required=False,
        widget=forms.NumberInput(attrs={'class': 'w-full rounded-md border-slate-300 shadow-sm', 'placeholder': '0'})
    )

    class Meta:
        model = Workout
        # 2. fields and widgets must be INSIDE Meta
        fields = ['distance', 'hours', 'minutes', 'seconds', 'notes', 'rpe']
        
        widgets = {
            'distance': forms.NumberInput(attrs={'class': 'w-full rounded-md border-slate-300 shadow-sm focus:border-blue-500 focus:ring-blue-500', 'placeholder': '0.0'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'w-full rounded-md border-slate-300 shadow-sm focus:border-blue-500 focus:ring-blue-500', 'placeholder': 'How did it feel?'}),
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
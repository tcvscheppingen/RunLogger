"""View for displaying and updating the user's profile."""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from runs.models import UserProfile
from runs.forms import UserProfileForm


@login_required
def user_profile(request):
    """Display and handle updates to the logged-in user's profile."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('user_profile')
    else:
        form = UserProfileForm(instance=profile)
    return render(request, 'runs/user_profile.html', {'form': form, 'profile': profile})

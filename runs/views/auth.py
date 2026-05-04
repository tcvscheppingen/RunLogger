from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, views as auth_views
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit


@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'runs/register.html', {'form': form})


@method_decorator(ratelimit(key='ip', rate='10/m', method='POST', block=True), name='dispatch')
class RateLimitedLoginView(auth_views.LoginView):
    pass

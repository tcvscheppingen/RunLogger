"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from django.http import HttpResponse
from django_ratelimit.exceptions import Ratelimited
from runs import views


def handler403(_request, exception=None):
    if isinstance(exception, Ratelimited):
        return HttpResponse("Too many attempts. Please wait a moment and try again.", status=429)
    return HttpResponse("Forbidden", status=403)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.dashboard, name='dashboard'),
    path('delete/<int:pk>/', views.delete_run, name='delete_run'),
    path('workout/<int:pk>/', views.workout_details, name='workout_details'),
    path('split/delete/<int:pk>/', views.delete_split, name='delete_split'),
    path('export/csv/', views.export_csv, name='export_csv'),
    path('import/csv/', views.import_csv, name='import_csv'),
    path('profile/', views.user_profile, name='user_profile'),
    path('register/', views.register, name='register'),

    # Built-in Auth views
    path('login/', views.RateLimitedLoginView.as_view(template_name='runs/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]

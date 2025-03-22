from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.views.decorators.cache import cache_control
from .models import PanicAttackEntry, DailyMoodEntry
from django.contrib.auth.decorators import login_required

# Create your views here.
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def index(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    return render(request, "home.html")

def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("index")  # Redirect to home after login
        else:
            return render(request, "login.html", {"error": "Invalid credentials"})
    return render(request, "login.html")

def logout_view(request):
    logout(request)
    return redirect("login")

def signup_view(request):
    if request.method == "POST":
        username = request.POST["name"]
        email = request.POST["email"]
        password = request.POST["password"]

        # Check if the user already exists
        if User.objects.filter(username=username).exists():
            return render(request, "signup.html", {"error": "User already exists"})

        # Create new user
        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()

        # Log in the new user
        login(request, user)

        return redirect("index")  # Redirect to home page after signup

    return render(request, "signup.html")

@login_required
def dashboard(request):
    # Fetching triggers and moods for the logged-in user
    triggers = PanicAttackEntry.objects.filter(user=request.user).order_by('-timestamp')
    moods = DailyMoodEntry.objects.filter(user=request.user).order_by('-timestamp')

    # Extract only the time (HH:MM format) for display
    for entry in triggers:
        entry.time_only = entry.timestamp.strftime('%H:%M')

    for entry in moods:
        entry.time_only = entry.timestamp.strftime('%H:%M')

    context = {
        'triggers': triggers,
        'moods': moods
    }

    return render(request, 'dashboard.html', context)
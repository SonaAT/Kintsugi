from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.views.decorators.cache import cache_control
from .models import PanicAttackEntry, DailyMoodEntry
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializers import PanicAttackEntrySerializer, DailyMoodEntrySerializer
import re

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

@api_view(['POST'])
def save_trigger(request):
    """
    API endpoint to save panic attack trigger data.
    """
    try:
        username = request.data.get("username")
        trigger = request.data.get("trigger")

        if not username:
            return Response({"error": "Username is missing"}, status=status.HTTP_400_BAD_REQUEST)

        print(f"Received trigger for user: {username}")  # Debugging output

        user = User.objects.get(username=username)  # Check if user exists
        panic_entry = PanicAttackEntry.objects.create(user=user, trigger=trigger)
        serializer = PanicAttackEntrySerializer(panic_entry)

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except User.DoesNotExist:
        return Response({"error": f"User '{username}' not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def save_mood(request):
    """
    API endpoint to save daily mood data.
    """
    try:
        username = request.data.get("username")
        mood_text = request.data.get("mood")

        # Extract mood from quotes using regex
        mood_match = re.search(r'"(.*?)"', mood_text)
        mood = mood_match.group(1) if mood_match else "Unknown"  # Default to "Unknown" if no match

        user = User.objects.get(username=username)
        mood_entry = DailyMoodEntry.objects.create(user=user, mood=mood)
        serializer = DailyMoodEntrySerializer(mood_entry)

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@login_required
def get_logged_in_user(request):
    """
    API endpoint to get the currently logged-in user.
    """
    return JsonResponse({"username": request.user.username})

@login_required
def spin_view(request):
    return render(request, 'spin.html')

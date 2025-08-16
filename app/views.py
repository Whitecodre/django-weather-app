import os
import requests
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.utils import timezone
from .models import FavoriteCity, SearchHistory
from dotenv import load_dotenv

load_dotenv()

def get_weather_data(location):
    api_key = os.getenv('WEATHER_API_KEY')
    base_url = "http://api.openweathermap.org/data/2.5/"
    
    try:
        current = requests.get(f"{base_url}weather?q={location}&appid={api_key}&units=metric").json()
        if current.get('cod') != 200:
            return None, current.get('message', 'Unknown error')
            
        forecast = requests.get(f"{base_url}forecast?q={location}&appid={api_key}&units=metric").json()
        
        return {
            'current': {
                'city': current['name'],
                'country': current['sys']['country'],
                'temperature': current['main']['temp'],
                'conditions': current['weather'][0]['description'],
                'icon': current['weather'][0]['icon'],
                'humidity': current['main']['humidity'],
                'wind_speed': current['wind']['speed'],
                'pressure': current['main']['pressure'],
                'timestamp': timezone.now()
            },
            'forecast': [
                {
                    'date': item['dt_txt'],
                    'temp_max': item['main']['temp_max'],
                    'temp_min': item['main']['temp_min'],
                    'icon': item['weather'][0]['icon'],
                    'conditions': item['weather'][0]['description']
                } for item in forecast.get('list', [])[::8][:5]
            ]
        }, None
    except Exception as e:
        return None, str(e)

def weather_view(request):
    location = request.GET.get('city', 'London,UK')
    
    if 'lat' in request.GET and 'lon' in request.GET:
        try:
            response = requests.get(
                f"http://api.openweathermap.org/data/2.5/weather?"
                f"lat={request.GET['lat']}&lon={request.GET['lon']}"
                f"&appid={os.getenv('WEATHER_API_KEY')}&units=metric"
            ).json()
            location = f"{response['name']},{response['sys']['country']}"
        except Exception as e:
            messages.error(request, f"Geolocation failed: {str(e)}")

    weather_data, error = get_weather_data(location)
    context = {
        'current': None,
        'forecast': [],
        'favorites': [],
        'is_favorite': False,
        'recent_searches': []
    }

    if not error:
        is_favorite = False
        if request.user.is_authenticated:
            favorites = FavoriteCity.objects.filter(user=request.user)
            is_favorite = favorites.filter(
                city=weather_data['current']['city'],
                country_code=weather_data['current']['country']
            ).exists()

            SearchHistory.objects.create(
                user=request.user,
                city=f"{weather_data['current']['city']},{weather_data['current']['country']}",
                temperature=weather_data['current']['temperature'],
                conditions=weather_data['current']['conditions'],
                icon=weather_data['current']['icon'],
                humidity=weather_data['current']['humidity'],
                wind_speed=weather_data['current']['wind_speed'],
                pressure=weather_data['current']['pressure']
            )

            recent_searches = (
                SearchHistory.objects
                .filter(user=request.user)
                .order_by('-searched_at')
                .values_list('city', flat=True)
                .distinct()[:5]
            )

            context.update({
                'favorites': favorites,
                'recent_searches': recent_searches
            })

        context.update({
            'current': weather_data['current'],
            'forecast': weather_data['forecast'],
            'is_favorite': is_favorite
        })
    else:
        messages.error(request, f"Weather data unavailable: {error}")

    return render(request, 'weather.html', context)

@login_required
def save_favorite(request):
    if request.method == 'POST':
        city = request.POST.get('city', '').strip().title()
        country = request.POST.get('country', '').upper()
        if city and country:
            FavoriteCity.objects.get_or_create(
                user=request.user,
                city=city,
                country_code=country
            )
        return HttpResponse(f'''
                <button hx-post="/remove-favorite/"
                        hx-vals='{{"city": "{city}", "country": "{country}"}}'
                        hx-target="this"
                        hx-swap="outerHTML"
                        class="text-yellow-400 hover:text-yellow-300 flex items-center">
                    ★ Saved
                </button>
            ''')
    return HttpResponse({'status': 'error'}, status=400)

@login_required
def remove_favorite(request):
    if request.method == 'POST':
        city = request.POST.get('city', '').strip().title()
        country = request.POST.get('country', '').upper()

        if city and country:
            # Delete the record
            FavoriteCity.objects.filter(
                user=request.user,
                city=city,
                country_code=country
            ).delete()

            # Check if removal came from favorites list
            target_id = request.headers.get('HX-Target', '')

            if target_id.startswith('fav-'):
                # Removing from favorites section → return nothing (HTMX removes the element)
                return HttpResponse('')

            # Otherwise, this is from the main weather card → return Save button
            return HttpResponse(f'''
                <button hx-post="/save-favorite/"
                        hx-vals='{{"city": "{city}", "country": "{country}"}}'
                        hx-target="this"
                        hx-swap="outerHTML"
                        class="text-white hover:text-yellow-300 flex items-center">
                    ♥ Save Location
                </button>
            ''')

    return HttpResponse('Error', status=400)

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

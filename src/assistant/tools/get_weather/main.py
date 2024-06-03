import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from utils.logger import logger

load_dotenv()

# takes in a dict with date and time and returns a unix timestamp
def convert_to_unix(time):
    if time.get('date') and time.get('time'):
        time_str = f"{time['date']} {time['time']}"
    elif time.get('date'):
        time_str = f"{time['date']} 12:00:00"

    dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
    logger.info(f"Converted time string {time_str} to unix timestamp: {int(dt.timestamp())}")
    return int(dt.timestamp())

async def location_to_coords(location, api_key):
    logger.info(f"Converting location to coordinates: {location}")
    try:
        combined_location = []
        if 'city' in location:
            combined_location.append(f"{location['city']}")
        if 'state' in location:
            combined_location.append(f"{location['state']}")
        if 'country' in location:
            combined_location.append(f"{location['country']}")
        combined_location = ','.join(combined_location)

        logger.info(f"Combined location: {combined_location}")
        response = requests.get(f'http://api.openweathermap.org/geo/1.0/direct?q={combined_location}&limit=1&appid={api_key}')
        logger.debug(f'API REQUEST URL: http://api.openweathermap.org/geo/1.0/direct?q={combined_location}&limit=1&appid={api_key}')
        data = response.json()
        logger.info(f"Converted location {combined_location} to coordinates: {data}")
        return data[0]['lat'], data[0]['lon']
    except Exception as e:
        logger.error(f"Error converting location to coordinates: {e}")
        return None, None
    
def round_temp_str(temp):
    return str(round(float(temp)))


async def get_weather_function(location, unit, time, api_key, language = 'en'):
    logger.info(f"Getting weather for location: {location}, unit: {unit}, time: {time}, language: {language}")

    try:
        coords = await location_to_coords(location, api_key)
        logger.info(f"Converted location to coordinates: {coords}")


        if time in ['now', 'today', 'current time', None]:
            logger.info("Getting current weather")
            call_type = 'weather'
        else: 
            logger.info("Getting forecast")
            call_type = 'forecast'
            unix_time = convert_to_unix(time)
            logger.info(f"Converted time to unix: {unix_time}")

            if (unix_time > (datetime.now() + timedelta(days=5)).timestamp()):
                logger.warning("Requested time is more than 5 days in the future")
                return {'response': 'Sorry, I can only give you the weather within the next 5 days.'}
            if (unix_time < datetime.now().timestamp()):
                logger.warning("Requested time is in the past")
                return {'response': 'Sorry, as of now, I cannot give you past weather.'}

        openweather_request_url = f'http://api.openweathermap.org/data/2.5/{call_type}?lat={coords[0]}&lon={coords[1]}&appid={api_key}&units={unit}&lang={language}'
        logger.info(f"Sending request to: {openweather_request_url}")

        response = requests.get(openweather_request_url)
        data = response.json()
        logger.info(f"Received response: {data}")

        if call_type == 'weather':
            temperature = round_temp_str(data['main']['temp'])
            feels_like = round_temp_str(data['main']['feels_like'])
            description = data['weather'][0]['main']
            icon = data['weather'][0]['icon']
        elif call_type == 'forecast':
            closest_forecast = None
            smallest_difference = float('inf')

            for forecast in data['list']:
                current_difference = (forecast['dt'] - unix_time)
                logger.info(f"Current difference: {current_difference}")
                
                logger.info(f"Current difference: {current_difference}, Smallest_difference: {smallest_difference}")
                if (current_difference < smallest_difference):
                    smallest_difference = current_difference
                    closest_forecast = forecast

            temperature = round_temp_str(closest_forecast['main']['temp'])
            feels_like = round_temp_str(closest_forecast['main']['feels_like'])
            description = closest_forecast['weather'][0]['main']
            icon = closest_forecast['weather'][0]['icon']

        
        if time is None or time == '':
            time = datetime.now()
        formatted_datetime = time.strftime("%A, %B %d, %Y %I:%M:%S %p")

        simple_response = {
            'datetime': formatted_datetime,
            'temperature': temperature,
            'description': description,
        }

        complete_response = {
            'temperature': temperature,
            'feels_like': feels_like,
            'description': description,
            'icon': icon
        }
        return {
            'type': 'weather',
            'weather': simple_response
        }

    except Exception as e:
        logger.error(f"Error getting weather: {e}")
        return {'response': {
            'type': 'error',
            'content': f'Error getting weather: {e}'
        }}

# from utils.logger import logger

async def main(user, unit = None, location = None, time = None):
    logger.info(f"Weather function recieved user: {user}, unit: {unit}, location: {location}, time: {time}")
    try:
        api_key = os.getenv('OPENWEATHER_API_KEY')
        unit = 'imperial' if (unit or user['settings']['temp_unit']) == 'f' else 'metric'
        if location is None or len(location) == 0:
            location = user['settings']['current_location']
        logger.info(f"Using unit: {unit}")
        logger.info(f"Using api_key: {api_key}")
        return await get_weather_function(location, unit, time, api_key)
    except Exception as e:
        logger.error(f"Error running tool get_weather: {e}")
        return {'response': f'Error running tool get_weather: {e}'}
    
get_weather = main

call_format = """
{
    "name": "get_weather",
    "description": "Retrieves the weather and temperature for a location, at a specific or non specific time.", 
    "parameter_definitions": {
        "unit": {
            "description": "Retreives temperature converted to this unit, formatted as 'c' for celcius, 'f' for farenheit, or 'none' for none",
            "type": "str",
            "required": false
        },
        "location": {
            "description": "Retrieves weather data for this location, formated as {'city': 'placeholder', 'state': 'placeholder', 'country': 'placeholder'}, or {}, or none.",
            "type": "dictionary",
            "required": false
        },
        "time": {
            "description": "Retreives weather data for this time and date, formated as YYYY-MM-DD HH:MM",
            "type": "str",
            "required": false
        }
    }
}
"""
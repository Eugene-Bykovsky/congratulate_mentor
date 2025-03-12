import requests


def fetch_data(api_url, endpoint):
    try:
        response = requests.get(f'{api_url}{endpoint}')
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при подключении к API: {e}")
        return None


def fetch_mentors(api_url):
    data = fetch_data(api_url, '/mentors')
    return data.get('mentors', []) if data else []


def fetch_postcards(api_url):
    data = fetch_data(api_url, '/postcards')
    return data.get('postcards', []) if data else []


def extract_holidays_from_postcards(postcards):
    holidays = {}
    for postcard in postcards:
        holiday_id = postcard['holidayId']
        if holiday_id not in holidays:
            holidays[holiday_id] = postcard[
                'name_ru']  # Берем название первой открытки для праздника
    return [{"id": hid, "name_ru": hname} for hid, hname in holidays.items()]

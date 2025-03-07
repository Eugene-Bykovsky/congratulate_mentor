import requests


def fetch_data(api_url, endpoint, headers=None):
    if headers is None:
        headers = {}
    try:
        response = requests.get(f'{api_url}{endpoint}', headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при подключении к API: {e}")
        return None


def fetch_mentors(api_url, headers=None):
    return fetch_data(api_url, '/mentors', headers)


def fetch_holidays(api_url, headers=None):
    return fetch_data(api_url, '/holidays', headers)


def fetch_postcards(api_url, headers=None):
    return fetch_data(api_url, '/postcards', headers)

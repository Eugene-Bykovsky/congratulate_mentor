import requests


def fetch_data(api_url, endpoint, headers=None):
    if headers is None:
        headers = {}

    try:
        response = requests.get(f'{api_url}{endpoint}', headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Ошибка при получении данных. Код ответа: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"Произошла ошибка подключения к API: {e}")
        return []


def fetch_mentors(api_url, headers=None):
    return fetch_data(api_url, '/mentors', headers)


def fetch_holidays(api_url, headers=None):
    return fetch_data(api_url, '/holidays', headers)


def fetch_postcards(api_url, headers=None):
    return fetch_data(api_url, '/postcards', headers)
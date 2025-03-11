import requests


def fetch_data(api_url, endpoint):
    try:
        response = requests.get(f'{api_url}{endpoint}')
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка: {e}")
        return None


def fetch_mentors(api_url):
    return fetch_data(api_url, '/mentors')['mentors']


def fetch_postcards(api_url):
    return fetch_data(api_url, '/postcards')['postcards']

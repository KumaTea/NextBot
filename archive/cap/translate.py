import uuid
import requests
import configparser



config = configparser.ConfigParser()
config.read('config.ini')

endpoint = "https://api.cognitive.microsofttranslator.com"
path = '/translate'
constructed_url = endpoint + path

key = config['translate']['key']
location = config['translate']['location']


def translate(text: str = 'Hello, world!', source: str = 'en', target: str = 'zh-Hans') -> str:
    params = {
        'api-version': '3.0',
        'from': source,
        'to': target
    }

    headers = {
        'Ocp-Apim-Subscription-Key': key,
        'Ocp-Apim-Subscription-Region': location,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4()),
    }

    body = [{
        'text': text
    }]

    request = requests.post(constructed_url, params=params, headers=headers, json=body)
    response = request.json()
    return response[0]['translations'][0]['text']

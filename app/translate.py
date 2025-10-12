import requests
from flask_babel import _
from app import current_app

def translate(text, source_language, dest_language):
    if 'MS_TRANSLATOR_KEY' not in current_app.config or \
            not current_app.config['MS_TRANSLATOR_KEY']:
        return _('Error: the translation service is not configured.')
    
    # provided in Keys and Endpoint page
    auth = {
        'Ocp-Apim-Subscription-Key': current_app.config['MS_TRANSLATOR_KEY'],
        'Ocp-Apim-Subscription-Region': 'uksouth',
    }
    # path for the translation endpoint
    r = requests.post( 
        'https://api.cognitive.microsofttranslator.com'
        '/translate?api-version=3.0&from={}&to={}'.format(
            source_language, dest_language), headers=auth, json=[{'Text': text}]) # JSON sending structured data between a browser and a server.
    if r.status_code != 200:
        return _('Error: the translation service failed.')
    return r.json()[0]['translations'][0]['text']
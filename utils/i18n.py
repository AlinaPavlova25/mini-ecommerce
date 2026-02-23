import json
import os
from flask import session

_translations = {}

def load_translations():
    global _translations
    translations_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'translations')
    
    for lang in ['tr', 'en']:
        filepath = os.path.join(translations_dir, f'{lang}.json')
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                _translations[lang] = json.load(f)

def get_translation(key, lang=None):
    if not _translations:
        load_translations()
    
    if lang is None:
        lang = session.get('language', 'tr')
    
    return _translations.get(lang, {}).get(key, key)

def t(key):
    return get_translation(key)

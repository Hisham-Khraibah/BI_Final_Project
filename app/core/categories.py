# -----------------------------------------------------------------------------
# CATEGORIES MODULE
# -----------------------------------------------------------------------------
'''
Business logic for default categories, custom categories, keyword rules,
and automatic category suggestions.
'''
from __future__ import annotations
import json
import os
import string
from typing import Any

# -----------------------------------------------------------------------------
# JSON READ / WRITE
# -----------------------------------------------------------------------------
def safe_read_json(path: str, default_value: Any) -> Any:
    '''Safely read a JSON file.'''
    try:
        if not os.path.exists(path):
            return default_value

        with open(path, 'r', encoding='utf-8') as file:
            return json.load(file)

    except Exception:
        return default_value


def safe_write_json(path: str, data: Any) -> bool:
    '''Safely write a JSON file.'''
    try:
        with open(path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2)

        return True

    except Exception:
        return False

# -----------------------------------------------------------------------------
# DEFAULT CATEGORY KEYWORDS
# -----------------------------------------------------------------------------
CATEGORY_KEYWORDS = {
    '': [],
    'Food & Restaurant': [
        'restaurant',
        'cafe',
        'coffee',
        'starbucks',
        'mcdonald',
        'burger',
        'pizza',
    ],
    'Groceries': [
        'grocery',
        'supermarket',
        'walmart',
        'aldi',
        'lidl',
    ],
    'Transport': [
        'uber',
        'lyft',
        'taxi',
        'bus',
        'train',
        'fuel',
        'shell',
    ],
    'Shopping': [
        'amazon',
        'target',
        'mall',
        'retail',
    ],
    'Bills & Utilities': [
        'electric',
        'water',
        'internet',
        'wifi',
        'verizon',
    ],
    'Entertainment': [
        'netflix',
        'spotify',
        'movie',
        'cinema',
    ],
    'Health': [
        'pharmacy',
        'drug',
        'walgreens',
        'cvs',
        'doctor',
    ],
    'Travel': [
        'hotel',
        'airbnb',
        'flight',
        'airlines',
    ],
}

# -----------------------------------------------------------------------------
# CUSTOM CATEGORY FUNCTIONS
# -----------------------------------------------------------------------------
def load_custom_categories(custom_cat_path: str) -> list[str]:
    '''Load custom categories from JSON.'''
    try:
        data = safe_read_json(custom_cat_path, [])
        return data if isinstance(data, list) else []

    except Exception:
        return []

def save_custom_category(custom_cat_path: str, category: str) -> bool:
    '''Save a custom category if it does not already exist.'''
    try:
        category = str(category).strip()

        if not category or category.isdigit():
            return False

        categories = load_custom_categories(custom_cat_path)
        normalized_categories = {value.casefold() for value in categories}

        if category.casefold() in normalized_categories:
            return True

        categories.append(category)
        categories = sorted(set(categories), key=lambda value: value.lower())

        return safe_write_json(custom_cat_path, categories)

    except Exception:
        return False

def delete_custom_category(custom_cat_path: str, category: str) -> bool:
    '''Delete a custom category if it exists.'''
    try:
        categories = load_custom_categories(custom_cat_path)
        target = str(category).strip().casefold()

        updated_categories = [
            value
            for value in categories
            if str(value).strip().casefold() != target
        ]

        if len(updated_categories) == len(categories):
            return True

        return safe_write_json(custom_cat_path, updated_categories)

    except Exception:
        return False

def get_all_categories(custom_cat_path: str) -> list[str]:
    '''
    Merge default and custom categories.

    Returns:
        List of all categories with the empty option first.
    '''
    try:
        base_categories = [
            category
            for category in CATEGORY_KEYWORDS.keys()
            if category != ''
        ]
        custom_categories = load_custom_categories(custom_cat_path)

        merged_categories = sorted(
            set(base_categories + custom_categories),
            key=lambda value: value.lower(),
        )

        return [''] + merged_categories

    except Exception:
        return ['']

# -----------------------------------------------------------------------------
# CUSTOM KEYWORD RULES
# -----------------------------------------------------------------------------
def load_custom_keywords(custom_keyword_path: str) -> dict[str, str]:
    '''Load custom keyword-to-category rules from JSON.'''
    try:
        data = safe_read_json(custom_keyword_path, {})
        return data if isinstance(data, dict) else {}

    except Exception:
        return {}

def save_custom_keyword(
    custom_keyword_path: str,
    keyword: str,
    category: str,
) -> bool:
    '''Save a custom keyword rule.'''
    try:
        keyword = str(keyword).strip().lower()
        category = str(category).strip()

        if not keyword or keyword.isdigit():
            return False

        data = load_custom_keywords(custom_keyword_path)
        data[keyword] = category

        return safe_write_json(custom_keyword_path, data)

    except Exception:
        return False

def delete_custom_keyword(custom_keyword_path: str, keyword: str) -> bool:
    '''Delete a custom keyword rule if it exists.'''
    try:
        keyword = str(keyword).strip().lower()
        data = load_custom_keywords(custom_keyword_path)

        if keyword in data:
            del data[keyword]
            return safe_write_json(custom_keyword_path, data)

        return True

    except Exception:
        return False

# -----------------------------------------------------------------------------
# AUTO CATEGORY SUGGESTION
# -----------------------------------------------------------------------------
def normalize_text(text: str) -> set[str]:
    '''
    Normalize text by lowercasing, removing punctuation, and splitting into words.
    '''
    try:
        cleaned_text = str(text).lower()
        cleaned_text = cleaned_text.translate(
            str.maketrans('', '', string.punctuation)
        )
        return set(cleaned_text.split())

    except Exception:
        return set()

def auto_category(
    merchant: str,
    note: str,
    custom_keyword_path: str,
) -> str:
    '''
    Suggest a category using:
    1. custom keyword rules
    2. default category keywords
    '''
    try:
        words = normalize_text(f'{merchant} {note}')
        custom_rules = load_custom_keywords(custom_keyword_path)

        for keyword, category in custom_rules.items():
            if keyword in words:
                return category

        for category, keywords in CATEGORY_KEYWORDS.items():
            if category == '':
                continue

            if any(keyword in words for keyword in keywords):
                return category

        return ''

    except Exception:
        return ''
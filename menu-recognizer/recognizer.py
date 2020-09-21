"""module with recognition function"""
from typing import Iterable, Dict
from collections import namedtuple
import tempfile
from pathlib import Path

from PIL import Image
import pytesseract
import spacy

from google.cloud import storage


LanguageCode = namedtuple('LanguageCode', ('iso', 'pytesseract', 'spacy'))


LANGUAGE_CODE_CONVERTER = {
    'de': LanguageCode('de', 'deu', 'de_core_news_sm')
}


def filter_raw_text(text: str, sequences_to_remove: Iterable[str]) -> str:
    """
    Removes all occurences from a text which are present in the sequences_to_remove list.
    This is an easy first step filtering, which is pretty weak, but makes usage of NLP later easier.

    Parameters
    ----------
    text : str
        test to filter
    sequences_to_remove : Iterable[str]
        sequences to remove

    Returns
    -------
    str
        filtered text
    """
    cleaned_text = text
    for seq in sequences_to_remove:
        cleaned_text = cleaned_text.replace(seq, '')
    return cleaned_text

def extract_text(img_path: Path, lang: str) -> str:
    """
    extracts the text from an image

    Parameters
    ----------
    img_path : Path
        path to the image file

    Returns
    -------
    str
        extracted text
    """
    img = Image.open(str(img_path)).convert('L')
    text = pytesseract.image_to_string(img, lang=LANGUAGE_CODE_CONVERTER[lang].pytesseract)
    return text

def generate_menu(words: Iterable) -> Dict[str, str]:
    """
    generates a dictionary with the menu

    Parameters
    ----------
    words : Iterable
        list of word

    Returns
    -------
    Dict[str, str]
        dictionary with weekdays as keys and the food as values
    """
    # Split by weekdays
    # TODO make language agnostic
    plan = {
        'Montag': '',
        'Dienstag': '',
        'Mittwoch': '',
        'Donnerstag': '',
        'Freitag': ''
    }
    cur_day = ''
    for word in words:
        if word.text in plan:
            cur_day = word.text
            continue
        # Skip all before Montag
        if cur_day == '':
            continue
        plan[cur_day] += word.text + ' '

    plan = {day: val.strip() for day, val in plan.items()}
    return plan

def process_document(text: str, lang: str) -> Iterable:
    """
    processes given text as document and returns a list of word in the order they have been recognized

    Parameters
    ----------
    text : str
        document as text
    lang : str
        language code of the text

    Returns
    -------
    Iterable
        list of words
    """
    # Naive text filtering
    # TODO get from anywhere
    seqs_to_remove = [
        'Einen frischen Obstteller gibt es jeden Taq / Nachtisch\n\nindividuell',
        'Kennzeichnung der Allergene',
        'Vesper'
    ]
    cleaned_text = filter_raw_text(text, seqs_to_remove)

    nlp = spacy.load(LANGUAGE_CODE_CONVERTER[lang].spacy)
    doc = nlp(cleaned_text)
    tokens = [token for token in doc]
    words = [token for token in tokens if token.is_alpha and len(token) > 1] # Remove abbreations
    return words

def process_image(bucket_name: str, file_name: str, lang: str):

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    
    # Download file
    blob = bucket.blob(file_name)
    with tempfile.TemporaryDirectory() as tmp_dir_name:
        tmp_dir = Path(tmp_dir_name)
        file_path = Path(file_name)
        dest_name = tmp_dir / file_path.name
        blob.download_to_filename(dest_name)
        # OCR
        text = extract_text(dest_name, lang)

    words = process_document(text, lang)    
    menu = generate_menu(words)
    return menu
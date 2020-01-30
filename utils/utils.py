from random import choice
import re, string, unicodedata


DESKTOP_AGENTS = [
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/602.2.14 (KHTML, like Gecko) Version/10.0.1 Safari/602.2.14',
    'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0'
]


def random_header():
    return {
        'User-Agent': choice(DESKTOP_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
        'Accept-Encoding': 'none',
        'Accept-Language': 'en-US,en;q=0.8',
        'Connection': 'keep-alive'
    }


def clean_keyword(text):
    text = text.strip()
    text = re.sub(' +', ' ', text)
    text = text.translate(str.maketrans(dict.fromkeys(string.punctuation)))
    return text.strip()


def format_afm(text):
    text = text.replace('-', '')
    return text.upper()


def afm_type(text):
    if not text or text == '':
        return 'UNK'
    if text[0] == '0':
        return 'ΦΠ/ΝΠ'
    if re.match('(1|2|3|4)', text[0]):
        return 'ΦΠ'
    if re.match('(7|8|9)', text[0]):
        return 'ΝΠ'
    return 'UNK'

def format_hastener(text):
    text = text.strip()
    text = re.sub(re.compile('<.*?>'), '', text)
    text = re.sub(' +', ' ', text)
    
    # text = ''.join(
    #     c for c in unicodedata.normalize('NFD', text)
    #     if unicodedata.category(c) != 'Mn'
    # )
    
    for c in '|!#$<>\/»«"\_`\'':
        if c in text:
            text = re.sub(c, '', text)
    return text.strip()

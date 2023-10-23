import os

from random import random
from time import sleep

import requests
from bs4 import BeautifulSoup as BS
import pandas as pd


# Request params
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}
HOST = 'https://www.oxfordlearnersdictionaries.com'
ENDP = '/wordlists/oxford3000-5000'
# Main selectors
WLIST_SEL = 'ul.top-g > li'
WORD_DURL_SEL = 'a'
SPART_SEL = 'span.pos'
LVL_SEL = 'span.belong-to'
WPRON_SEL = 'div.pron-us'
# Detailed selectors
SECTION_SEL = '.sense' #'#entryContent ol > li' unclear results
DEF_SEL = 'span.def'
EX_SEL = 'ul.examples span.x'
# Attributes to get
HREF = 'href'
MP3 = 'data-src-mp3'
# Paths
AUDIO_PATH = 'audio'
OUTPUT_NAME = 'dict.csv'


def check_host_in_url(url:str, host:str=HOST) -> str:
    """Check if the URL contains host address and adds it if not."""
    if host not in url:
        url = host + url
    return url


def get_processed_page(url: str, host:str=HOST,
                       headers:dict=HEADERS, timeout:int=30,
                       soup_mode:str='lxml') -> BS|None:
    """Check if the URL contains the host. Make a request and a soup."""
    url = check_host_in_url(url, host=host)

    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
    except Exception:
        sleep(30)
        get_processed_page(url, host, headers, timeout, soup_mode)
    soup = None

    if resp.status_code == 200:
        soup = BS(resp.text, soup_mode)
    else:
        print(f"[Error] Wrong status code: {resp.status_code}")

    return soup


def main():
    dir_list = os.listdir()
    if not AUDIO_PATH in dir_list:
        os.mkdir(AUDIO_PATH)

    dict_df = pd.read_csv(OUTPUT_NAME) if OUTPUT_NAME in dir_list else None
    start_val = 0 if dict_df is None else dict_df.last_valid_index() + 1

    mp3_files = os.listdir(AUDIO_PATH)

    url = HOST + ENDP
    main_soup = get_processed_page(url)
    word_list = main_soup.select(WLIST_SEL)
    # Getting a list from not hidden elements (selector does not work)
    word_list = [word for word in word_list if len(word.attrs) > 1]
    total_words = len(word_list)
    print(f"[Log] Found {total_words} words.")

    word_set = []
    try:
        for w in word_list[start_val:]:
            print('-'*150)
            word_el = w.select_one(WORD_DURL_SEL)
            part_of_sentence_el = w.select_one(SPART_SEL)
            lvl = w.select_one(LVL_SEL)
            pronunciation = w.select_one(WPRON_SEL)

            word = word_el.get_text()
            print(f"[Log] Processing {word_list.index(w) + 1} word: {word}.")
            part_of_sentence = part_of_sentence_el.get_text()
            lvl = lvl.get_text().capitalize()

            file_name = f"{word}.mp3"
            if not file_name in mp3_files:
                print(f"[Log] Downloading {file_name}.")
                mp3_url = check_host_in_url(pronunciation.get(MP3))
                resp_mp3 = requests.get(mp3_url, headers=HEADERS)
                if resp_mp3.status_code == 200:
                    with open(f"{AUDIO_PATH}/{file_name}", 'wb') as mp3:
                        mp3.write(resp_mp3.content)
            else:
                print(f"[Log] The file already exists: {file_name}.")

            wurl = word_el.get(HREF)
            det_soup = get_processed_page(wurl)
            details = det_soup.select(SECTION_SEL)

            definitions = [det.select_one(DEF_SEL).text for det in details[:2]
                           if det.select_one(DEF_SEL)]
            examples = [det.select_one(EX_SEL).text for det in details[:2]
                        if det.select_one(EX_SEL)]

            word_set.append(
                {
                    'Word': word,
                    'Part of Sentence': part_of_sentence,
                    'Level': lvl,
                    'Definition': '\n'.join(definitions),
                    'Example': '\n'.join(examples),
                    'Pronunciation File': file_name
                }
            )

            sleep(random())
    except Exception as e:
        print(f"[Error] Exception occured: {e}")
    finally:
        words_df = pd.DataFrame(word_set, index=None)
        output_df = words_df if dict_df is None else pd.concat([dict_df, words_df])
        output_df.to_csv(OUTPUT_NAME, index=None)

    print(" RESULT ".center(150, '='))
    print(f"[Log] Scraped {start_val + len(word_set)} words out of {total_words}.")


if __name__ == '__main__':
    main()

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
WLIST_SEL = 'ul.top-g > li:not([class])' # Somehow it still takes tags with classes that are hidden
WORD_DURL_SEL = 'a'
SPART_SEL = 'span.pos'
LVL_SEL = 'span.belong-to'
WPRON_SEL = 'div.pron-us'
# Detailed selectors
SECTION_SEL = '#entryContent ol > li'
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

    resp = requests.get(url, headers=headers, timeout=timeout)
    soup = None

    if resp.status_code == 200:
        soup = BS(resp.text, soup_mode)
    else:
        print(f"[Error] Wrong status code: {resp.status_code}")

    return soup


def main():
    if not AUDIO_PATH in os.listdir():
        os.mkdir(AUDIO_PATH)

    mp3_files = os.listdir(AUDIO_PATH)

    url = HOST + ENDP
    main_soup = get_processed_page(url)
    word_list = main_soup.select(WLIST_SEL)

    word_set = []
    try:
        for w in word_list[:100]:
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

            definitions = [det.select_one(DEF_SEL).text for det in details[:2]]
            examples = [det.select_one(EX_SEL).text for det in details[:2]]

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
        word_df = pd.DataFrame(word_set, index=None)
        word_df.to_csv(OUTPUT_NAME, index=None)

    print(" RESULT ".center(150, '='))
    print(f"[Log] Scraped {len(word_set)} words out of {len(word_list)}.")


if __name__ == '__main__':
    main()

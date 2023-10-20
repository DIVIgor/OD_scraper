import requests

from bs4 import BeautifulSoup as BS


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
SECTION_SEL = '#entryContent ol > li'
DEF_SEL = 'span.def'
EX_SEL = 'ul.examples span.x'
# Attributes to get
HREF = 'href'
MP3 = 'data-src-mp3'
# Paths
AUDIO_PATH = ''


def make_soup(data, mode = 'lxml'):
    return BS(data, mode)

def main():
    url = HOST + ENDP

    resp = requests.get(url, headers=HEADERS)
    assert resp.status_code == 200
    main_soup = make_soup(resp.text)
    word_list = main_soup.select(WLIST_SEL)
    word_set = []
    for w in word_list[:3]:
        word_el = w.select_one(WORD_DURL_SEL)
        part_of_sentence_el = w.select_one(SPART_SEL)
        lvl = w.select_one(LVL_SEL)
        pronunciation = w.select_one(WPRON_SEL)

        word = word_el.get_text()
        part_of_sentence = part_of_sentence_el.get_text()
        lvl = lvl.get_text().capitalize()

        mp3_url = pronunciation.get(MP3)
        file_name = f"{word}.mp3"
        if HOST not in mp3_url:
            mp3_url = HOST + mp3_url
        resp_mp3 = requests.get(mp3_url, headers=HEADERS)
        assert resp_mp3.status_code == 200
        with open(AUDIO_PATH + file_name, 'wb') as mp3:
            mp3.write(resp_mp3.content)

        wurl = word_el.get(HREF)
        if HOST not in wurl:
            wurl = HOST + wurl
        resp_det = requests.get(wurl, headers=HEADERS)
        assert resp_det.status_code == 200
        det_soup = make_soup(resp_det.text)
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

    print(word_set)


if __name__ == '__main__':
    main()

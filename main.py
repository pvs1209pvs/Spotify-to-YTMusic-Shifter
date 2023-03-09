import selenium
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver import Keys
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import spotipy
from selenium.webdriver.common.by import By
from spotipy.oauth2 import SpotifyOAuth
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

SPOTIPY_CLIENT_ID = '73f8e3c4592e46fea5f90060af15c5ac'
SPOTIPY_CLIENT_SECRET = '4d612b4dcc5e429da3be37e6775f5a0e'
REDIRECT_URL = "http://localhost:8080"

SCOPE = "user-library-read"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET,
                                               redirect_uri=REDIRECT_URL, scope=SCOPE))


def get_all_liked_songs(limit):
    chunk_number = 0
    liked_songs = []

    a = ""

    while True:
        results = sp.current_user_saved_tracks(limit=limit, offset=chunk_number * limit)

        for idx, item in enumerate(results['items']):
            liked_songs.append(item['track']['name'] + ' - ' + item['track']['artists'][0]['name'])

        chunk_number += 1

        if len(results['items']) < limit:
            break

    return liked_songs


def is_elmnt_exist(webdriver, xpath):
    try:
        webdriver.find_element(By.XPATH, xpath)
    except NoSuchElementException:
        return False
    return True


def is_liked(web_driver: WebDriver):
    """
    Return True if the song is already liked.
    :param web_driver: WebDriver
    :return: True if the song is already liked
    """

    try:
        liked_text = WebDriverWait(web_driver, 1).until(EC.visibility_of_element_located((By.XPATH,
                                                                                          "/html/body/ytmusic-app/ytmusic-popup-container/tp-yt-iron-dropdown/div/ytmusic-menu-popup-renderer/tp-yt-paper-listbox/ytmusic-toggle-menu-service-item-renderer[2]/yt-formatted-string")))
        return liked_text.text == "Remove from liked songs"
    except selenium.common.exceptions.TimeoutException:
        return False


def add_to_ytm(song_to_save: str):
    # Setup ChromeDriver
    chrome_opts = Options()
    chrome_opts.add_experimental_option("debuggerAddress", "localhost:8989")
    chrome = webdriver.Chrome(executable_path="/usr/local/bin/chromedriver", options=chrome_opts)

    # Open YTM
    chrome.get("https://music.youtube.com//")

    # Click Search
    search = WebDriverWait(chrome, 5).until(EC.visibility_of_element_located((By.XPATH,
                                                                              "/html/body/ytmusic-app/ytmusic-app-layout/ytmusic-nav-bar/div[2]/ytmusic-search-box/div/div[1]/tp-yt-paper-icon-button[1]/tp-yt-iron-icon")))
    search.click()

    # Search the song
    srch_txt_fld = WebDriverWait(chrome, 5).until(EC.visibility_of_element_located((By.XPATH,
                                                                                    "/html/body/ytmusic-app/ytmusic-app-layout/ytmusic-nav-bar/div[2]/ytmusic-search-box/div/div[1]/input")))
    srch_txt_fld.send_keys(song_to_save)
    srch_txt_fld.send_keys(Keys.ENTER)

    # Right-click on the song
    top_rslt = WebDriverWait(chrome, 5).until(EC.visibility_of_element_located((By.XPATH,
                                                                                "/html/body/ytmusic-app/ytmusic-app-layout/div[3]/ytmusic-search-page/ytmusic-tabbed-search-results-renderer/div[2]/ytmusic-section-list-renderer/div[2]/ytmusic-shelf-renderer[1]/div[3]")))
    actions = ActionChains(chrome)
    actions.context_click(top_rslt).perform()

    # Add song
    if not is_liked(chrome):
        try:
            add_to_lib = WebDriverWait(chrome, 1).until(EC.visibility_of_element_located((By.XPATH,
                                                                                          "/html/body/ytmusic-app/ytmusic-popup-container/tp-yt-iron-dropdown[1]/div/ytmusic-menu-popup-renderer/tp-yt-paper-listbox/ytmusic-toggle-menu-service-item-renderer[2]/yt-formatted-string")))
            add_to_lib.click()
            return ""
        except selenium.common.exceptions.TimeoutException:
            return song_to_save

    return ""

def magic():
    all_spotify_songs = get_all_liked_songs(50)[:2]
    missing_songs = []

    for spoty_song in all_spotify_songs:
        result = add_to_ytm(spoty_song)

        print(result)
        if result != "":
            missing_songs.append(result)

    print(missing_songs)


magic()

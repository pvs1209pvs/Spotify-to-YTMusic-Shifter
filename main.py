import selenium
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import Keys
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from spotipy.oauth2 import SpotifyOAuth
import spotipy

SPOTIPY_CLIENT_ID = "73f8e3c4592e46fea5f90060af15c5ac"
SPOTIPY_CLIENT_SECRET = "4d612b4dcc5e429da3be37e6775f5a0e"
REDIRECT_URL = "http://localhost:8080"
SCOPE = "user-library-read"
REMOTE_DEBUGGING_PORT = 9222
CHROME_DRIVER_PATH = "/usr/local/bin/chromedriver"


def load_creds(filename: str):
    global SPOTIPY_CLIENT_ID
    global SPOTIPY_CLIENT_SECRET
    global REMOTE_DEBUGGING_PORT
    global CHROME_DRIVER_PATH

    with open(filename, "r") as cred_file:
        SPOTIPY_CLIENT_ID = cred_file.readline().strip()
        SPOTIPY_CLIENT_SECRET = cred_file.readline().strip()
        REMOTE_DEBUGGING_PORT = cred_file.readline().strip()
        CHROME_DRIVER_PATH = cred_file.readline().strip()


def get_all_liked_songs(spotify, limit):
    chunk_number = 0
    liked_songs = []

    while True:
        results = spotify.current_user_saved_tracks(limit=limit, offset=chunk_number * limit)

        for idx, item in enumerate(results['items']):
            liked_songs.append(item['track']['name'] + ' - ' + item['track']['artists'][0]['name'])

        chunk_number += 1

        if len(results['items']) < limit:
            break

    return liked_songs


def is_elmnt_exist(web_driver, xpath):
    try:
        web_driver.find_element(By.XPATH, xpath)
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
        liked_text = WebDriverWait(web_driver, 10).until(ec.visibility_of_element_located((By.XPATH,
                                                                                           "/html/body/ytmusic-app/ytmusic-popup-container/tp-yt-iron-dropdown/div/ytmusic-menu-popup-renderer/tp-yt-paper-listbox/ytmusic-toggle-menu-service-item-renderer[2]/yt-formatted-string")))
        return liked_text.text == "Remove from liked songs"
    except selenium.common.exceptions.TimeoutException:
        return False


def is_top_res_song(web_driver:WebDriver):
    is_song = WebDriverWait(web_driver, 10).until(ec.visibility_of_element_located((By.XPATH,
                                                                      "/html/body/ytmusic-app/ytmusic-app-layout/div[3]/ytmusic-search-page/ytmusic-tabbed-search-results-renderer/div[2]/ytmusic-section-list-renderer/div[2]/ytmusic-shelf-renderer[1]/div[3]/ytmusic-responsive-list-item-renderer/div[2]/div[3]/yt-formatted-string/span[1]")))
    return is_song.text == "Song"


def look_elsewhere(web_driver):
    """
    if the top result isn't a song ie album or something else.
    :param web_driver:
    :return:
    """
    type = WebDriverWait(web_driver, 10).until(ec.visibility_of_element_located((By.XPATH,"/html/body/ytmusic-app/ytmusic-app-layout/div[3]/ytmusic-search-page/ytmusic-tabbed-search-results-renderer/div[2]/ytmusic-section-list-renderer/div[2]/ytmusic-shelf-renderer[2]/div[3]/ytmusic-responsive-list-item-renderer[1]/div[2]/div[3]/yt-formatted-string/span[1]")))
    if type.text == "Song":
        return type
    else:
        return None
    # return type.text == "Song"
        # song_maybe = WebDriverWait(web_driver, 10).until(ec.visibility_of_element_located((By.XPATH,
        #                                                                              "/html/body/ytmusic-app/ytmusic-app-layout/div[3]/ytmusic-search-page/ytmusic-tabbed-search-results-renderer/div[2]/ytmusic-section-list-renderer/div[2]/ytmusic-shelf-renderer[2]/div[3]/ytmusic-responsive-list-item-renderer[1]")))


def add_to_ytm(song_to_save: str):
    # Setup ChromeDriver
    chrome_opts = Options()
    chrome_opts.add_experimental_option("debuggerAddress", "localhost:8989")
    chrome = webdriver.Chrome(executable_path=CHROME_DRIVER_PATH, options=chrome_opts)

    # Open YTM
    chrome.get("https://music.youtube.com//")
    print(chrome.port)

    # Click Search
    search = WebDriverWait(chrome, 10).until(ec.visibility_of_element_located((By.XPATH,
                                                                               "/html/body/ytmusic-app/ytmusic-app-layout/ytmusic-nav-bar/div[2]/ytmusic-search-box/div/div[1]/tp-yt-paper-icon-button[1]/tp-yt-iron-icon")))
    search.click()

    # Search the song
    srch_txt_fld = WebDriverWait(chrome, 10).until(ec.visibility_of_element_located((By.XPATH,
                                                                                     "/html/body/ytmusic-app/ytmusic-app-layout/ytmusic-nav-bar/div[2]/ytmusic-search-box/div/div[1]/input")))
    srch_txt_fld.send_keys(song_to_save)
    srch_txt_fld.send_keys(Keys.ENTER)

    if is_top_res_song(chrome):
        # Right-click on the song
        top_res = WebDriverWait(chrome, 10).until(ec.visibility_of_element_located((By.XPATH,
                                                                                "/html/body/ytmusic-app/ytmusic-app-layout/div[3]/ytmusic-search-page/ytmusic-tabbed-search-results-renderer/div[2]/ytmusic-section-list-renderer/div[2]/ytmusic-shelf-renderer[1]/div[3]")))

        ActionChains(chrome).context_click(top_res).perform()

        # Add song (from right-click menu)
        if not is_liked(chrome):
            try:
                add_to_lib = WebDriverWait(chrome, 10).until(ec.visibility_of_element_located((By.XPATH,"/html/body/ytmusic-app/ytmusic-popup-container/tp-yt-iron-dropdown[1]/div/ytmusic-menu-popup-renderer/tp-yt-paper-listbox/ytmusic-toggle-menu-service-item-renderer[2]/yt-formatted-string")))

                add_to_lib.click()
                return ""
            except selenium.common.exceptions.TimeoutException:
                return song_to_save
    else:
        something = look_elsewhere(chrome)

        if something is None:
            return song_to_save
        else:
            ActionChains(chrome).context_click(something).perform()
            other = WebDriverWait(chrome, 10).until(ec.visibility_of_element_located((By.XPATH, "/html/body/ytmusic-app/ytmusic-popup-container/tp-yt-iron-dropdown/div/ytmusic-menu-popup-renderer/tp-yt-paper-listbox/ytmusic-toggle-menu-service-item-renderer")))
            other.click()
            return "nice"

    return ""


def move_spotify_to_ytm(spotify):
    all_spotify_songs = get_all_liked_songs(spotify, 50)

    missing_songs = []

    for spoty_song in all_spotify_songs[:5]:
        result = add_to_ytm(spoty_song)

        if result != "":
            missing_songs.append(result)

    print(missing_songs)



if __name__ == "__main__":

    # load_creds("creds.txt")
    # print(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, REMOTE_DEBUGGING_PORT, CHROME_DRIVER_PATH)
    add_to_ytm("die 4 me halsey")
    exit(100)


    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                                   client_secret=SPOTIPY_CLIENT_SECRET,
                                                   redirect_uri=REDIRECT_URL,
                                                   scope=SCOPE))

    move_spotify_to_ytm(sp)

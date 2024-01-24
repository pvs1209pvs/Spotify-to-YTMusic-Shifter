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

SPOTIPY_CLIENT_ID = ""
SPOTIPY_CLIENT_SECRET = ""
REDIRECT_URL = "http://localhost:8080"
SCOPE = "user-library-read"
REMOTE_DEBUGGING_PORT = 0
CHROME_DRIVER_PATH = ""


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


def search_songs_sec(web_driver):
    """
    Returns the element if the result is of type 'Song' else None.
    :param web_driver: WebDriver.
    :return: Element itself if True else None.
    """
    type = WebDriverWait(web_driver, 10).until(ec.visibility_of_element_located((By.XPATH,"/html/body/ytmusic-app/ytmusic-app-layout/div[3]/ytmusic-search-page/ytmusic-tabbed-search-results-renderer/div[2]/ytmusic-section-list-renderer/div[2]/ytmusic-shelf-renderer[2]/div[3]/ytmusic-responsive-list-item-renderer[1]/div[2]/div[3]/yt-formatted-string/span[1]")))

    return type if type.text == "Song" else None


def add_to_ytm(song_to_save: str):
    """
    Adds the song to YTMusic
    :param song_to_save: Song to add to YTMusic.
    :return: Empty-string is the song was successful added else the name of the song.
    """

    # Setup ChromeDriver
    chrome_opts = Options()
    chrome_opts.add_experimental_option("debuggerAddress", "localhost:" + str(REMOTE_DEBUGGING_PORT))
    chrome = webdriver.Chrome(executable_path=CHROME_DRIVER_PATH, options=chrome_opts)
    # Open YTM
    chrome.get("https://music.youtube.com//")

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

        # Performs right-click
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
        song_element = search_songs_sec(chrome)

        if song_element is None:
            return song_to_save
        else:

            ActionChains(chrome).context_click(song_element).perform()
            song = WebDriverWait(chrome, 10).until(ec.visibility_of_element_located((By.XPATH, "/html/body/ytmusic-app/ytmusic-popup-container/tp-yt-iron-dropdown/div/ytmusic-menu-popup-renderer/tp-yt-paper-listbox/ytmusic-toggle-menu-service-item-renderer[2]")))
            song.click()
            return ""


    return ""


def move_spotify_to_ytm(spotify):
    all_spotify_songs = get_all_liked_songs(spotify, 50)
    all_spotify_songs = ['Die 4 Me - Halsey', 'Saints Row - Main Theme - Malcolm Kirby Jr.', 'Play Me Like A Violin - Stephen', 'Bitch Lasagna - pewdiepie', 'What Lovers Do (feat. SZA) - Maroon 5', 'Backwards Directions - Abby Sage', 'Chand Sifarish - Jatin-Lalit', 'Baarish Ki Jaaye - B Praak', 'London Lahore - Dilbag Singh', '2019 FLOW - Sikander Kahlon', 'The Way I Are (Dance with Somebody) [feat. Lil Wayne] - Bebe Rexha', 'Aston Martin Truck - Roddy Ricch', 'Pasoori - Shae Gill', 'Summer High - AP Dhillon', 'Rabba Ve (From "High End Yaariyaan") - B Praak', 'Breaking Through - The Wreckage', 'Lonely Road - WILLOW', 'Meri Jaan Meri Jaan (From "Bachchhan Paandey") - B Praak', 'NA NA NA - Osekhon', 'Desi Kalakaar - Yo Yo Honey Singh', 'Taare - Diljit Dosanjh', 'Sajna - Yashal Shahid', 'Humble - Tarsem Jassar', 'No Count - Tarsem Jassar', 'Guts - Tarsem Jassar', 'My Pride - Tarsem Jassar', 'Never Really Loved Me (with Dean Lewis) - Kygo', 'Wild Imagination - Rare Americans', 'Perfectly Imperfect - MOD SUN', 'pretty toxic revolver - Machine Gun Kelly', 'I Love U - The Chainsmokers', 'Cold Heart - PNAU Remix - Elton John', 'West Coast - OneRepublic', 'Eyes Don’t Lie - Tones And I', 'Synchronize - Milky Chance', "Can't Stop Us Now - Pitbull", 'Rumors - NEFFEX', 'G.O.A.T. - Diljit Dosanjh', 'Unforgettable - Diljit Dosanjh', 'Sai - Satinder Sartaaj', 'Offshore - Shubh', 'Dil Na Jaaneya Remix by DJ Chetas & DJ Lijo - Dj Chetas', 'Gallan Mithiyan - Mankirt Aulakh', 'Savan - Vilen', 'Eternity - NexP', 'Hear You Calling - Kid Mac', 'Lucid Dreams - Juice WRLD', 'Already Dead - Juice WRLD', 'Bad Boy (with Young Thug) - Juice WRLD', 'Reminds Me Of You - Juice WRLD', 'el Diablo - Machine Gun Kelly', 'Wants And Needs - Instrumental - Diamond Audio', 'Worth It (feat. Kid Ink) - Fifth Harmony', 'Love Language - Acoustic - Connor Price', 'Choothi - Waqar Ex', 'Left - Jordan Solomon', 'Nira Ishq - Guri', 'Taara - Ammy Virk', 'SUBEME LA RADIO (feat. Descemer Bueno & Zion & Lennox) - Enrique Iglesias', 'BITE ME - NEFFEX', 'Uchiyaan Dewaraan - Bilal Saeed', 'Time Lapse - Ludovico Einaudi', 'Main Suneya - Ammy Virk', 'MISS THE RAGE - XAE.Miami', 'Brown Boy - NAV', 'Goosebumps - Remix - Travis Scott', 'This Feeling - The Chainsmokers', 'Freshman List - NAV', 'Never Give Up - NEFFEX', "I'm So Paid - Akon", 'Playing Through the Pain - I Am King', 'Love the Way You Lie, Pt. 2 - I Am King', 'Higher (feat. iann dior) - Clean Bandit', 'Malibu - Virginia To Vegas', 'Lifestyle (feat. Adam Levine) - Jason Derulo', 'Juice - Future', 'Yaarr Ni Milyaa - Harrdy Sandhu', 'Minute - NAV', 'My Mind - NAV', 'Best of Me - NEFFEX', 'Cheerleader - Felix Jaehn Remix Radio Edit - OMI', 'Watch Me (Whip / Nae Nae) - Silentó', 'The Adventures of Moon Man & Slim Shady (with Eminem) - Kid Cudi', 'I Like Me Better - Lauv', 'no song without you - HONNE', 'Immortal - Dream Evil', 'Professional Rapper (feat. Snoop Dogg) - Lil Dicky', 'Spartan - NEFFEX', 'Make It - NEFFEX', 'Stay (with Alessia Cara) - Zedd', 'Nowhere Fast (feat. Kehlani) - Extended Version - Eminem', 'Body - Dzeko Remix - Loud Luxury', 'In Your Head - Eminem', 'Freestyle Rap Leader - Skar-p', 'Meray Saathiya - Roxen', 'Rubbin off the Paint - YBN Nahmir', "No Flockin' - Kodak Black", 'Save Me - Promoting Sounds', 'Lose Somebody - Kygo', 'Intentions (feat. Quavo) - Justin Bieber', 'Eastside (with Halsey & Khalid) - benny blanco', 'Ek Raat - Vilen', 'The Hunter - Adam Jensen', 'Pendu (feat. Young Fateh) - Dr Zeus', 'me & ur ghost - blackbear', 'Stupid Love - Lady Gaga', 'Despacito - Luis Fonsi', 'Antisocial (with Travis Scott) - Ed Sheeran', 'All Mirrors - Angel Olsen', 'Bubbly - Roy Woods', 'Supply - Gurjas Sidhu', 'Magnolia - Playboi Carti', 'Million Reasons - Lady Gaga', "Now's My Time (Nba 2k12 Theme) [feat. Elizabeth Elidades] - D.J.I.G. & Alex Kresovich", 'Cold - NEFFEX', 'Best of Me - NEFFEX', 'Destiny - NEFFEX', 'Renegades - Feeder', 'This Town - Niall Horan', 'Believe - Eminem', '1-800-273-8255 - Logic', 'dirty laundry - blackbear', 'Hate Me (with Juice WRLD) - Ellie Goulding', 'Careless - NEFFEX', 'Sandstorm - Darude', 'Bump & Grind (Bassline Riddim) - Vato Gonzalez', 'Mariah - NAV', '23 - Mike WiLL Made-It', 'Mercy - Shawn Mendes', "Can't Let Go. - B L N D K N G S", 'You Know - NAV', 'Lose Yourself - From "8 Mile" Soundtrack - Eminem', 'Here With Me - Marshmello', 'Natural - Imagine Dragons', "You Can't Stop Me - Andy Mineo", 'Changed My Mind - Tove Styrke', 'Play Me Like a Violin - Stephen', 'I Know - Jocelyn Alice', '1-800-273-8255 - Logic', 'Scared to Be Lonely - Martin Garrix', 'Friends (with BloodPop®) - Justin Bieber', 'iSpy - KYLE', 'Rapper - Jaden', 'Rap Saved Me (feat. Quavo) - 21 Savage', 'Sick Boy - The Chainsmokers', 'Kill The Lights - The Glorious Sons', 'Wanted You (feat. Lil Uzi Vert) - NAV', 'Morning After - dvsn', 'Flashlight - Original Mix - R3HAB', 'After the Party - The Menzingers', 'TEAM - Magic & Bird', "Maybe You're Right - Miley Cyrus", 'Thought It Was a Drought - Future', 'American Idiot - Green Day', 'Back to You (feat. Bebe Rexha & Digital Farm Animals) - Louis Tomlinson', 'Feel So Close - Radio Edit - Calvin Harris', 'High Without Your Love - Loote', 'Kings And Queens Of Summer - Matstubs', 'One More Light - Linkin Park', 'No Vacancy - OneRepublic', 'Tired - Kygo Remix - Alan Walker', 'Despacito - Remix - Luis Fonsi', 'Disrespectful - GASHI']

    missing_songs = []

    for spoty_song in all_spotify_songs:
        result = add_to_ytm(spoty_song)

        if result != "":
            missing_songs.append(result)

    print(missing_songs)



if __name__ == "__main__":

    load_creds("creds.txt")
    print(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, REMOTE_DEBUGGING_PORT, CHROME_DRIVER_PATH)

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                                   client_secret=SPOTIPY_CLIENT_SECRET,
                                                   redirect_uri=REDIRECT_URL,
                                                   scope=SCOPE))



    move_spotify_to_ytm(sp)

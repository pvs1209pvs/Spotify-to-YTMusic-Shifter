# Spotify-to-YTMusic-Shifter

### Instructions (for Linux)
* Install **spotipy** and **selenium** pip packages 
* Create Developer account on Spotify to get your **SPOTIPY_CLIENT_ID** and **SPOTIPY_CLIENT_SECRET**
* Run Chrome in **Debugging Mode** using ```google-chrome --remote-debugging-port=XXXX -user-data-dir=/path/to/dir``` in your terminal.
  * You will have to navigate to where Google Chrome is installed on Linux (should be under ```/usr/bin```).
* Replace XXXX with a valid 4 digit **port number**
* Enter all your credentials to a text file, all on a separate line in the following order:
  * SPOTIPY_CLIENT_ID
  * SPOTIPY_CLIENT_SECRET
  * Port Number
  * Path to Chrome Driver (from https://sites.google.com/chromium.org/driver/)
* Login to https://music.youtube.com/ using your Google Account in the Chrome opened in Debug Mode.
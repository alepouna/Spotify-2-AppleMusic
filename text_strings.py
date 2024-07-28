SSL_ERROR_FIX =("""
                
                This issue is likey because of missing certification for macOS.
                Here are the steps to solution:
                1. Open the folder /Applications/Python 3.x (x is the version you are running).
                2. Double click the Install Certificates.command. It will open a terminal and install the certificate.
                3. Rerun this script.
                """) 

COMMAND_LINE_ERROR ='\nCommand usage:\npython3 convertsongs.py yourplaylist.csv\nMore info at https://github.com/therealmarius/Spotify-2-AppleMusic\n'
PARENT_DIRECTORY_NOT_ALLOWED = "\nERROR: It is not allowed to process the parent directory"

ERROR_401 = "\ERROR: 401 Unauthorized. Please refer to the README and check you have entered your Bearer Token, Media-User-Token and session cookies."
ERROR_403 = "\ERROR: 403 Forbidden. Please refer to the README and check you have entered your Bearer Token, Media-User-Token and session cookies."

CSV_FORMAT_INVALID = '\nERROR: The CSV file is not in the correct format!\nPlease be sure to download the CSV file(s) only from https://watsonbox.github.io/exportify/.\n\n'

MANUALLY_ENTER_BEARER_TOKEN = "\nPlease enter your Apple Music Authorization (Bearer token):\n"
MANUALLY_ENTER_MEDIA_USER_TOKEN = "\nPlease enter your media user token:\n"
MANUALLY_ENTER_SESSION_COOKIES = "\nPlease enter your cookies:\n"
MANUALLY_ENTER_COUNTRY_CODE = "\nPlease enter the country code (e.g., FR, UK, US etc.): "

HOST_ERROR_GETTING_PLAYLIST = "ERROR: Host error while getting playlist. If you recently deleted it, please try again in a few seconds.\n"
PLAYLIST_DESCRIPTION = "A new playlist created via API using Spotify-2-AppleMusic v3"


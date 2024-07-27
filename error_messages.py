SSL_ERROR_FIX =("""
                
                This issue is likey because of missing certification for macOS.
                Here are the steps to solution:
                1. Open the folder /Applications/Python 3.x (x is the version you are running).
                2. Double click the Install Certificates.command. It will open a terminal and install the certificate.
                3. Rerun this script.
                """) 

COMMAND_LINE_ERROR ='\nCommand usage:\npython3 convertsongs.py yourplaylist.csv\nMore info at https://github.com/therealmarius/Spotify-2-AppleMusic\n'

ERROR_401 = "\nError 401: Unauthorized. Please refer to the README and check you have entered your Bearer Token, Media-User-Token and session cookies.\n"
ERROR_403 = "\nError 403: Forbidden. Please refer to the README and check you have entered your Bearer Token, Media-User-Token and session cookies.\n"

CSV_FORMAT_INVALID = '\nThe CSV file is not in the correct format!\nPlease be sure to download the CSV file(s) only from https://watsonbox.github.io/exportify/.\n\n'
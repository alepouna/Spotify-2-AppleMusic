# Imports
from sys import argv
import os
import re
import requests
import csv
import urllib.parse, urllib.request
from time import sleep
import json
from datetime import datetime
from text_strings import *

VERSION = 3
# Delay (in seconds) to wait between tracks (to avoid getting rate limted) - reduce at own risk
delay = 0.5

# By default, results will be written to a JSON file (in results directory). Set to False if you prefer
write_full_results_to_json = True


def write_to_log(*args, **kwargs):
    log_file = 's2am.log'
    now = datetime.now()
    datetime_str = now.strftime('%Y-%m-%dT%H:%M:%S')
    
    if not os.path.exists(log_file):
        open(log_file, 'w').close()
    
    with open(log_file, 'a', encoding='utf-8') as file:
        file.write(f"{datetime_str} {' '.join(map(str, args))}\n")

# def escape_apostrophes(s):
#     return s.replace("'", "\\'")

def remove_apostrophes(s):
    return s.replace("\'", "")

def normalize_string(s):
    # Convert to lowercase
    s = s.lower()
    # Remove specified characters
    s = re.sub(r'[-()&+,.’;:]', '', s)
    # Replace multiple spaces with a single space
    s = re.sub(r'\s+', ' ', s)
    # Remove leading and trailing spaces
    s = s.strip()
    return s

def print_header(playlist_name, number_of_tracks):
    print("\n")
    print("=" * 80)
    print(f"Spotify to Apple Music Converter v{VERSION}")
    print(f"Playlist Name: {playlist_name}")
    print(f"Number of Tracks: {number_of_tracks}")
    print("=" * 80)
    print(f"{'Title':<20} {'Artist':<20} {'Album':<20} {'Found':<7} {'Result':<13}")
    print("=" * 80)

def truncate_text(text, limit):
    if len(text) > limit:
        return text[:limit-3] + "..."
    return text

def print_row(title, artist, album, search_status, result):
    title = truncate_text(title, 20)
    artist = truncate_text(artist, 20)
    album = truncate_text(album, 20)
    search_type = truncate_text(search_status, 7)
    result = truncate_text(result, 13)
    print(f"{title:<20} {artist:<20} {album:<20} {search_type:<7} {result:<13}")

def print_footer(search_results, playlist_results):
    print("=" * 80)
    print(f"Search Results: {search_results}")
    print(f"Add to Playlist Result: {playlist_results}")
    print("=" * 80)
    print("\n")


def get_csv_file_list(arg):
    csv_files = []
    if arg == "..":
        print(PARENT_DIRECTORY_NOT_ALLOWED)
        write_to_log(PARENT_DIRECTORY_NOT_ALLOWED)
        exit(1)
    if arg.endswith(".csv"):
        filename = arg
        csv_files.append(filename)
    else:
        directory = arg
        message_directory = "current directory" if directory == '.' else directory

        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(".csv"):
                    csv_files.append(os.path.join(root, file))
        write_to_log(f"Processing {len(csv_files)} CSV files from {message_directory}.")
        print(f"\nProcessing {len(csv_files)} CSV files from {message_directory}.")
    return csv_files


# Read file contents if it exists, or ask the user to input it
def read_file_contents(f,prompt):
    if os.path.exists(f):
        with open(f,'r') as file:
            return file.read().rstrip('\n')
    else:
        return input(prompt)

def get_connection_data():
    token = read_file_contents("token.dat", MANUALLY_ENTER_BEARER_TOKEN)
    media_user_token = read_file_contents("media_user_token.dat", MANUALLY_ENTER_MEDIA_USER_TOKEN)
    cookies = read_file_contents("cookies.dat", MANUALLY_ENTER_SESSION_COOKIES)
    country_code = read_file_contents("country_code.dat", MANUALLY_ENTER_COUNTRY_CODE)
    return token, media_user_token, cookies, country_code


def csv_file_format_is_valid(header_row):
    if len(header_row) < 17 or header_row[1] != 'Track Name' or header_row[3] != 'Artist Name(s)' or header_row[5] != 'Album Name' or header_row[16] != 'ISRC':
        return False
    return True

def get_song_list(playlist_file):
    # Read the CSV file
    with open(str(playlist_file), encoding='utf-8') as file:
        reader = csv.reader(file)
        header_row = next(reader)  # Read the header row
        
        # Iterate through each row and create a dictionary for the specified columns
        if csv_file_format_is_valid(header_row):
            rows = []
            for row in reader:
                if len(row) > 16:
                    row_dict = {
                        'track_name': remove_apostrophes(row[1]),
                        'artist_name': remove_apostrophes(row[3]),
                        'album_name': remove_apostrophes(row[5]),
                        'isrc': row[16]
                    }
                    rows.append(row_dict) 
                else:
                    # Handle the case where the row doesn't have enough columns
                    print(f"Row does not have enough columns: {row}. Skipping.")
                    write_to_log(f"Row does not have enough columns: {row}. Skipping.")

            # Return a list of dictionaries, each representing a row
            return rows
        else:
            print(CSV_FORMAT_INVALID)
            write_to_log(CSV_FORMAT_INVALID)
            return {} 

# Function to "create AM session"
def create_session(token, media_user_token, cookies):
    with requests.Session() as s:
        s.headers.update({
            "Authorization": f"{token}",
            "media-user-token": f"{media_user_token}",
            "Cookie": f"{cookies}".encode('utf-8'),
            "Host": "amp-api.music.apple.com",
            "Accept-Encoding":"gzip, deflate, br",
            "Referer": "https://music.apple.com/",
            "Origin": "https://music.apple.com",
            #"Content-Length": "45",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            #"TE": "trailers"
            })
        return s

def get_playlist_display_name(playlist_file):
    playlist_name = os.path.basename(playlist_file)
    playlist_name = playlist_name.split('.')
    playlist_name = playlist_name[0]
    playlist_name = playlist_name.replace('_', ' ')
    playlist_name = playlist_name.capitalize()
    return playlist_name

def create_playlist(s, playlist_name):
    url = "https://amp-api.music.apple.com/v1/me/library/playlists"
    data = {
        'attributes': {
            'name': playlist_name,
            'description': PLAYLIST_DESCRIPTION,
        }
    }
    # Test if playlist exists and create it if not
    response = session.get(url)
    if response.status_code == 200:
        for playlist in response.json()['data']:
            try:
                if playlist['attributes']['name'] == playlist_name:
                    write_to_log(f"Playlist {playlist_name} already exists as {playlist['id']}")
                    return playlist['id']
            except:
                print(HOST_ERROR_GETTING_PLAYLIST)
                write_to_log(HOST_ERROR_GETTING_PLAYLIST)
                exit(1)
    response = session.post(url, json=data)
    if response.status_code == 201:
        sleep(0.2)
        write_to_log (f"Playlist {playlist_name} created as {response.json()['data'][0]['id']}")
        return response.json()['data'][0]['id']
    elif response.status_code == 401:
        print(ERROR_401)
        write_to_log(ERROR_401)
        exit(1)
    elif response.status_code == 403:
        print(ERROR_403)
        write_to_log(ERROR_403)
        exit(1)
    else:
        raise Exception(f"Error {response.status_code} while creating playlist {playlist_name}")
        exit(1)

def get_playlist_track_ids(session, playlist_id):
    # test if song is already in playlist
    try:
        response = session.get(f"https://amp-api.music.apple.com/v1/me/library/playlists/{playlist_id}/tracks")
        if response.status_code == 200:
            return [track['attributes']['playParams']['catalogId'] for track in response.json()['data']]
        elif response.status_code == 404:
            return []
        else:
            raise Exception(f"Error {response.status_code} while getting playlist {playlist_id}")
            return None
    except:
        raise Exception(f"Error while getting playlist {playlist_id}")
        return None


def find_track_by_isrc(session, country_code, album_name, artist_name, isrc):
    # Search the Apple Music caralog for a song using the ISRC
    BASE_URL = f"https://amp-api.music.apple.com/v1/catalog/{country_code}/songs?filter[isrc]={isrc}"
    try:
        request = session.get(BASE_URL)
        if request.status_code == 200:
            data = json.loads(request.content.decode('utf-8'))
        else:
            raise Exception(f"Error {request.status_code}\n{request.reason}\n")
        if data["data"]:
            pass
        else:
            return None
    except Exception as e:
        write_to_log(f"An error occured with the ISRC based search request: {e}")
        return print(f"An error occured with the ISRC based search request: {e}")
    
    # Try to match the song with the results
    try:
        for each in data['data']:
            isrc_album_name = normalize_string(remove_apostrophes(each['attributes']['albumName']))
            isrc_artist_name = normalize_string(remove_apostrophes(each['attributes']['artistName']))
            csv_artist_name = normalize_string(artist_name)
            csv_album_name = normalize_string(album_name)

            write_to_log("Sanity Checking Album Name: '" + isrc_album_name + "' from ISRC '" + each['id'] + "' with '" + csv_album_name + "' from CSV")
            write_to_log("Sanity Checking Artist Name: '" + isrc_artist_name + "' from ISRC '" + each['id'] + "' with '" + csv_artist_name + "' from CSV")

            # Sanity check
            if isrc_album_name == csv_album_name and isrc_artist_name == csv_artist_name:
                return str(each['id'])
            elif isrc_album_name == csv_album_name and (isrc_artist_name in csv_artist_name or csv_artist_name in isrc_artist_name):
                return str(each['id'])
            elif isrc_album_name.startswith(csv_album_name[:6]) and isrc_artist_name.startswith(csv_artist_name[:4]):
                return str(each['id'])
            elif isrc_album_name == csv_album_name:
                return str(each['id'])
            else:
                return None
    except:
        return None

def make_text_search_request(url):
    write_to_log("Making request to", url)
    sleep(delay)
    request = urllib.request.Request(url)
    try:
        response = urllib.request.urlopen(request)
        return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        if "orbidden" in str(e):
            write_to_log("403: Forbidden was received from", url)
        elif "SSL: CERTIFICATE_VERIFY_FAILED" in str(e):
            print(SSL_ERROR_FIX)
            write_to_log(SSL_ERROR_FIX)
            exit(1)
        else:
            write_to_log("An error occurred with the Text search request", e)
        return None

def find_track_by_text(country_code, album, artist, title):
    album = normalize_string(album)
    artist = normalize_string(artist)
    title = normalize_string(title)
    
    BASE_URL = f"https://itunes.apple.com/search?country={country_code}&media=music&entity=song&limit=15&term="
    # Search the iTunes catalog for a song
    search_queries = [
        f"{title} {artist} {album}",
        f"{title} {artist}",
        f"{title} {album}",
        title
    ]
    write_to_log("From CSV:", title, "|", artist, "|", album)
    for query in search_queries:
        url = BASE_URL + urllib.parse.quote(query)
        data = make_text_search_request(url)
        if data and data['resultCount'] > 0:
            for each in data['results']:
                track_name = normalize_string(remove_apostrophes(each['trackName']))
                artist_name = normalize_string(remove_apostrophes(each['artistName']))
                collection_name = normalize_string(remove_apostrophes(each['collectionName']))
                track_id = str(each['trackId'])

                write_to_log("From API:", track_name,"|", artist_name,"|", collection_name)

                # Trying to match with the exact track name, artist name and album name
                if track_name == title and artist_name == artist and collection_name == album:
                    write_to_log("Exact match on track name, artist name and album name")
                    return track_id    
                #Trying to match with the first 8 characters of the track name, artist name and album name
                elif track_name[0:8] == title[0:8] and artist_name[0:8] == artist[0:8] and collection_name[0:8] == album[0:5]:    
                    write_to_log("Exact match on first 8 characters of the track name, artist name and album name")
                    return track_id
                #Trying to match with the exact track name and the artist name
                elif track_name == title and artist_name == artist:
                    write_to_log("Exact match on track name and artist name")
                    return track_id
                #Trying to match with the first 8 characters of the track name and the artist name
                elif track_name[0:8] == title[0:8] and artist_name[0:8] == artist[0:8]:
                    write_to_log("Exact match on first 8 characters of the track name and artist name")
                    return track_id
                #Trying to match with the exact track name and the album name
                elif track_name == title and collection_name == album:
                    write_to_log("Exact match on track name and album name")
                    return track_id
                #Trying to match with the first 8 characters of the track name and the album name
                elif track_name[0:8] == title[0:8] and collection_name[0:8] == album[0:5]:
                    write_to_log("Exact match on first 8 characters of the track name and album name")
                    return track_id
                #Trying to match with the exact track name and the artist name, in the case artist name are different between Spotify and Apple Music
                elif track_name == title and (artist_name in artist or artist in artist_name):
                    write_to_log("Exact match on track name and artist name")
                    return track_id
                #Trying to match with the first 8 characters of the track name and the artist name, in the case artist name are different between Spotify and Apple Music
                elif track_name[0:8] == title[0:8] and (artist_name in artist or artist in artist_name):
                    write_to_log("Exact match on first 8 characters of the track name and artist name")
                    return track_id
                #Trying to match with the exact track name and the album name, in the case album name are different between Spotify and Apple Music
                elif track_name == title and (collection_name in album or album in collection_name):
                    write_to_log("Exact match on track name and album name")
                    return track_id 
                #Trying to match with the first 8 characters of the track name and the album name, in the case album name are different between Spotify and Apple Music
                elif track_name[0:8] == title[0:8] and (collection_name in album or album in collection_name):
                    write_to_log("Exact match on first 8 characters of the track name and album name")
                    return track_id
        
    return None

def count_tracks_by_search_method(data):
    search_method_count = {}
    try:
        for entry in data:
            method = entry["search_method"]
            if method in search_method_count:
                search_method_count[method] += 1
            else:
                search_method_count[method] = 1
        return search_method_count
    except:
        return None

def count_tracks_by_result(data):
    try:
        result_count = {}
        for entry in data:
            result = entry["result"]
            if result in result_count:
                result_count[result] += 1
            else:
                result_count[result] = 1
        return result_count
    except:
        return None 

def fetch_equivalent_song_id(session, song_id):
    try:
        request = session.get(f"https://amp-api.music.apple.com/v1/catalog/{country_code}/songs?filter[equivalents]={song_id}")
        if request.status_code == 200:
            data = json.loads(request.content.decode('utf-8'))
            return str(data['data'][0]['id'])
        else:
            return str(song_id)
    except:
        return str(song_id)

def add_song_to_playlist(session, song_id, playlist_id, playlist_track_ids, playlist_name):
    song_id=str(song_id)
    equivalent_song_id = fetch_equivalent_song_id(session, song_id)
    if equivalent_song_id != song_id: 
        write_to_log(f"{song_id} switched to equivalent -> {equivalent_song_id}")
        if equivalent_song_id in playlist_track_ids:
            write_to_log(f"Song {equivalent_song_id} already in playlist {playlist_name}\n")
            return "DUPLICATE"
        song_id = equivalent_song_id
    try:   
        write_to_log("Track ID used for Add Request:", song_id)
        request = session.post(f"https://amp-api.music.apple.com/v1/me/library/playlists/{playlist_id}/tracks", json={"data":[{"id":f"{song_id}","type":"songs"}]})
        # Checking if the request is successful
        if request.status_code == 200 or request.status_code == 201 or request.status_code== 204:
            write_to_log(f"Song {song_id} added successfully")
            return str(song_id)
        # If not, print the error code
        else: 
            write_to_log(f"Error {request.status_code} while adding song {song_id}: {request.reason}\n")
            return "ERROR"
    except:
        print(f"HOST ERROR: Apple Music might have blocked the connection during the add of {song_id}\nPlease wait a few minutes and try again.\nIf the problem persists, please contact the developer.\n")
        write_to_log(f"HOST ERROR: Apple Music might have blocked the connection during the add of {song_id}\nPlease wait a few minutes and try again.\nIf the problem persists, please contact the developer.\n")
        return "ERROR"

def write_json_results(data, filename):
    logs_dir = 'results'
    if not os.path.exists(logs_dir):
        try:
            os.makedirs(logs_dir)
        except OSError:
            pass
    base_name = filename.rsplit('.', 1)[0]
    now = datetime.now()
    datetime_str = now.strftime('%Y%m%d_%H%M%S')
    results_filename = f"{base_name}_results_{datetime_str}.json"
    if os.path.exists(logs_dir):
        full_path = os.path.join(logs_dir, results_filename)
    else:
        full_path = results_filename
    with open(full_path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)
    write_to_log("Wrote full results to", full_path)

def write_failure_log(data, filename):
    base_name = filename.rsplit('.', 1)[0]
    now = datetime.now()
    datetime_str = now.strftime('%Y%m%d_%H%M%S')
    results_filename = f"{base_name}_failure_{datetime_str}.txt"
    with open(results_filename, 'w', encoding='utf-8') as file:
        for entry in data:
            line = f"{entry['track_name']} | {entry['artist_name']} | {entry['album_name']} (Seach Status: {entry['search_status']} | Addding to Playlist: {entry['result']})\n"
            file.write(line)
    write_to_log("Wrote failure log to", results_filename)


if __name__ == "__main__":
    write_to_log("="*80)
    write_to_log(f"Apple Music Playlist Converte v{VERSION}")
    write_to_log("Program was started")
    write_to_log("Rate limit delay is", delay)
    
    # Get the connection data
    token, media_user_token, cookies, country_code = get_connection_data()
    write_to_log("Country code is", country_code)
    write_to_log("Token length is", len(token))
    write_to_log("Media User Token length is", len(media_user_token))
    write_to_log("Cookies length is", len(cookies))

    # If a single CSV file is provided, use it, otherwise get all CSV files in the directory
    try:    
        csv_files = get_csv_file_list(argv[1])
    except IndexError:
        print("ERROR: No CSV file or directory provided")
        write_to_log("ERROR: No CSV file or directory provided")
        exit(1)
    
    # Create the remote session
    session = create_session(token, media_user_token, cookies)
    
    # Loop through the CSV files
    for playlist_file in csv_files:
        if not os.path.exists(playlist_file):
            print ("\nERROR: playlist file not found")
            write_to_log ("ERROR: playlist file not found")
            exit(1)
        else:
            write_to_log ("="*80)
            write_to_log ("Processing", playlist_file)

        #Get the display name for the playlist 
        playlist_display_name = get_playlist_display_name(playlist_file)
       
        # Read the CSV file for this playlist
        song_list = get_song_list(playlist_file)
        write_to_log(len(song_list), "tracks found for", playlist_display_name)
    
        # Print the table header
        print_header(playlist_display_name, len(song_list))
        
        # Check if playlist already exists and if not create a new one, then get a list of track ids from the playlist
        playlist_id = create_playlist(session, playlist_display_name)
        playlist_track_ids = get_playlist_track_ids(session, playlist_id)
       
        # Loop through the songs to find the track id and add it to the playlist
        for index, song in enumerate(song_list, start=1):
            sleep(delay)
            write_to_log("-"*80)
            write_to_log("Processing track", index, "of", len(song_list))
            write_to_log("Searching for " + song['track_name'] + " by " + song['artist_name'] + " from album " + song['album_name'])
            write_to_log("Searching using ISRC", song['isrc'])
            track_id = find_track_by_isrc(session, country_code, song['album_name'],song['artist_name'],song['isrc'])

            if track_id:
                if str(track_id) in playlist_track_ids:
                    write_to_log("From ISRC Search got", track_id, "which is already in playlist")
                    song['track_id'] = track_id
                    song['search_method'] = "ISRC"
                    song['search_status'] = "DUPLICATE"
                else:
                    write_to_log("From ISRC Search, will add", track_id)
                    song['track_id'] = track_id
                    song['search_method'] = "ISRC"
                    song['search_status'] = "OK"
            else:
                write_to_log("Track not found using ISRC, will try text search")
                track_id = find_track_by_text(country_code, song['album_name'],song['artist_name'],song['track_name'])
                if track_id:
                    if str(track_id) in playlist_track_ids:
                        write_to_log("From Text Search got", track_id, "which is already in playlist")
                        song['track_id'] = track_id
                        song['search_method'] = "TEXT"
                        song['search_status'] = "DUPLICATE"
                    else:
                        write_to_log("From Text Search, will add", track_id)
                        song['track_id'] = track_id
                        song['search_method'] = "TEXT"
                        song['search_status'] = "OK"
                else:
                    write_to_log("Track not found using text search - Skipping")
                    song['track_id'] = "NOT_FOUND"
                    song['search_method'] = "NOT_FOUND"
                    song['search_status'] = "NOT_FOUND"

            if song['search_status'] == "OK":
                result = add_song_to_playlist(session, song['track_id'], playlist_id, playlist_track_ids, playlist_display_name) 
                if result == "ERROR":
                    write_to_log("Failed to add", song['track_id'], "to", playlist_display_name)
                    song['result'] = "ERROR"
                elif result == "DUPLICATE":
                    write_to_log("Skipped adding duplicate", song['track_id'], "to", playlist_display_name)
                    song['result'] = "DUPLICATE"
                else:
                    song['result'] = "ADDED"
                    song['added_track_id'] = result
            else:
                song['result'] = "SKIPPED"
                song['added_track_id'] = "SKIPPED"

            # Print the table row
            print_row(song['track_name'], song['artist_name'], song['album_name'], song['search_status'], song['result'])


        # Results summary
        search_results = count_tracks_by_search_method(song_list)
        playlist_results = count_tracks_by_result(song_list)

        # Print the table footer
        print_footer(search_results, playlist_results)

        write_to_log("-"*80)
        write_to_log("Tracks found by search method:", count_tracks_by_search_method(song_list))
        write_to_log("Tracks added by result:",count_tracks_by_result(song_list))

        # Write a json file with the full results
        if write_full_results_to_json:
            write_json_results(song_list, playlist_file)

        # Write a json file with the failure results only
        #failure_list = [song for song in song_list if (song.get('search_status') == "OK" and song.get('result') != "ADDED") or song.get('search_status') != "OK" ]
        
        failure_list = [song for song in song_list if ((song.get('search_status') == "OK" and song.get('result') != "ADDED") or (song.get('search_status') != "OK" and song.get('search_status') != "DUPLICATE"))]
        if failure_list:
            write_failure_log(failure_list, playlist_file)

        write_to_log("Finished processing", playlist_file)
        write_to_log ("="*80)
    write_to_log("Finished processing all CSV files")
    write_to_log ("Program Ended")

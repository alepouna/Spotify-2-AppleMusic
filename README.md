# Spotify to Apple Music - Docker Edition

This is a version of [https://github.com/nf1973/Spotify-2-AppleMusic] for Docker.

For instructions on how to use the app without Docker, what it does, etc. please see [https://github.com/nf1973/Spotify-2-AppleMusic]

## Env Variables

- `delay` Delay between tracks (in seconds) to prevent rate limits. Adjust at your own risk.

## Volumes

This version requires you to mount a volume into `/app/data` (see [docker-compose.yml](./docker-compose.yml) example) which needs to contain:

- A folder called `playlists` which will need to have the .csv of your playlists from Spotify
- A file `token.dat`
- A file `media_user_token.dat`
- A file `cookies.dat`
- A file `country_code.dat`

Note in the feature these might be set as enviornmental variables.

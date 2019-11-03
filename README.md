# Qo-DL Reborn
Tool written in Python to download streamable tracks from Qobuz.

![](https://orion.feralhosting.com/sorrow/qo_rb.jpg)

[COMPILED BUILDS HERE](https://github.com/Sorrow446/Qo-DL-Reborn/releases)

# Setup
## Quickstart ##
Input the following field values for the keys below into your config file:
- email
- password; md5 hashed
- quality

## Config file ##
Key  | Info
------------- | -------------
email  | -
password  | -
quality  | Track download quality. 1 = MP3 320, 2 = 16-bit FLAC, 3 = 24-bit / =< 96kHz FLAC, 4 = best. If your chosen quality isn't available, the next best quality will be used.
keep_cover  | If true, the album's cover will be kept and renamed to from "cover.jpg" to "folder.jpg" instead of being deleted. Only applies to album or track URL (not plist etc.).
cover_size  | - Size cover to request from API. 1 = 50x50, 2 = 230x230, 3 = 600x600. 4 = max. If no album cover is returned, it won't be written to the album's tracks.
download_dir  | - Directory to download to. Tracks won't be downloaded to a temp directory beforehand. Default = Qo-DL Reborn downloads.
embed_cover  | - If true, album covers will be written to tracks.
filename_template | - You may use any of tags under the "tags" section in your config file (make sure you wrap them in curly brackets). Can be combined with plain text.
<all tags under "tags" section> | If true, the corresponding tag will be written to tracks. If the API doesn't return metadata for a specific tag, it won't be written to.
comment | Write custom comment to comment tag in tracks.

**Bools must be all lowercase.**

# Usage
Supported media:    

Type  | Example
------------- | -------------
Album  | `https://play.qobuz.com/album/hxyqb40xat3uc`, `https://www.qobuz.com/gb-en/album/mount-to-nothing-sangam/hxyqb40xat3uc`
Artist page  | `https://play.qobuz.com/artist/1619283`
Favourited albums  | `https://play.qobuz.com/user/library/favorites/albums`
Favourited tracks  | `https://play.qobuz.com/user/library/favorites/tracks`
Playlist  | `https://play.qobuz.com/playlist/1452423`
Track | `https://open.qobuz.com/track/48237909`

Qo-DL Reborn may also be used via CLI.    

```
usage: qo-dl_reborn.py [-h] -u URL [-q QUALITY] [-p--path P__PATH] [-c CSIZE]
                       [-k] [-C COMMENT] [-e]

Tool written in Python to download streamable tracks from Qobuz.

optional arguments:
  -h, --help            show this help message and exit
  -u URL, --url URL     URL. Supported: album, artist page, fav albums, fav tracks, playlist, track.
  -q QUALITY, --quality QUALITY
                        Track download quality. 1 = MP3 320, 2 = 16-bit FLAC,
                        3 = 24-bit / =< 96kHz FLAC, 4 = best. If your chosen
                        quality isn't available, the next best quality will be
                        used.
  -p--path P__PATH      Directory to download to. Tracks won't be downloaded
                        to a temp directory beforehand. Make sure you wrap
                        this up in double quotes.
  -c CSIZE, --csize CSIZE
                        Size cover to request from API. 1 = 50x50, 2 =
                        230x230, 3 = 600x600. 4 = max. If no album cover is
                        returned, it won't be written to the album's tracks.
  -k, --keepcov         Leave folder.jpg in album dir. Y or N.
  -C COMMENT, --comment COMMENT
                        Write custom comment to comment tag in tracks. Make
                        sure you wrap this up in double quotes.
  -e, --embedcov        If true, album covers will be written to tracks.
  ```


**You can't download ANY tracks with a free account.**

If you need to get in touch: Sorrow#5631, [Reddit](https://www.reddit.com/user/Sorrow446)

# Disclaimer
I will not be responsible for how you use Qo-DL Reborn.    
Qobuz brand and name is the registered trademark of its respective owner.    
Qo-DL Reborn has no partnership, sponsorship or endorsement with Qobuz.    

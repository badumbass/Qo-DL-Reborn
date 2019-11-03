#!/usr/bin/env python3

import os
import re
import sys
import json
import time
import argparse
import platform
import traceback
from datetime import datetime

import qopy
import requests
from tqdm import tqdm
from mutagen import File
import mutagen.id3 as id3
from mutagen.flac import FLAC, Picture
from mutagen.id3 import ID3NoHeaderError

client = qopy.Client()

def print_title():
	print("""
 _____         ____  __       _____     _               
|     |___ ___|    \|  |     | __  |___| |_ ___ ___ ___ 
|  |  | . |___|  |  |  |__   |    -| -_| . | . |  _|   |
|__  _|___|   |____/|_____|  |__|__|___|___|___|_| |_|_|
   |__|
   
   """)

def get_os():
	if platform.system() == 'Windows':
		return True
	else:
		return False

def os_cmds(arg):
	if get_os():
		if arg == "c":
			os.system('cls')
		elif arg == "t":
			os.system('title Qo-DL Reborn R1 (by Sorrow446 ^& DashLt)')
	else:
		if arg == "c":
			os.system('clear')
		elif arg == 't':
			sys.stdout.write('\x1b]2;Qo-DL Reborn R1 (by Sorrow446 & DashLt)\x07')

def parse_prefs(cfg, tag_cfg):
	if cfg:
		parser = argparse.ArgumentParser(
			description='Tool written in Python to download streamable tracks from Qobuz.')
		parser.add_argument(
			'-u', '--url',
			default='',
			required=True,
			help='URL. Supported: album, artist page, fav albums, fav tracks, playlist, track.')
		parser.add_argument(
			'-q', '--quality',
			default=cfg['qual'],
			help='Track download quality. 1 = MP3 320, 2 = 16-bit FLAC, 3 = 24-bit / =< 96kHz FLAC, 4 = best. '
				 'If your chosen quality isn\'t available, the next best quality will be used.')
		parser.add_argument(
			'-p' '--path',
			default=cfg['dir'],
			help='Directory to download to. Tracks won\'t be downloaded to a temp directory beforehand. '
			     'Make sure you wrap this up in double quotes.')
		parser.add_argument(
			'-c', '--csize',
			default=cfg['cov_size'],
			help='Size cover to request from API. 1 = 50x50, 2 = 230x230, 3 = 600x600. '
			     '4 = max. If no album cover is returned, it won\'t be written to the album\'s tracks.')
		parser.add_argument(
			'-k', '--keepcov',
			default=cfg['keep_cov'],
			action='store_true',
			help='Leave folder.jpg in album dir. Y or N.')
		parser.add_argument(
			'-C', '--comment',
			default=tag_cfg['COMMENT'],
			help='Write custom comment to comment tag in tracks. Make sure you wrap this up in double quotes.')
		parser.add_argument(
			'-e', '--embedcov',
			default=cfg['embed_cov'],
			action='store_true',
			help='If true, album covers will be written to tracks.')
		args = parser.parse_args()
		cfg['qual'] = args.quality
		cfg['keep_cov'] = args.keepcov
		cfg['embed_cov'] = args.embedcov
		cfg['cov_size'] = args.csize
		cfg['dir'] = args.p__path
		cfg['url'] = args.url
		tag_cfg['COMMENT'] = args.comment
		return cfg, tag_cfg
	else:
		with open('config.json') as f:
			cfg = json.load(f)
		rt_opts={
			"email": cfg['creds']['email'],
			"pwd": cfg['creds']['password'],
			"qual": cfg['prefs']['quality'],
			"keep_cov": cfg['prefs']['keep_cover'],
			"embed_cov": cfg['prefs']['embed_cover'],
			"cov_size": cfg['prefs']['cover_size'],
			"dir": cfg['prefs']['download_dir'],
			"filename_template": cfg['prefs']['filename_template']}
		tags={
			"ALBUM": cfg['prefs']['tags']['album'],
			"ALBUMARTIST": cfg['prefs']['tags']['albumartist'],
			"ARTIST": cfg['prefs']['tags']['artist'],
			"COMMENT": cfg['prefs']['tags']['comment'],
			"COMPOSER": cfg['prefs']['tags']['composer'],
			"COPYRIGHT": cfg['prefs']['tags']['copyright'],
			"DISCNUMBER": cfg['prefs']['tags']['discnumber'],
			"DISCTOTAL": cfg['prefs']['tags']['disctotal'],
			"DATE": cfg['prefs']['tags']['year'],
			"GENRE": cfg['prefs']['tags']['genre'],
			"ISRC": cfg['prefs']['tags']['isrc'],		
			"LABEL": cfg['prefs']['tags']['label'],
			"PERFORMER": cfg['prefs']['tags']['performer'],		
			"TITLE": cfg['prefs']['tags']['title'],
			"URL": cfg['prefs']['tags']['url'],
			"UPC": cfg['prefs']['tags']['upc'],
			"TRACKNUMBER": cfg['prefs']['tags']['tracknumber'],
			"TRACKTOTAL": cfg['prefs']['tags']['tracktotal'],		
			"YEAR": cfg['prefs']['tags']['year']}
	qual = rt_opts['qual']
	cov_size = rt_opts['cov_size']
	dl_dir = rt_opts['dir']
	qual_dict = {
		1: 5,
		2: 6,
		3: 7,
		4: 27}
	cov_dict = {
		1: "_50.jpg",
		2: "_230.jpg",
		3: "_600.jpg",
		4: "_max.jpg"}
	if not dl_dir.strip():
		dl_dir = "Qo-DL Reborn downloads"
	rt_opts['dir'] = dl_dir
	rt_opts['qual'] = qual_dict[qual]
	rt_opts['cov_size'] = cov_dict[cov_size]
	return rt_opts, tags
	
def get_id(url):
	return re.match(r'https?://(?:w{0,3}|play|open)\.qobuz\.com/(?:(?:album|track|artist'
		'|playlist|label)/|[a-z]{2}-[a-z]{2}/album/-?\w+(?:-\w+)*-?/|user/library/favorites/)(\w+)', url).group(1)

def get_type(url):
	type = url.split('/')[3]
	if not type in ['album', 'artist', 'playlist', 'track', 'label']:
		if type == "user":
			type = url.split('/')[-1]
		else:
			type = url.split('/')[4]
	return type

def exist_check(f):
	if os.path.isfile(f):
		if f.endswith(('.flac', '.mp3')):
			return True
		os.remove(f)
	return False

def sanitize(f):
	if get_os():
		return re.sub(r'[\\/:*?"><|]', '-', f)
	else:
		return re.sub('/', '-', f)	

def dir_setup(dir):
	if not os.path.isdir(dir):
		os.makedirs(dir)

def download_booklet(album_fol_s, goodies):
	if goodies:
		booklet = None
		for goodie in goodies:
			if goodie['file_format_id'] == 21:
				booklet = goodie['url']
				break
		if booklet:
			booklet_dir = os.path.join(album_fol_s, "booklet.pdf")
			print("Booklet available. Downloading...")
			download_cov(booklet, booklet_dir)
	# Reserved code to download multiple booklets for
	# when and if Qobuz fix them.
	# b_list = []
	# for goodie in goodies:
		# if goodie['file_format_id'] == 21:
			# b_list.append(goodie['url'])
	# tot = len(b_list)
	# if tot == 1:
		# print("Booklet available. Downloading...")
	# else:
		# print(str(tot) + " booklets available. Downloading...")
	# num = 0
	# for url in b_list:
		# num =+ 1
		# if num == 1:
			# cov = os.path.join(album_fol_s, "booklet.pdf")
		# else:
			# cov = os.path.join(album_fol_s, "booklet_" + str(num) + ".pdf")
		# download_cov(url, cov)
		
def download_cov(url, cov):
	exist_check(cov)
	r = requests.get(url)
	if r.status_code == 404:
		print("This album has no cover.")
		return False
	r.raise_for_status()
	with open (cov, 'wb') as f:
		f.write(r.content)
	return True
	
def parse_meta(src, meta, num, tot):
	if meta:
		if src['version']:
			title = src.get('title') + " (" + src['version'].strip() + ")"
		else:
			title = src.get('title')
		if num:
			tracknum = num
		else:
			tracknum = src.get('track_number')
		meta['ARTIST'] = src.get('performer', {}).get('name')
		meta['ISRC'] = src.get('isrc')
		meta['DISCNUMBER'] = src.get('media_number')
		meta['TITLE'] = title
		meta['TRACKNUMBER'] = tracknum
		meta['PERFORMER'] = src.get('performer', {}).get('name')
	else:
		if tot:
			tracktot = tot
		else:
			tracktot = src.get('tracks_count')
		meta={
			"ALBUMARTIST": src.get('artist', {}).get('name'),
			"TRACKTOTAL": tracktot,
			"COMPOSER": src.get('composer', {}).get('name'),
			"DISCTOTAL": src.get('media_count'),
			"ALBUM": src.get('title'),
			"LABEL": src.get('label', {}).get('name'),
			"COPYRIGHT": src.get('copyright'),
			"URL": src.get('url'),
			"UPC": src.get('upc'),
			"GENRE": src.get('genre', {}).get('name'),
			"YEAR": datetime.fromtimestamp(src.get('released_at')).strftime('%Y')}
	return meta

def write_tags(f, meta, tag_cfg, cov, ext, embed_cov):
	if ext == ".flac":
		audio = FLAC(f)
		for k, v in meta.items():
			if tag_cfg[k]:
				audio[k] = str(v)
		if embed_cov and cov:
			with open(cov, 'rb') as cov_obj:
				image = Picture()
				image.type = 3
				image.mime = "image/jpeg"
				image.data = cov_obj.read()
				audio.add_picture(image)
		audio.save()
	elif ext == ".mp3":
		try: 
			audio = id3.ID3(f)
		except ID3NoHeaderError:
			audio = id3.ID3()
		if tag_cfg['TRACKNUMBER'] and tag_cfg['TRACKTOTAL']:
			audio['TRCK'] = id3.TRCK(encoding=3, text=str(meta['TRACKNUMBER']) + "/" + str(meta['TRACKTOTAL']))
		elif tag_cfg['TRACKNUMBER']:
			audio['TRCK'] = id3.TRCK(encoding=3, text=str(meta['TRACKNUMBER']))
		if tag_cfg['DISCNUMBER']:
			audio['TPOS'] = id3.TPOS(encoding=3, text=str(meta['DISCNUMBER']) + "/" + str(meta['DISCTOTAL']))	
		legend={
			"ALBUM": id3.TALB,
			"ALBUMARTIST": id3.TPE2,
			"ARTIST": id3.TPE1,
			"COMMENT": id3.COMM,
			"COMPOSER": id3.TCOM,
			"COPYRIGHT": id3.TCOP,
			"DATE": id3.TDAT,
			"GENRE": id3.TCON,
			"ISRC": id3.TSRC,
			"LABEL": id3.TPUB,
			"PERFORMER": id3.TOPE,
			"TITLE": id3.TIT2,
			# Not working.
			"URL": id3.WXXX,
			"YEAR": id3.TYER}
		for k, v in meta.items():
			try:
				if tag_cfg[k]:
					id3tag = legend[k]
					audio[id3tag.__name__] = id3tag(encoding=3, text=v)
			except KeyError:
				pass
		if embed_cov and cov:
			with open(cov, 'rb') as cov_obj:
				audio.add(id3.APIC(3, 'image/jpeg', 3, '', cov_obj.read()))
		audio.save(f, 'v2_version=3')
	
def download_track(url_resp, title, pre, num, tot, qual, ref):
	try:
		if url_resp['sample']:
			print("The API returned the sample of the track instead of the full length track. "
				  "Maybe it's not allowed to be streamed. Skipped.")
			return False
	except KeyError:
		pass
	ret_qual = url_resp.get('format_id')
	if qual != 5:
		if ret_qual == 5:
			print("Track unavailable in FLAC. Using MP3 320 instead...")	
	if ret_qual != 5:
		spec = "{}-bit / {}kHz FLAC".format(url_resp['bit_depth'], url_resp['sampling_rate'])
	else:
		spec = "MP3 320"
	print("Downloading track {} of {}: {} - {}".format(num, tot, title, spec))
	r = requests.get(url_resp['url'], stream=True, headers={
		'Range':'bytes=0-',
		"Referer": "https://play.qobuz.com/" + ref,
		"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
			"(KHTML, like Gecko) Chrome/73.0.3683.75 Safari/537.36"})
	r.raise_for_status()
	size = int(r.headers.get('content-length', 0))
	with open(pre, 'wb') as f:
		with tqdm(total=size, unit='B',
			unit_scale=True, unit_divisor=1024,
			initial=0, miniters=1) as bar:		
				for chunk in r.iter_content(32*1024):
					if chunk:
						f.write(chunk)
						bar.update(len(chunk))
	return True

def download(id, album_fol_s, meta, num, tot, fol, qual, cov, ref, tag_cfg, fn_template, cov_dir, embed_cov):
	if not fn_template.strip():
		fn_template = str(num) + ". " +  meta['TITLE']
	else:
		fn_template = fn_template.upper().format(**meta)
	title = meta['TITLE']
	if not tot:
		tot = meta['TRACKTOTAL']
	pre = os.path.join(album_fol_s, str(num) + ".qo-dl_download")	
	url_resp = client.get_track_url(id, qual)
	if url_resp['format_id'] == 5:
		ext = ".mp3"
	else:
		ext = ".flac"
	post = os.path.join(album_fol_s, sanitize(fn_template) + ext)
	exist_check(pre)
	if exist_check(post):
		print("Track already exists locally. Skipped.")
		return
	if download_track(url_resp, title, pre, num, tot, qual, ref):
		write_tags(pre, meta, tag_cfg, cov_dir, ext, embed_cov)
		try:
			os.rename(pre, post)
		except OSError:
			print("Failed to rename track.")

def main(type, id, cfg, tag_cfg, fol, cli):
	dl_dir = cfg['dir']
	qual = cfg['qual']
	cov_size = cfg['cov_size']
	keep_cov = cfg['keep_cov']
	embed_cov = cfg['embed_cov']
	fn_template = cfg['filename_template']
	while True:
		if not cli:
			if not fol:
				url, id = None, None
				url = input('Input URL: ').strip()
				if not url:
					os_cmds('c')
					print_title()
					continue
		if cli:
			url = cfg['url']
		if not id:
			try:
				id = get_id(url)
			except AttributeError:
				if cli:
					print("Invalid URL.")
					sys.exit(1)
				print("Invalid URL. Returning to URL input screen...")
				time.sleep(1)
				os_cmds('c')
				print_title()
				continue
		if not type:
			type = get_type(url)
		# if not cli:
			# os_cmds('c')
		if type == "album":
			num = 0
			src_meta = client.get_album_meta(id)
			al_meta = parse_meta(src_meta, None, None, None)
			album_fol = al_meta['ALBUMARTIST'] + " - " + al_meta['ALBUM']
			print(album_fol + "\n")
			if fol is not None:
				album_fol_s = os.path.join(dl_dir, fol, sanitize(album_fol))
			else:
				album_fol_s = os.path.join(dl_dir, sanitize(album_fol))
			dir_setup(album_fol_s)
			cov = src_meta['image']['thumbnail'].split('_')[0] + cov_size
			cov_dir = os.path.join(album_fol_s, "cover.jpg")
			if not download_cov(cov, cov_dir):
				cov_dir = None
			ref = "album/" + str(src_meta['id'])
			for track in src_meta['tracks']['items']:
				num += 1
				final_meta = parse_meta(track, al_meta, num, None)	
				download(track['id'], album_fol_s, final_meta, num, None, fol, qual, cov, ref, tag_cfg, fn_template, cov_dir, embed_cov)
			download_booklet(album_fol_s, src_meta.get('goodies'))
		elif type == "track":
			src_meta = client.get_track_meta(id)
			al_meta = parse_meta(src_meta['album'], None, None, None)
			final_meta = parse_meta(src_meta, al_meta, None, None)
			album_fol = al_meta['ALBUMARTIST'] + " - " + al_meta['ALBUM']
			album_fol_s = os.path.join(dl_dir, sanitize(album_fol))
			dir_setup(album_fol_s)
			cov = src_meta['album']['image']['thumbnail'].split('_')[0] + cov_size
			cov_dir = os.path.join(album_fol_s, "cover.jpg")
			if not download_cov(cov, cov_dir):
				cov_dir = None
			ref = "album/" + str(src_meta['album']['id'])
			download(src_meta['id'], album_fol_s, final_meta, 1, 1, fol, qual, cov, ref, tag_cfg, fn_template, cov_dir, embed_cov)
			download_booklet(album_fol_s, src_meta.get('album', {}).get('goodies'))
		elif type in ["playlist", "tracks"]:
			num = 0
			if type == "playlist":
				src_meta = client.get_plist_meta(id)
			else:
				src_meta = client.get_favourites(type)
			for dict in src_meta:
				if num == 0:
					if type == "playlist":
						if not dict['is_public']:
							print("Playlist is private. Can't download. Returning to URL input screen...")
							time.sleep(2)
							os_cmds('c')
							return
						tot = dict['tracks_count']
						id = dict['id']
						title = dict['name']
						owner = dict['owner']['name']
						ref = "playlist/" + str(id)
						# Append ID to prevent possible clashes.
						album_fol = owner + " - " + title + " [" + str(id) + "]"
						album_fol_s = os.path.join(dl_dir, sanitize(album_fol))
						tracks = dict['tracks']['items']
						print(owner + " - " + title + "\n")
					else:
						tot = dict['total']
						ref = 'user/library/favorites/tracks'
						album_fol_s = os.path.join(dl_dir, "Favourited tracks")
						tracks = dict['items']
						print("Favourited tracks")
					dir_setup(album_fol_s)
				for track in tracks:
					num += 1
					al_meta = parse_meta(track['album'], None, None, tot)
					cov = track['album']['image']['thumbnail'].split('_')[0] + cov_size
					cov_dir = os.path.join(album_fol_s, "cover.jpg")
					if not download_cov(cov, cov_dir):
						cov_dir = None
					final_meta = parse_meta(track, al_meta, num, None)
					download(track['id'], album_fol_s, final_meta, num, tot, fol, qual, cov, ref, tag_cfg, fn_template, cov_dir, embed_cov)
			os.remove(cov_dir)
		elif type in ["artist", "label", "albums"]:
			if type == "artist":
				src_meta = client.get_artist_meta(id)	
			elif type == "label":		
				src_meta = client.get_label_meta(id)
			else:
				src_meta = client.get_favourites(type)
			num = 0
			for dict in src_meta:
				if num == 0:
					if type == "albums":
						tot = dict['total']
						ref = 'user/library/favorites/tracks'
						title = "Favourited albums"
						albums = dict['items']
						print(title + "\n")
					else:
						tot = dict['albums_count']
						title = dict['name']
						ref = type + "/" + str(dict['id'])
						albums = dict['albums']['items']
						print(title)
				for album in albums:			
					album_fol_s = os.path.join(dl_dir, sanitize(title))
					dir_setup(album_fol_s)	
					cov = album['image']['thumbnail'].split('_')[0] + cov_size
					cov_dir = os.path.join(album_fol_s, "cover.jpg")
					if not download_cov(cov, cov_dir):
						cov_dir = None
					num += 1
					print("\nDownloading album " + str(num) + " of " + str(tot) + ":")
					# The artist & label epoint don't include track meta we need. Run IDs through album ripping code.
					main('album', album['id'], cfg, tag_cfg, sanitize(title), cli)
		if cov_dir is not None and keep_cov:
			out_fn = os.path.join(album_fol_s, "folder.jpg")
			exist_check(out_fn)
			os.rename(cov_dir, out_fn)
		elif cov_dir:
			if os.path.isfile(cov_dir):
				os.remove(cov_dir)
		if fol:
			break
		if cli:
			sys.exit()
		os_cmds('c')
		print_title()
	
if __name__ == '__main__':
	try:
		os_cmds('t')
		print_title()
		cfg, tag_cfg = parse_prefs(None, None)
		try:
			if sys.argv[1]:
				cfg, tag_cfg = parse_prefs(cfg, tag_cfg)
				cli = True
		except IndexError:
			cli = False
		label = client.auth(cfg['email'], cfg['pwd'])
		print("Signed in successfully - " + label + " account.\n")
		main(False, False, cfg, tag_cfg, None, cli)
	except (KeyboardInterrupt, SystemExit):
		sys.exit()
	except:
		traceback.print_exc()
		input('\nAn exception has occurred. Press enter to exit.')
		sys.exit()

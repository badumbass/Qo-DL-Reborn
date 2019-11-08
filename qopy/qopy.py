# Wrapper for Qo-DL Reborn. Sorrow446.

import os
import time
import json
import hashlib
import requests
import tempfile
import platform

import spoofbuz
from qopy.exceptions import AuthenticationError, IneligibleError, InvalidAppSecretError, InvalidAppIdError

class Client:
	def __init__(self, **kwargs):
		self.id, self.sec = self.cfg_setup(False)
		self.session = requests.Session()
		self.session.headers.update({
			'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0',
			"X-App-Id": self.id})
		self.base = 'https://www.qobuz.com/api.json/0.2/'

	def api_call(self, epoint, **kwargs):
		if epoint == "user/login?":	
			params={
				"email": kwargs['email'],
				"password": kwargs['pwd']}
		elif epoint == "track/get?":
			params={
				"track_id": kwargs['id']}					
		elif epoint == "album/get?":
			params={
				"album_id": kwargs['id']}
		elif epoint == "playlist/get?":
			params={
				"extra": 'tracks',
				"playlist_id": kwargs['id'],
				"limit": 500,
				"offset": kwargs['offset']}
		elif epoint == "artist/get?":
			params={
				"app_id": self.id,
				"artist_id": kwargs['id'],
				"limit": 500,
				"offset": kwargs['offset'],
				"extra": 'albums'}
		elif epoint == "label/get?":
			params={
				"label_id": kwargs['id'],
				"limit": 500,
				"offset": kwargs['offset'],
				"extra": 'albums'}
		elif epoint == "favorite/getUserFavorites?":
			params={
				"app_id": self.id,
				"limit": 500,
				"offset": kwargs['offset'],
				"type": kwargs['type']}		
		elif epoint == "userLibrary/getAlbumsList?":
			unix = time.time()
			r_sig = "userLibrarygetAlbumsList" + str(unix) + kwargs['sec']
			r_sig_hashed = hashlib.md5(r_sig.encode('utf-8')).hexdigest()
			params={
				"app_id": self.id,
				"user_auth_token": self.uat,
				"request_ts": unix,
				"request_sig": r_sig_hashed}
		elif epoint == "track/getFileUrl?":
			unix = time.time()
			track_id = kwargs['id']
			fmt_id = kwargs['fmt_id']
			r_sig = "trackgetFileUrlformat_id{}intentstreamtrack_id{}{}{}".format(fmt_id, track_id, unix, self.sec)
			r_sig_hashed = hashlib.md5(r_sig.encode('utf-8')).hexdigest()
			params={
				"request_ts": unix,
				"request_sig": r_sig_hashed,
				"track_id": track_id,
				"format_id": fmt_id,
				"intent": 'stream'}
		r = self.session.get(self.base + epoint, params=params)
		# Do ref header.
		if epoint == "user/login?":
			if r.status_code == 401:
				raise AuthenticationError('Invalid credentials.')		
			elif r.status_code == 400:
				raise InvalidAppIdError('Invalid app id.')
		elif epoint in ["track/getFileUrl?", "userLibrary/getAlbumsList?"]:
			if r.status_code == 400:
				raise InvalidAppSecretError('Invalid app secret.')
		r.raise_for_status()
		return r.json()

	def auth(self, email, pwd):
		try:
			usr_info = self.api_call('user/login?', email=email, pwd=pwd)
		except InvalidAppIdError:
			self.id, self.sec = self.cfg_setup(True)
			usr_info = self.api_call('user/login?', email=email, pwd=pwd)
		if not usr_info['user']['credential']['parameters']:
			raise IneligibleError("Free accounts are not eligible to download tracks.")
		self.uat = usr_info['user_auth_token']
		self.session.headers.update({
			"X-User-Auth-Token": self.uat})
		# Qo-DL only needs the subscription type.
		return usr_info['user']['credential']['parameters']['short_label']
	
	def get_album_meta(self, id):
		return self.api_call('album/get?', id=id)
	
	def get_track_meta(self, id):
		return self.api_call('track/get?', id=id)
	
	def get_track_url(self, id, fmt_id):
		try:
			return self.api_call('track/getFileUrl?', id=id, fmt_id=fmt_id)
		except InvalidAppSecretError:
			self.id, self.sec = self.cfg_setup(True)
			return self.api_call('track/getFileUrl?', id=id, fmt_id=fmt_id)
	
	# Metadata which could require multiple calls (500+ items).
	def multi_meta(self, epoint, key, id, type):
		total = 1
		offset = 0
		while total > 0:
			if type in ["tracks", "albums"]:
				j = self.api_call(epoint, id=id, offset=offset, type=type)[type]
			else:
				j = self.api_call(epoint, id=id, offset=offset, type=type)
			if offset == 0:
				yield j
				total = j[key] - 500
			else:
				yield j
				total -= 500
			offset += 500
	
	def get_label_meta(self, id):
		return self.multi_meta('label/get?', 'albums_count', id, None)
	
	def get_plist_meta(self, id):
		return self.multi_meta('playlist/get?', 'tracks_count', id, None)

	def get_artist_meta(self, id):
		return self.multi_meta('artist/get?', 'albums_count', id, None)
	
	def get_favourites(self, type):
		return self.multi_meta('favorite/getUserFavorites?', 'total', None, type)
	
	def test_secret(self, sec):
		try:
			r = self.api_call('userLibrary/getAlbumsList?', sec=sec)
			return True
		except InvalidAppSecretError:
			return False
	
	def cfg_setup(self, delete):
		tmp = '/tmp' if platform.system() == 'Darwin' else tempfile.gettempdir()
		cfg = os.path.join(tmp, 'qopy_cfg.json')
		if delete:
			os.remove(cfg)
		if not os.path.isfile(cfg):
			spoofer = spoofbuz.Spoofer()
			id = spoofer.get_app_id()
			for secret in spoofer.get_app_sec().values():
				if self.test_secret(secret):
					sec = secret
					break
			id_sec={
				"id": id,
				"sec": sec}
			with open(cfg, 'w') as f:
				json.dump(id_sec, f, indent=4)
		with open(cfg) as f:
			cfg_out = json.load(f)
		return cfg_out['id'], cfg_out['sec']

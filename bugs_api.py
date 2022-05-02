from datetime import datetime, timedelta

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry


class BugsApi:
    def __init__(self):
        # device id from the Bugs android app
        self.device_id = None

        # all required session variables
        self.access_token = None
        self.refresh_token = None
        self.expires = None

        self.s = requests.Session()

        retries = Retry(total=10,
                        backoff_factor=0.4,
                        status_forcelist=[429, 500, 502, 503, 504])

        self.s.mount('http://', HTTPAdapter(max_retries=retries))
        self.s.mount('https://', HTTPAdapter(max_retries=retries))

    def headers(self):
        return {
            'User-Agent': 'Mobile|Bugs|5.03.33|Android|12|Pixel 6|Google|market|105033301',
            'Authorization': f'Bearer {self.access_token}' if self.access_token else '',
        }

    def auth(self, username, password):
        r = self.s.post('https://secure.bugs.co.kr/api/5/login', params={
            'capText': '',
            'device_model': 'android',
            'key': '',
            'passwd': password,
            'udid': self.device_id,
            'userid': username,
            'device_id': self.device_id
        }, headers=self.headers())

        r = r.json()
        if r.get('ret_code') == 300:
            raise ConnectionError('Invalid username or password')

        self.access_token = r['result']['token']['access_token']
        self.refresh_token = r['result']['token']['refresh_token']
        self.expires = datetime.now() + timedelta(seconds=r['result']['token']['expires_in'])

    def get_account(self):
        r = self.s.post('https://secure.bugs.co.kr/api/5/right', headers=self.headers(), params={
            'device_model': 'android',
            # 'carrier_name': 'Telekom',
            'device_id': self.device_id
        })

        r = r.json()

        if r.get('ret_code') != 0:
            raise ConnectionError(r.get('ret_msg'))

        return r.get('result')

    def set_session(self, session: dict):
        self.device_id = session.get('device_id')
        self.access_token = session.get('access_token')
        self.refresh_token = session.get('refresh_token')
        self.expires = session.get('expires')

    def get_session(self):
        return {
            'device_id': self.device_id,
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'expires': self.expires
        }

    def _make_call(self, method: str, endpoint: str, params: dict = None, json=None, additional_headers=None):
        valid_methods = {'GET', 'POST'}
        if method not in valid_methods:
            raise ValueError('method: must be one of %r ' % valid_methods)

        # function for API requests
        if not params:
            params = {}

        headers = self.headers()
        if additional_headers:
            headers.update(additional_headers)

        # always add the device id to the params?
        params.update({'device_id': self.device_id})

        if method == 'GET':
            r = self.s.get(f'https://mapi.bugs.co.kr/music/5/{endpoint}', params=params, headers=headers)
        else:
            r = self.s.post(f'https://mapi.bugs.co.kr/music/5/{endpoint}', params=params, json=json, headers=headers)

        if r.status_code not in {200, 201, 202}:
            raise ConnectionError(r.text)

        return r.json()

    def get_artist(self, artist_id: str or int):
        artist_id = int(artist_id)
        return self._make_call('POST', 'multi/invoke/map', json=[{
            "id": "artist",
            "args": {
                "artist_id": artist_id,
                "result_type": "DETAIL"
            }
        }, {
            "id": "artist_image",
            "args": {
                "artist_id": artist_id
            },
        }]).get('list')

    def get_artist_tracks(self, artist_id: str or int, page: int = 1, limit: int = 9999):
        artist_id = int(artist_id)
        return self._make_call('POST', 'multi/invoke/map', json=[{
            "id": "artist_track",
            "args": {
                "artist_id": artist_id,
                "filter": "ALL",
                "page": page,
                "result_type": "LIST",
                "size": limit,
                "sort": "POPULAR"
            }
        }]).get('list')

    def get_artist_albums(self, artist_id: str or int, page: int = 1, limit: int = 9999):
        artist_id = int(artist_id)
        return self._make_call('POST', 'multi/invoke/map', json=[{
            "id": "artist_album_filter_release",
            "args": {
                "artist_id": artist_id,
                "page": page,
                "result_type": "LIST",
                "size": limit,
                "sort": "recent"
            }
        }]).get('list')

    def get_artist_compilation_albums(self, artist_id: str or int, page: int = 1, limit: int = 9999):
        artist_id = int(artist_id)
        return self._make_call('POST', 'multi/invoke/map', json=[{
            "id": "artist_album_filter_joincompil",
            "args": {
                "artist_id": artist_id,
                "page": page,
                "result_type": "LIST",
                "size": limit,
                "sort": "recent"
            }
        }]).get('list')

    def get_artist_videos(self, artist_id: str or int, page: int = 1, limit: int = 9999):
        artist_id = int(artist_id)
        return self._make_call('POST', 'multi/invoke/map', json=[{
            "id": "artist_mv",
            "args": {
                "artist_ids": str(artist_id),
                "filter": "ALL",
                "page": page,
                "result_type": "LIST",
                "size": limit,
                "sort": "recent"
            }
        }]).get('list')

    def get_album(self, album_id: str or int):
        album_id = int(album_id)
        return self._make_call('POST', 'multi/invoke/map', json=[{
            "id": "album",
            "args": {
                "album_id": album_id,
                "result_type": "DETAIL"
            }
        }, {
            "id": "album_artist_role",
            "args": {
                "album_id": album_id

            }
        }, {
            "id": "album_image",
            "args": {
                "album_id": album_id
            }
        }]).get('list')

    def get_album_tracks(self, album_id: str or int):
        album_id = int(album_id)
        return self._make_call('POST', 'multi/invoke/map', json=[{
            "id": "album_track",
            "args": {
                "album_id": album_id,
                "result_type": "LIST"
            }
        }]).get('list')

    def get_track(self, track_id: str or int):
        track_id = int(track_id)
        return self._make_call('POST', 'multi/invoke/map', json=[{
            "id": "track",
            "args": {
                "track_id": track_id,
                "result_type": "DETAIL"
            }
        }, {
            "id": "track_artist_role",
            "args": {
                "track_id": track_id
            }
        }]).get('list')

    def get_lyrics(self, track_id: str or int):
        return self._make_call('GET', f'track/{track_id}/lyrics')

    def get_stream(self, track_id: int, bitrate: str = 'flac'):
        # bitrate is either 'flac24', 'flac', 'aac256', 'aac', '320k'
        valid_bitrate = {'flac24', 'flac', 'aac256', 'aac', '320k'}
        if bitrate not in valid_bitrate:
            raise ValueError('bitrate: must be one of %r ' % valid_bitrate)

        return self._make_call('GET', f'play/track/{track_id}/streaming', params={
            'bitrate': bitrate,
            'wwan': 'N',
            'overwrite_session': 'Y'
        }).get('result')

    def get_search(self, query: str):
        return self._make_call('GET', 'multi/invoke/map', json=[{
            "id": "get_search_combine",
            "args": {
                "query": query
            }
        }]).get('list')

    def get_search_individually(self, query: str, category: str = 'track', page: int = 1, limit: int = 100):
        return self._make_call('GET', f'search/{category}', params={
            'query': query,
            'page': page,
            'size': limit,
            'sort': 'exact',
            'flac_str_only': 'N'
        })

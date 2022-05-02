import logging
import random
import string

from datetime import datetime

from utils.models import *
from .bugs_api import BugsApi

module_information = ModuleInformation(
    service_name='Bugs',
    module_supported_modes=ModuleModes.download | ModuleModes.covers | ModuleModes.lyrics,
    session_settings={'username': '', 'password': ''},
    session_storage_variables=['device_id', 'access_token', 'refresh_token', 'expires'],
    netlocation_constant='bugs',
    test_url='https://music.bugs.co.kr/track/5311931'
)


class ModuleInterface:
    # noinspection PyTypeChecker
    def __init__(self, module_controller: ModuleController):
        self.cover_size = module_controller.orpheus_options.default_cover_options.resolution
        self.exception = module_controller.module_error
        self.oprinter = module_controller.printer_controller
        self.print = module_controller.printer_controller.oprint
        self.module_controller = module_controller

        # LOW = 128kbit/s AAC, MEDIUM = 320kbit/s MP3, HIGH = 320kbit/s AAC, LOSSLESS = 1411kbit/s FLAC
        self.quality_order = ['flac24', 'flac', 'aac256', '320k', 'aac']
        self.quality_parse = {
            QualityEnum.MINIMUM: self.quality_order[4],
            QualityEnum.LOW: self.quality_order[4],
            QualityEnum.MEDIUM: self.quality_order[3],
            QualityEnum.HIGH: self.quality_order[2],
            QualityEnum.LOSSLESS: self.quality_order[1],
            QualityEnum.HIFI: self.quality_order[0]
        }

        self.session = BugsApi()

        # generate device_id and save it in the temporary settings
        device_id = module_controller.temporary_settings_controller.read('device_id')
        if not device_id:
            device_id = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits + '_',
                                               k=28))
            self.module_controller.temporary_settings_controller.set('device_id', device_id)

        session = {
            'device_id': device_id,
            'access_token': module_controller.temporary_settings_controller.read('access_token'),
            'refresh_token': module_controller.temporary_settings_controller.read('refresh_token'),
            'expires': module_controller.temporary_settings_controller.read('expires')
        }

        self.session.set_session(session)

        if session['access_token'] and session['expires'] > datetime.now():
            self.valid_account()

        if session['refresh_token'] and datetime.now() > session['expires']:
            # access token expired, get new refresh token
            self.refresh_token()

    def refresh_token(self):
        logging.debug(f'Bugs: access_token expired, getting a new one')

        # get a new access_token and refresh_token from the API
        # TODO: implement refresh token oauth flow
        # refresh_data = self.session.refresh()

        # save the new access_token, refresh_token and expires in the temporary settings
        self.module_controller.temporary_settings_controller.set('access_token', self.session.access_token)
        self.module_controller.temporary_settings_controller.set('refresh_token', self.session.refresh_token)
        self.module_controller.temporary_settings_controller.set('expires', self.session.expires)
            
    def login(self, email: str, password: str):
        logging.debug(f'Bugs: no session found, login')
        self.session.auth(email, password)

        self.valid_account()

        # save the new access_token, refresh_token and expires in the temporary settings
        self.module_controller.temporary_settings_controller.set('access_token', self.session.access_token)
        self.module_controller.temporary_settings_controller.set('refresh_token', self.session.refresh_token)
        self.module_controller.temporary_settings_controller.set('expires', self.session.expires)

    def valid_account(self):
        # get the subscription from the API and check if it's at least a "VIP" subscription
        account_data = self.session.get_account()
        if account_data and account_data.get('member_level').get('level') != 'VIP':
            raise self.exception('You need a VIP account to use this module')

    @staticmethod
    def _generate_artwork_url(cover_path: str, size: int, max_size=3000):
        # not the best idea, but it rounds the self.cover_size to the nearest number in supported_sizes, 3001 is needed
        # for the "uncompressed" cover
        supported_sizes = [75, 140, 200, 350, 500, 1000, 1280, 1400, 2000, 3001]
        best_size = min(supported_sizes, key=lambda x: abs(x - size))
        # return "uncompressed" cover if self.cover_resolution > max_size
        cover_size = best_size if best_size <= max_size else 'original'
        return f'https://image.bugsm.co.kr/album/images/{cover_size}{cover_path}'

    def search(self, query_type: DownloadTypeEnum, query: str, track_info: TrackInfo = None, limit: int = 20):
        if query_type is DownloadTypeEnum.playlist:
            raise self.exception(f'Query type "{query_type.name}" is not supported!')

        results = self.session.get_search(query)[0].get('get_search_combine').get('result')

        items = []
        for i in results.get(query_type.name).get('list'):
            additional = []
            if query_type is DownloadTypeEnum.track:
                name = i.get('track_title')
                result_id = i.get('track_id')

                artists = [a.get('artist_nm') for a in i.get('artists')]
                year = i.get('album').get('release_ymd')[:4] if i.get('album').get('release_ymd') else None

                additional.append('LOSSLESS') if i.get('rights').get('download_flac').get('service_flac_yn') else None
            elif query_type is DownloadTypeEnum.album:
                name = i.get('title')
                result_id = i.get('album_id')

                artists = [j.get('artist_nm') for j in i.get('artists')]
                year = i.get('release_ymd')[:4] if i.get('release_ymd') else None
            elif query_type is DownloadTypeEnum.artist:
                name = i.get('artist_nm')
                result_id = i.get('artist_id')

                artists = None
                year = None
            else:
                raise self.exception(f'Query type "{query_type.name}" is not supported!')

            item = SearchResult(
                name=name,
                artists=artists,
                year=year,
                result_id=result_id,
                additional=additional if additional != [] else None,
                extra_kwargs={'data': {i.get('id'): i}}
            )

            items.append(item)

        return items

    def get_playlist_info(self, playlist_id: str):
        self.exception(f'Bugs does not support playlists?')

    def get_artist_info(self, artist_id: str, get_credited_albums: bool, data=None) -> ArtistInfo:
        artist_data = self.session.get_artist(artist_id)
        # get the "artist" and "artist_image" data from the multi-call request, artist is always 0 and artist_image 1
        artist_info = artist_data[0].get('artist').get('result')
        # TODO: download all artist pictures?
        artist_images = artist_data[1].get('artist_image').get('list')

        # get all the artist tracks
        artist_tracks_data = self.session.get_artist_tracks(artist_id)
        artist_tracks = artist_tracks_data[0].get('artist_track').get('list')

        # get all the artist albums
        artist_albums_data = self.session.get_artist_albums(artist_id)
        artist_albums = artist_albums_data[0].get('artist_album_filter_release').get('list')

        # get all the compilation albums
        if get_credited_albums:
            artist_compilations_data = self.session.get_artist_compilation_albums(artist_id)
            artist_albums += artist_compilations_data[0].get('artist_album_filter_joincompil').get('list')

        return ArtistInfo(
            name=artist_info.get('artist_nm'),
            tracks=[t.get('track_id') for t in artist_tracks],
            track_extra_kwargs={'data': {t.get('track_id'): t for t in artist_tracks}},
            albums=[a.get('album_id') for a in artist_albums],
            album_extra_kwargs={'data': {a.get('album_id'): a for a in artist_albums}},
        )

    def get_album_info(self, album_id: str, data=None) -> AlbumInfo:
        # check if album is already in album cache, add it
        if data is None:
            data = {}

        # always get the album data from the API, because the cache is missing a lot of tags
        album_data = self.session.get_album(album_id)
        album_info = album_data[0].get('album').get('result')

        tracks_data = self.session.get_album_tracks(album_id)
        tracks = tracks_data[0].get('album_track').get('list')

        # add all the tracks and album to the cache
        cache = {'data': {track.get('track_id'): track for track in tracks}}
        cache['data'].update({album_id: album_info})

        return AlbumInfo(
            name=album_info.get('title'),
            release_year=album_info.get('release_ymd')[:4] if album_info.get('release_ymd') else None,
            cover_url=self._generate_artwork_url(album_info.get('image').get('path'), size=self.cover_size),
            artist=album_info.get('artists')[0].get('artist_nm'),
            artist_id=album_info.get('artists')[0].get('artist_id'),
            tracks=[t.get('track_id') for t in tracks],
            track_extra_kwargs=cache
        )

    def get_track_info(self, track_id: int, quality_tier: QualityEnum, codec_options: CodecOptions,
                       data=None) -> TrackInfo:
        if data is None:
            data = {}

        track_data = data[track_id] if track_id in data else self.session.get_track(
            track_id)[0].get('track').get('result')

        album_id = track_data.get('album').get('album_id')
        album_data = data[album_id] if album_id in data else self.session.get_album(
            album_id)[0].get('album').get('result')

        release_year = album_data.get('release_ymd')[:4] if album_data.get('release_ymd') else None

        release_date = album_data.get('release_ymd') if album_data.get('release_ymd') else None
        # add a day if the day is missing from the YYYYMM date
        if len(release_date) == 6:
            release_date += '01'
        release_date = datetime.strptime(release_date, '%Y%m%d').strftime('%Y-%m-%d')

        tags = Tags(
            album_artist=album_data.get('artists')[0].get('artist_nm'),
            track_number=track_data.get('track_no'),
            total_tracks=album_data.get('track_count'),
            disc_number=track_data.get('disc_no'),
            total_discs=album_data.get('disc_count'),
            genres=[genre.get('svc_nm') for genre in album_data.get('genres')] if album_data.get('genres') else None,
            release_date=release_date,
            copyright=f'© {release_year} {album_data.get("labels")[0].get("label_nm")}',
            replay_gain=track_data.get('track_gain'),
        )

        error = None
        if not track_data.get('rights').get('streaming').get('service_yn'):
            error = f'Track "{track_data.get("track_title")}" is not streamable!'

        # set default highest_quality to lowest (aac)
        highest_quality = self.quality_order[-1]
        # iterate over the quality order and check if the track is available in that quality
        for i in range(self.quality_order.index(self.quality_parse[quality_tier]), len(self.quality_order)):
            quality = self.quality_order[i]
            # if the track is available in that quality, set it as the highest quality and break
            if quality in track_data.get('bitrates'):
                highest_quality = quality
                break

        # get the bitrate based on the highest quality, why has aac256 not 256kbit/s?!
        bitrate = {
            'flac24': 2116,
            'flac': 1411,
            'aac256': 320,
            '320k': 320,
            'aac': 128,
        }[highest_quality]

        # get the codec based on the highest quality
        codec = {
            'flac24': CodecEnum.FLAC,
            'flac': CodecEnum.FLAC,
            'aac256': CodecEnum.AAC,
            '320k': CodecEnum.MP3,
            'aac': CodecEnum.AAC,
        }[highest_quality]

        # https://en.wikipedia.org/wiki/Audio_bit_depth#cite_ref-1
        bit_depth = {
            'flac24': 24,
            'flac': 16
        }.get(highest_quality, None)

        track_info = TrackInfo(
            name=track_data.get('track_title'),
            album=album_data.get('title'),
            album_id=album_data.get('album_id'),
            artists=[a.get('artist_nm') for a in track_data.get('artists')],
            artist_id=track_data.get('artists')[0].get('artist_id'),
            release_year=release_year,
            bitrate=bitrate,
            sample_rate=44.1,
            bit_depth=bit_depth,
            cover_url=self._generate_artwork_url(album_data.get('image').get('path'), size=self.cover_size),
            tags=tags,
            codec=codec,
            download_extra_kwargs={'track_id': track_id, 'quality_tier': highest_quality},
            error=error
        )

        return track_info

    def get_track_download(self, track_id: str or int, quality_tier: str) -> TrackDownloadInfo:
        stream_data = self.session.get_stream(track_id, quality_tier)
        if stream_data.get('state') != 'OK':
            raise Exception('Requested quality tier is currently not available, try again later')

        return TrackDownloadInfo(download_type=DownloadEnum.URL, file_url=stream_data.get('url'))

    def get_track_lyrics(self, track_id: str or int) -> LyricsInfo:
        # get lyrics data for current track id
        lyrics_data = self.session.get_lyrics(track_id)

        embedded, synced = None, None
        if lyrics_data.get('result'):
            if 'time' in lyrics_data.get('result'):
                # only synced lyrics are available
                lyrics = lyrics_data.get('result').get('time')
                # get the synced lyrics in the right lrc format
                lyrics = lyrics.replace("＃", "\n")
                # split the lyrics by line and | into a list of [<time>, <line>]
                lines_split = [line.split('|') for line in lyrics.splitlines()]
                # finally, create the lrc string
                synced = "\n".join(
                    f'[{datetime.fromtimestamp(float(time)).strftime("%M:%S.%f")[0:-4]}]{line}'
                    for time, line in lines_split)

                # convert the synced lyrics to normal lyrics
                embedded = "\n".join(f'{line}' for time_stamp, line in lines_split)
            elif 'normal' in lyrics_data.get('result'):
                # only embedded lyrics are available
                embedded = lyrics_data.get('result').get('normal')

        return LyricsInfo(
            embedded=embedded,
            synced=synced
        )

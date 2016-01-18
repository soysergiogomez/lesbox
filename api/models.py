__author__ = 'agusx1211'

from operator import attrgetter
import random
import datetime
from django.db import models
import json
import time
import requests

ACCOUNT_FREE = 'f'
ACCOUNT_PREMIUM = 'p'
ACCOUNT_TYPE = (
    (ACCOUNT_FREE, 'Free'),
    (ACCOUNT_PREMIUM, 'Premium'),
)


class User(models.Model):
    
    ACCOUNT_FREE = ACCOUNT_FREE
    ACCOUNT_PREMIUM = ACCOUNT_PREMIUM
    
    username = models.CharField(max_length=60)
    spotify_id = models.CharField(max_length=60, primary_key=True)
    email = models.CharField(max_length=255)
    token_spotify = models.CharField(max_length=255)
    expire_token_spotify = models.IntegerField()
    account_type = models.CharField(max_length=1, choices=ACCOUNT_TYPE)

    def __str__(self):
        return self.spotifyId

    @staticmethod
    def check_token_spotify(token_spotify, spotify_id):
        """Return True if the token is valid for Spotify server."""
        auth_header = 'Bearer %s' % token_spotify
        res = requests.get('https://api.spotify.com/v1/me',
                           HTTP_AUTHORIZATION=auth_header)
        if res.status_code == 200:
            spotify_data = json.loads(res.content)
            return spotify_data["id"] == spotify_id
        else:
            return False

    def join_party(self, party):
        party.users.add(self)

    def left_party(self, party):
        party.users.remove(self)

    def is_authenticated(self, access_token):
        return (self.expire_token_spotify > int(time.time())) and \
            (access_token == self.token_spotify)

    def get_current_luck(self):
        """Devuelve un valor al azar, que sera usado para calcular
        el orden en el que son reproducidas las canciones en la Party"""
        random.seed(self.email + datetime.datetime.now().strftime("%Y-%m-%d"))
        return random.randint(0, 9223372036854775806)


class Party(models.Model):
    id = models.AutoField(primary_key=True)

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owner')
    name = models.CharField(max_length=255)
    members = models.ManyToManyField(User, related_name='members')

    current_user = models.ForeignKey(User, related_name='current_user')

    def __str__(self):
        return self.name

    @classmethod
    def create_party(cls, _owner, _name):
        p = cls(owner=_owner, name=_name)
        return p

    def get_members_in_order(self):
        return sorted(self.members.all(), key=attrgetter('get_current_luck'))

    def get_next_track(self):
        all_checked = False
        loop_count = 0

        while not all_checked:
            current_user = self.get_next_user()
            next_user_tracks = Track.get_all_tracks_sorted(self, current_user)

            if loop_count > len(self.get_members_in_order()):
                all_checked = True

            if len(next_user_tracks) > 0:
                next_track = next_user_tracks[0]
                next_track.played = True
                next_track.save()
                return next_track
            else:
                loop_count += 1

        return None

    def get_next_user(self):
        if self.current_user is not None:
            if len(self.get_members_in_order()) < self.get_members_in_order().index(self.current_user) - 1:
                return self.get_members_in_order()[self.get_members_in_order().index(self.current_user) - 1]
            else:
                return self.get_members_in_order()[0]
        else:
            return self.get_members_in_order()[0]


class Track(models.Model):
    id = models.AutoField(primary_key=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user')
    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name='party')

    spotify_track_id = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    duration_ms = models.IntegerField()
    explicit = models.BooleanField()
    preview_url = models.CharField(max_length=255)
    href = models.CharField(max_length=255)
    popularity = models.IntegerField()
    uri = models.CharField(max_length=255)

    played = models.BooleanField()

    priority = models.IntegerField()

    def __str__(self):
        return self.name

    def get_party_id(self):
        return self.party.id

    def get_user_id(self):
        return self.user.spotifyId

    @classmethod
    def create_track(cls, user, party, spotify_track_id, name, duration_ms,
                     explicit, preview_url, href, popularity, uri, priority):
        track = cls(
            user=user,
            party=party,
            spotify_track_id=spotify_track_id,
            name=name,
            duration_ms=duration_ms,
            explicit=explicit,
            review_url=preview_url,
            href=href,
            popularity=popularity,
            priority=priority,
            uri=uri,
            played=False
        )
        
        return track

    @staticmethod
    def get_all_tracks(party, user):
        return Track.objects.filter(party=party, user=user, played=False)

    @staticmethod
    def get_all_tracks_sorted(party, user):
        return sorted(Track.get_all_tracks(party, user), key=attrgetter('priority'))

    @staticmethod
    def del_all_tracks(party, user):
        Track.get_all_tracks(party, user).delete()

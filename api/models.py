from __future__ import unicode_literals
import httplib
from operator import attrgetter
import random
import datetime
from django.db import models
import json
import time

__author__ = 'agusx1211'


class User(models.Model):
    userName = models.CharField(max_length=60)
    spotifyId = models.CharField(max_length=60, primary_key=True)
    email = models.CharField(max_length=255)

    lastTokenSpotify = models.CharField(max_length=255)
    expireDateTokenSpotify = models.IntegerField()

    ACCOUNT_TYPE = (
        ('f', 'Free'),
        ('p', 'Premium'),
    )
    account_type = models.CharField(max_length=1, choices=ACCOUNT_TYPE)

    def __str__(self):
        return self.spotifyId

    def check_token_spotify(self):
        """Returns is the token is valid for Spotify server."""
        import urllib2
        req = urllib2.Request('https://api.spotify.com/v1/me')
        req.add_header('Authorization', 'Bearer ' + self.lastTokenSpotify)

        try:
            resp = urllib2.urlopen(req)
        except urllib2.HTTPError, e:
            return False
        except urllib2.URLError, e:
            return False
        except httplib.HTTPException, e:
            return False
        except Exception:
            return False

        content = resp.read()

        spotify_data = json.loads(content)
        return spotify_data["id"] == self.spotifyId

    def join_party(self, party):
        party.users.add(self)

    def left_party(self, party):
        party.users.remove(self)

    def is_authenticated(self, access_token):
        return (self.expireDateTokenSpotify > int(time.time())) and (access_token == self.lastTokenSpotify)

    def get_current_luck(self):
        """Devuelve un valor al azar, que sea usado para calcular
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

    @staticmethod
    def create_party(_owner, _name):
        p = Party(owner=_owner, name=_name)
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

    @staticmethod
    def create_track(_user, _party, _spotify_track_id, _name, _duration_ms, _explicit, _preview_url, _href, _popularity,
                     _uri,
                     _priority):
        t = Track()

        t.user = _user
        t.party = _party
        t.spotify_track_id = _spotify_track_id
        t.name = _name
        t.duration_ms = _duration_ms
        t.explicit = _explicit
        t.review_url = _preview_url
        t.href = _href
        t.popularity = _popularity
        t.priority = _priority
        t.uri = _uri
        t.played = False

        return t

    @staticmethod
    def get_all_tracks(party, user):
        return Track.objects.filter(party=party, user=user, played=False)

    @staticmethod
    def get_all_tracks_sorted(party, user):
        return sorted(Track.get_all_tracks(party, user), key=attrgetter('priority'))

    @staticmethod
    def del_all_tracks(party, user):
        Track.get_all_tracks(party, user).delete()

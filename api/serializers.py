from rest_framework import serializers
from api.models import User, Party, Track

__author__ = 'agusx1211'


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('userName', 'spotifyId', 'email', 'lastTokenSpotify', 'account_type')


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('userName', 'spotifyId', 'email', 'account_type')


class PartySerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    members = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Party
        fields = ('id', 'owner', 'name', 'members')

class TrackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Track
        fields = ('id', 'user', 'get_party_id', 'spotify_track_id', 'name', 'duration_ms', 'explicit', 'preview_url', 'href', 'popularity', 'uri', 'priority')

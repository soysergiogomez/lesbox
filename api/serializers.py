__author__ = 'agusx1211'

from rest_framework import serializers

from api.models import User, Party, Track


class ErrorSerializer(serializers.Serializer):
    status_code = serializers.IntegerField()
    errors = serializers.DictField(child=serializers.CharField())
    message = serializers.CharField(max_length=255, required=False)


class SpotifyUserSerializer(serializers.ModelSerializer):
    
    def validate(self, data):
        """Validate spotify user with server."""
        spotify_id = data.get('spotify_id')
        username = data.get('username')
        token_spotify = data.get('token_spotify')
        account_type = data.get('account_type')
        
        user, created = User.objects.get_or_create(spotify_id=spotify_id)
        
        if User.check_token_spotify(token_spotify, spotify_id):
            user.username = username
            user.token_spotify = token_spotify
            user.account_type = account_type
            user.save()
        else:
            raise serializers.ValidationError('Invalid spotify token')
        
        return data
    
    class Meta:
        model = User
        fields = ('username', 'spotify_id', 'email', 'token_spotify',
            'account_type')


class PartySerializer(serializers.ModelSerializer):
    owner = SpotifyUserSerializer(read_only=True)
    members = SpotifyUserSerializer(many=True, read_only=True)

    class Meta:
        model = Party
        fields = ('id', 'owner', 'name', 'members')


class TrackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Track
        fields = ('id', 'user', 'get_party_id', 'spotify_track_id', 'name',
            'duration_ms', 'explicit', 'preview_url', 'href', 'popularity',
            'uri', 'priority')

import json

from django.core import serializers
from django.http import HttpResponse

from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.decorators import api_view

from api.models import User, Party, Track
from api.serializers import (SpotifyUserSerializer, PartySerializer,
    TrackSerializer, ErrorSerializer)


class DataMixin(object):
    """ Mixin to parse data from body. """
    
    def get_data(self, request):        
        if "application/json" in request.META['CONTENT_TYPE']:
            try:
                data = json.loads(request.body)
            except ValueError:
                return Response(ErrorSerializer({
                    'status_code': 400,
                    'errors': {'JSON': 'decoding error'},
                    'message': 'JSON decoding error.'
                }).data, status=status.HTTP_400_BAD_REQUEST)
        else:
            data = request.POST
        
        return data


@api_view(('GET', ))
def index(request):
    return Response({'Hello, world': "You're at the api index."})


class SpotifyLoginView(APIView, DataMixin):
    """Sign in a user with spotify."""
    permission_classes = [
        AllowAny,
    ]
    serializer_class = SpotifyUserSerializer
    
    def post(self, request, *args, **kwargs):
        data = self.get_data(request)
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(ErrorSerializer({
                'status_code': 400,
                'errors': serializer.errors,
                'message': 'Invalid data'
            }).data, status=status.HTTP_400_BAD_REQUEST)


def create_party(request):
    try:
        token = request.META["HTTP_AUTHENTICATION"]

        received_json_data = json.loads(request.body)
        owner = User.objects.get(spotifyId=received_json_data['userId'])
        party_name = received_json_data['partyName']
    except ValueError:
        return HttpResponse("Inavlid Json", status=400)

    if owner.is_authenticated(token):
        return HttpResponse("No authenticated", status=403)

    party = Party.create_party(owner, party_name)
    party.save()

    party.members.add(owner)
    party.save()

    serializer = PartySerializer(party, many=False)
    return JSONResponse(serializer.data, status=201)


def set_tracks(request):
    try:
        token = request.META["HTTP_AUTHENTICATION"]

        received_json_data = json.loads(request.body)
        received_json_tracks = received_json_data['tracks']
        owner = User.objects.get(spotifyId=received_json_data['userId'])
        party = Party.objects.get(id=received_json_data['partyId'])
    except ValueError:
        return HttpResponse("Inavlid Json", status=400)

    if owner.is_authenticated(token):
        return HttpResponse("No authenticated", status=403)

    for _track in received_json_tracks:
        try:
            "If track exist update priority"
            track = Track.objects.get(id=_track["id"])
            track.priority = _track["priority"]
            track.save()
        except KeyError:
            "If not exist create a new track"
            track = Track.create_track(owner, party, _track["spotify_track_id"], _track["name"], _track["duration_ms"],
                                       _track["explicit"], _track["preview_url"], _track["href"], _track["popularity"],
                                       _track["uri"], _track["priority"])
            track.save()

    return return_all_tracks(party, owner)


def get_tracks(request):
    try:
        token = request.META["HTTP_AUTHENTICATION"]

        received_json_data = json.loads(request.body)
        owner = User.objects.get(spotifyId=received_json_data['userId'])
        party = Party.objects.get(id=received_json_data['partyId'])
    except ValueError:
        return HttpResponse("Inavlid Json", status=400)

    if owner.is_authenticated(token):
        return HttpResponse("No authenticated", status=403)

    return return_all_tracks(party, owner)


def del_all_tracks(request):
    try:
        token = request.META["HTTP_AUTHENTICATION"]

        received_json_data = json.loads(request.body)
        owner = User.objects.get(spotifyId=received_json_data['userId'])
        party = Party.objects.get(id=received_json_data['partyId'])
    except ValueError:
        return HttpResponse("Inavlid Json", status=400)

    if owner.is_authenticated(token):
        return HttpResponse("No authenticated", status=403)

    Track.del_all_tracks(party, owner)
    return return_all_tracks(party, owner)


def del_one(request):
    try:
        token = request.META["HTTP_AUTHENTICATION"]

        received_json_data = json.loads(request.body)
        owner = User.objects.get(spotifyId=received_json_data['userId'])
        party = Party.objects.get(id=received_json_data['partyId'])
        track = Track.objects.get(user=owner, party=party)
    except ValueError:
        return HttpResponse("Inavlid request", status=400)

    if owner.is_authenticated(token):
        return HttpResponse("No authenticated", status=403)

    track.delete()
    return return_all_tracks(party, owner)


def return_all_tracks(party, owner):
    tracks = Track.get_all_tracks(party, owner)
    serializer = TrackSerializer(tracks, many=True)
    return JSONResponse(serializer.data, status=200)

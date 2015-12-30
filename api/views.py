import json
from django.core import serializers
from django.http import HttpResponse
from rest_framework.renderers import JSONRenderer
from api.models import User, Party, Track
from django.views.decorators.csrf import csrf_exempt
from api.serializers import AccountSerializer, PartySerializer, TrackSerializer


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")


class JSONResponse(HttpResponse):
    """
    An HttpResponse that renders its content into JSON.
    """

    def __init__(self, data, **kwargs):
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)


@csrf_exempt
def login(request):
    try:
        received_json_data = json.loads(request.body)
        u = User(spotifyId=received_json_data['spotifyId'])
        u.account_type = received_json_data['account_type']
        u.userName = received_json_data["username"]
    except ValueError:
        return HttpResponse("Inavlid Json", status=403)

    if u.lastTokenSpotify != received_json_data["spotifyToken"]:
        u.lastTokenSpotify = received_json_data["spotifyToken"]
        if u.check_token_spotify():
            u.save()
            serializer = AccountSerializer(u, many=False)
            return JSONResponse(serializer.data)

    return HttpResponse("Spotify user not valid", status=400)


@csrf_exempt
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


@csrf_exempt
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


@csrf_exempt
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

@csrf_exempt
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


@csrf_exempt
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
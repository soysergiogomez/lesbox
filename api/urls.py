__author__ = 'agusx1211'
from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^user/login/', views.SpotifyLoginView.as_view(), name='create_user'),
    url(r'^party/create/', views.create_party, name='create_party'),
    url(r'^party/tracks/set', views.set_tracks, name='set_tracks'),
    url(r'^party/tracks/get', views.get_tracks, name='get_tracks'),
    url(r'^party/tracks/del', views.del_all_tracks, name='get_tracks'),
    url(r'^party/track/del/one', views.del_one, name='get_tracks'),

]
from django.urls import path

from rest_views import sync_views

urlpatterns = [
    path("api/v1/sync/<str:ats_source>/status", sync_views.status),
    path("api/v1/sync/<str:ats_source>", sync_views.sync),
]

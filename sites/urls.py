from django.urls import path
from sites.views import create_site, my_sites_view
#
urlpatterns = [
    path('create_site/', create_site, name='create_site'),
    path('my_sites/', my_sites_view, name='my_sites')
]

app_name = "sites"

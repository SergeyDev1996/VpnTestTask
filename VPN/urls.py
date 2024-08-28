from django.urls import path, re_path

from VPN.views import proxy_view

urlpatterns = [
    re_path(r'^(?P<site_name>[^/]+)(?P<path>.*)$', proxy_view, name='proxy_view')
]

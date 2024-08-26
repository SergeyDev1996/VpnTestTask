from django.urls import path

from VPN.views import proxy_view

urlpatterns = [
    path('<str:site_name>/', proxy_view, name='proxy_view'),]

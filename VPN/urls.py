from django.urls import path

from VPN.views import proxy_view, static_files_proxy_view

urlpatterns = [
    path('static_files_proxy/<str:site_name>/',
         static_files_proxy_view, name='static_files_proxy'),
    path('static_files_proxy/<str:site_name>/<path:resource_path>',
         static_files_proxy_view, name='static_files_proxy_with_path'),
    path('<str:site_name>/', proxy_view, name='proxy_view'),
    path('<str:site_name>/<path:path>',
         proxy_view, name='proxy_view_with_path'),
]

app_name = "VPN"

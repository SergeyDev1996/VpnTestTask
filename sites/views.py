import requests
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from urllib.parse import urljoin, urlparse

from django.urls import reverse_lazy

from .forms import SiteForm
from .models import Site
from django.contrib.auth.decorators import login_required
from bs4 import BeautifulSoup


@login_required
def create_site(request):
    if request.method == 'POST':
        form = SiteForm(request.POST)
        if form.is_valid():
            new_site = form.save(commit=False)
            new_site.user = request.user
            new_site.save()
            return HttpResponseRedirect(reverse_lazy("sites:my_sites"))
    else:
        form = SiteForm()
    return render(request, "sites/create_site.html", {'form': form})


@login_required
def my_proxy_view(request, site_name, link=''):
    try:
        user_site = Site.objects.get(name=site_name, user=request.user)
    except Site.DoesNotExist:
        return render(request, 'sites/site_not_exist.html')
    if link:
        parsed_link = urlparse(link)
        if parsed_link.scheme:
            site_url = link
        else:
            site_url = urljoin(user_site.url, link.lstrip('/'))
    else:
        site_url = user_site.url
    try:
        response = requests.get(site_url)
        response.raise_for_status()
    except requests.RequestException as e:
        return HttpResponse(f"An error occurred when trying "
                            f"to reach the site: {e}", status=502)
    content_type = response.headers.get('Content-Type', '')
    if 'text/html' in content_type:
        soup = BeautifulSoup(response.content, 'html.parser')
        current_site_domain = urlparse(site_url).netloc
        for anchor in soup.find_all('a', href=True):
            href = anchor['href']
            parsed_href = urlparse(href)
            if parsed_href.netloc and \
                    parsed_href.netloc != current_site_domain:
                continue
            else:
                relative_path = href.replace(parsed_href.scheme +
                                             '://' + parsed_href.netloc,
                                             '', 1).lstrip('/')
                new_href = request.build_absolute_uri(f'/{site_name}/'
                                                      f'{relative_path}')
                anchor['href'] = new_href
        return HttpResponse(str(soup), content_type='text/html')
    return HttpResponse(response.content, content_type=content_type)


@login_required
def my_sites_view(request):
    sites = Site.objects.filter(user=request.user)
    return render(request, 'sites/my_sites.html', {'sites': sites})
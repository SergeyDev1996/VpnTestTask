from django.http import HttpResponseRedirect
from django.shortcuts import render

from django.urls import reverse_lazy

from .forms import SiteForm
from .models import Site
from django.contrib.auth.decorators import login_required


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
def my_sites_view(request):
    sites = Site.objects.filter(user=request.user)
    for site in sites:
        site.total_megabytes = round(
            site.total_bytes / 1048576, 2
        )  # Convert bytes to MB
    return render(request, 'sites/my_sites.html', {'sites': sites})

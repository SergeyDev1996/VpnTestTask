from django import forms
from django.core.exceptions import ValidationError
from .models import Site


class SiteForm(forms.ModelForm):
    class Meta:
        model = Site
        fields = ['name', 'url']

    def clean_name(self):
        name = self.cleaned_data['name']
        # Add your validation logic for 'name' field
        if not name.isalnum():
            raise ValidationError('Invalid site name.'
                                  ' Please use only alphanumeric characters.')
        return name

    def clean_url(self):
        url = self.cleaned_data['url']
        # Add your validation logic for 'url' field
        if "http://" not in url and "https://" not in url:
            raise ValidationError('Invalid URL. Please include '
                                  '"http://" or "https://" in your URL.')
        return url

    def clean(self):
        # Use this method for any validation that involves multiple fields
        cleaned_data = super().clean()
        # For example, ensure that the site name is not already in use
        name = cleaned_data.get("name")
        url = cleaned_data.get("url")

        if Site.objects.filter(name=name, url=url).exists():
            raise ValidationError("A site with this "
                                  "name and URL already exists.")
        return cleaned_data

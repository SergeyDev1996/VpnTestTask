from django.db import models
from django.conf import settings


class Site(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    total_bytes = models.BigIntegerField(default=0)
    transitions_count = models.IntegerField(default=0)
    name = models.CharField(max_length=100)
    url = models.URLField()

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('user', 'name')
        # This ensures that each user can only have one unique name for a site

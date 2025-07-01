from django.db import models
from auth_app.models import Usuario


# Fonte da noticia
class Source(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

# Noticias
class News(models.Model):
    title = models.CharField(max_length=200, blank=False)
    link = models.CharField(blank=False)
    pubDate = models.DateField()
    description = models.CharField(blank=True)
    content = models.CharField(blank=False)
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
    link = models.CharField(max_length=500, blank=False)
    pubDate = models.DateField()
    description = models.CharField(max_length=800, blank=True)
    content = models.CharField(max_length=1500, blank=False)

class Dashboard(models.Model):
    pass
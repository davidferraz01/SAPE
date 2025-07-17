from django.db import models
from auth_app.models import Usuario


# Fonte da noticia
class Source(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

# Noticias
class News(models.Model):
    id = models.AutoField(primary_key=True)
    image = models.ImageField(upload_to='noticias_imagens/', blank=True, null=True)
    title = models.CharField(max_length=500)
    link = models.URLField(unique=True)
    pub_date = models.CharField(max_length=100)
    description = models.TextField()
    content = models.TextField(blank=True, null=True)
    source = models.CharField(max_length=50)  # ex: "G1", "UOL", "EBSERH"

    def __str__(self):
        return self.title

class Dashboard(models.Model):
    pass
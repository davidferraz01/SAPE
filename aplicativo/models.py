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
    title = models.CharField(max_length=500)
    link = models.URLField(unique=True)
    pub_date = models.DateField()
    description = models.TextField()
    content = models.TextField(blank=True, null=True)
    source = models.CharField(max_length=50)  # ex: "G1", "UOL", "EBSERH"
    important_words = models.TextField(blank=True, null=True)
    classification = models.JSONField(null=True, blank=True)

    def __str__(self):
        return self.title

# Dashboard
class Dashboard(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
    oe_count = models.JSONField(default=list, blank=True)
    initial_date = models.DateField()
    final_date = models.DateField()
    oe_news_map = models.JSONField(default=dict, blank=True)
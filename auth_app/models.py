from django.contrib.auth.models import AbstractUser
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from SAPE.roles import AnalistaRole, SupervisorRole
from django.contrib.auth.models import AbstractUser
from rolepermissions.roles import assign_role

class Usuario(AbstractUser):
    ANALISTA = "analista"
    SUPERVISOR = "supervisor"

    TIPOS_USUARIO = [
        (ANALISTA, "Analista"),
        (SUPERVISOR, "Supervisor"),
    ]

    email = models.EmailField(unique=True)
    nome = models.CharField(max_length=100, blank=True, null=True)
    tipo_usuario = models.CharField(max_length=11, choices=TIPOS_USUARIO)
    cpf = models.CharField(max_length=14, unique=True, blank=True, null=True)
    telefone = models.CharField(max_length=16)
    foto = models.ImageField(upload_to='usuarios/', blank=True, null=True)
    #team = models.CharField(max_length=100, blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["tipo_usuario"]

    def __str__(self):
        return f"{self.email} ({self.tipo_usuario})"

@receiver(post_save, sender=Usuario)
def assign_user_role(sender, instance, created, **kwargs):
    if created:  # Se o usuário foi recém-criado
        if instance.tipo_usuario == Usuario.ANALISTA:
            assign_role(instance, AnalistaRole)  # Atribui a role de Analista corretamente
        elif instance.tipo_usuario == Usuario.SUPERVISOR:
            assign_role(instance, SupervisorRole)  # Atribui a role de Supervisor corretamente

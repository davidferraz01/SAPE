from django.contrib.auth.models import AbstractUser
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from SAPE.roles import DoadorRole, InstituicaoRole
from django.contrib.auth.models import AbstractUser
from rolepermissions.roles import assign_role

class Usuario(AbstractUser):
    DOADOR = "doador"
    INSTITUICAO = "instituicao"

    TIPOS_USUARIO = [
        (DOADOR, "Doador"),
        (INSTITUICAO, "Instituição"),
    ]

    email = models.EmailField(unique=True)
    cpf = models.CharField(max_length=14, unique=True, blank=True, null=True)
    cnpj = models.CharField(max_length=30, unique=True, blank=True, null=True)
    nome_responsavel = models.CharField(max_length=100, blank=True, null=True)
    cpf_responsavel = models.CharField(max_length=14, blank=True, null=True)
    tipo_usuario = models.CharField(max_length=11, choices=TIPOS_USUARIO)
    telefone = models.CharField(max_length=16)
    foto = models.ImageField(upload_to='usuarios/', blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["tipo_usuario"]

    def __str__(self):
        return f"{self.email} ({self.tipo_usuario})"


@receiver(post_save, sender=Usuario)
def assign_user_role(sender, instance, created, **kwargs):
    if created:  # Se o usuário foi recém-criado
        if instance.tipo_usuario == Usuario.DOADOR:
            assign_role(instance, DoadorRole)  # Atribui a role de Doador corretamente
        elif instance.tipo_usuario == Usuario.INSTITUICAO:
            assign_role(instance, InstituicaoRole)  # Atribui a role de Instituição corretamente




from django.contrib import admin
from auth_app.models import Usuario
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission

class UsuarioAdmin(UserAdmin):
    # Personalize a exibição dos campos do usuário, se necessário
    list_display = ('username', 'email', 'telefone', 'foto')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informações pessoais', {'fields': ('first_name', 'last_name', 'email', 'telefone', 'foto')}),
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser', 'user_permissions')}),
        ('Datas importantes', {'fields': ('last_login', 'date_joined')}),
    )

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name == 'user_permissions':
            kwargs['queryset'] = Permission.objects.filter(content_type__app_label='auth_app')
        return super().formfield_for_manytomany(db_field, request, **kwargs)
        

admin.site.unregister(Group)
admin.site.register(Usuario, UsuarioAdmin)
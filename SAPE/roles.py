from rolepermissions.roles import AbstractUserRole

class DoadorRole(AbstractUserRole):
    role_name = "doador"  # Define o nome correto da role
    available_permissions = {
        'doador': True,
    }

class InstituicaoRole(AbstractUserRole):
    role_name = "instituicao"  # Define o nome correto da role
    available_permissions = {
        'instituicao': True,
    }

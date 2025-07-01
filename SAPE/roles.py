from rolepermissions.roles import AbstractUserRole

class AnalistaRole(AbstractUserRole):
    role_name = "analista"  # Define o nome correto da role
    available_permissions = {
        'analista': True,
    }

class SupervisorRole(AbstractUserRole):
    role_name = "supervisor"  # Define o nome correto da role
    available_permissions = {
        'supervisor': True,
    }

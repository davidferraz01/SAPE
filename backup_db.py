import os
import json
from datetime import datetime
import django
from django.core.management import call_command
from django.apps import apps

# Configurações do Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SAPE.settings.dev")
django.setup()

# Data atual
date = datetime.now().strftime('%d-%m-%Y_%H-%M-%S')

# Define caminho do backup
backup_path = f"C:\SAPE\SAPE_backups\{date}"

# Cria diretório do backup
os.makedirs(backup_path, exist_ok=True)

# Diretório para armazenar backups
backup_dir = rf"{backup_path}"

# Obter a lista de todos os modelos do aplicativo
app_models = apps.get_models()

# Loop através de cada modelo e criar backups individuais
for model in app_models:
    app_label = model._meta.app_label
    model_name = model.__name__
    backup_filename = f"{app_label}_{model_name}.json"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    # Chamando o comando dumpdata para criar o backup JSON do modelo atual
    call_command("dumpdata", f"{app_label}.{model_name}", "--output", backup_path)

print(f"Backup realizado em {date}")
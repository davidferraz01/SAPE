# Etapa 1: Construindo a imagem do Django

FROM python:3.12-slim

# Setando o diretório de trabalho
WORKDIR /app

# Instalando as dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiando o código do projeto para o container
COPY . .

# Variável de ambiente para o Django
ENV DJANGO_SETTINGS_MODULE=SAPE.settings.prod

# Rodando o collectstatic
RUN python manage.py collectstatic --noinput

# Instalando o Gunicorn
RUN pip install gunicorn

# Comando para rodar o Gunicorn
CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:443", "SAPE.wsgi:application"]

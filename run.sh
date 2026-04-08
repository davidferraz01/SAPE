#!/bin/bash

# Remove existing containers (ignore if none exist)
docker rm -f $(docker ps -aq) 2>/dev/null || true

# Build and start all services
docker compose up -d --build

# Wait for the database to be ready
echo "Aguardando o banco de dados ficar pronto..."
until docker exec sape-db-1 pg_isready -U sape > /dev/null 2>&1; do
  sleep 1
done
echo "Banco de dados pronto!"

# Run migrations
echo "Executando migrações..."
docker exec sape-web-1 python manage.py migrate
echo "Migrações concluídas!"
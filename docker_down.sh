#!/usr/bin/env sh
set -e

# Para todos os containers (se houver)
docker ps -q | xargs -r docker stop

# Remove todos os containers (se houver) - opcional
docker ps -aq | xargs -r docker rm -f

# Para Docker sem chance de reativar por socket
sudo systemctl stop docker.socket
sudo systemctl stop docker.service
sudo systemctl stop containerd

# Impede iniciar no boot
sudo systemctl disable docker.socket
sudo systemctl disable docker.service

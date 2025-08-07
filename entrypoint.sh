#!/bin/sh

# Atualiza repositórios e instala o cron (caso a imagem base não tenha)
apt-get update && apt-get install -y cron python3-pip

# Instala os pacotes Python necessários
pip install --no-cache-dir -r /app/requirements.txt

# Cria cron job para rodar todos os dias às 19:29
echo "29 19 * * * python3 /app/script.py >> /app/log.txt 2>&1" > /etc/cron.d/yeastar_job

# Aplica permissões corretas
chmod 0644 /etc/cron.d/yeastar_job
crontab /etc/cron.d/yeastar_job

# Exibe confirmação
echo "Cron job agendado. Rodará todos os dias às 19:29."

# Inicia o cron em foreground para manter o container vivo
cron -f

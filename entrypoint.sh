#!/bin/sh

# Cria cron job para rodar todos os dias às 19:29
echo "29 19 * * * python3 /app/script.py >> /app/log.txt 2>&1" > cronjob
crontab cronjob

# Roda cron em primeiro plano
cron -f

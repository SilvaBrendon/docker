FROM python:3.11-slim

# Atualiza e instala dependências do sistema
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    gnupg \
    cron \
    fonts-liberation \
    libnss3 \
    libxss1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libgbm-dev \
    libxshmfence1 \
    libxi6 \
    libgconf-2-4 \
    libxrandr2 \
    libu2f-udev \
    libvulkan1 \
    libdrm2 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Instala Edge e EdgeDriver headless
RUN curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg \
 && install -o root -g root -m 644 microsoft.gpg /etc/apt/trusted.gpg.d/ \
 && sh -c 'echo "deb [arch=amd64] https://packages.microsoft.com/repos/edge stable main" > /etc/apt/sources.list.d/microsoft-edge-dev.list' \
 && apt-get update \
 && apt-get install -y microsoft-edge-stable \
 && rm -rf /var/lib/apt/lists/*

RUN wget https://msedgedriver.azureedge.net/124.0.2478.80/edgedriver_linux64.zip && \
    unzip edgedriver_linux64.zip && \
    mv msedgedriver /usr/local/bin/ && \
    chmod +x /usr/local/bin/msedgedriver

# Cria diretório do app
WORKDIR /app
COPY . /app

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Executa entrada
CMD ["sh", "entrypoint.sh"]

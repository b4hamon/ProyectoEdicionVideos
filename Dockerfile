# Imagen con Chromium ya instalado para Playwright
FROM mcr.microsoft.com/playwright:v1.56.0-noble
RUN apt-get update && apt-get install -y --no-install-recommends python3-pip ffmpeg && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY package.json ./
RUN npm install --omit=dev
COPY requirements.txt ./
RUN pip3 install --break-system-packages --no-cache-dir -r requirements.txt
COPY . .
ENV HOST=0.0.0.0 PORT=8000 NO_ABRIR=1
EXPOSE 8000
CMD ["python3", "-m", "app"]

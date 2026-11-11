FROM node:22-bookworm-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN python3 -m venv /opt/oracle-venv
ENV PATH="/opt/oracle-venv/bin:${PATH}"

COPY requirements-render.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements-render.txt

COPY package.json ./
RUN npm install --omit=dev

COPY . .
RUN chmod +x /app/start-render.sh

EXPOSE 10000
CMD ["/app/start-render.sh"]

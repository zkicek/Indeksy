# Używamy oficjalnego obrazu Ubuntu jako bazy
FROM ubuntu:latest

ENV GITHUB_TOKEN='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'
ENV GITHUB_REPO='zkicek/History'

# Aktualizacja systemu i instalacja Pythona
RUN apt-get update && \
    apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Utworzenie katalogu roboczego
WORKDIR /app

# Kopiowanie skryptu do kontenera
COPY History.py /app/
COPY Waluty.py /app/
COPY requirements.txt /app/

# Utworzenie i aktywacja wirtualnego środowiska
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Instalacja zależności
RUN pip3 install --no-cache-dir -r requirements.txt

# Ustawienie punktu wejścia na uruchomienie skryptu
CMD ["python3", "Waluty.py"]
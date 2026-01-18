FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Moscow

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    libxcb-cursor0 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcb-xinerama0 \
    libxcb-randr0 \
    libxcb-image0 \
    libxcb-shm0 \
    libxcb-keysyms1 \
    libxcb-icccm4 \
    libxcb-xfixes0 \
    libxcb-shape0 \
    libxcb-render-util0 \
    libxcb-xkb1 \
    libxkbcommon0 \
    libxkbcommon-x11-0 \
    libgl1-mesa-dev \
    libglu1-mesa-dev \
    libegl1-mesa \
    libgles2-mesa \
    libglib2.0-0 \
    libfontconfig1 \
    libfreetype6 \
    libdbus-1-3 \
    libsm6 \
    libice6 \
    xauth \
    x11-apps \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip3 install --no-cache-dir -r requirements.txt

RUN useradd -m fnirsuser && chown -R fnirsuser:fnirsuser /app
USER fnirsuser

ENV QT_QPA_PLATFORM=xcb
ENV QT_LOGGING_RULES='qt.qpa.*=false'
ENV DISPLAY=:0

CMD ["python3", "main.py", "--gui"]
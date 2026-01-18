#!/bin/bash


if ! command -v docker &> /dev/null; then
    echo "Ошибка: Docker не установлен. Установите Docker и повторите попытку."
    exit 1
fi

if [ -z "$DISPLAY" ]; then
    echo "Предупреждение: DISPLAY не установлен. Убедитесь, что X11 сервер запущен."
    echo "На Linux: убедитесь, что X11 запущен"
    echo "На macOS: установите XQuartz и перезапустите терминал"
    echo "На Windows: установите Xming или VcXsrv"
fi

echo "Сборка Docker образа..."
docker build -t fnirs-analyzer .

echo "Запуск FNIRS анализатора..."
docker run -it --rm \
    --name fnirs-app \
    -e DISPLAY=$DISPLAY \
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
    -v $(pwd)/data:/app/data:rw \
    fnirs-analyzer
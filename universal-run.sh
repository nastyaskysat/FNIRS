#!/bin/bash


echo "=== FNIRS Анализатор ==="

if command -v docker &> /dev/null; then
    echo "Docker обнаружен. Запуск через Docker контейнер..."
    
    if ! docker image inspect fnirs-analyzer &> /dev/null; then
        echo "Сборка Docker образа..."
        docker build -t fnirs-analyzer .
    fi
    
    xhost +local:docker 2>/dev/null
    
    docker run -it --rm \
        -e DISPLAY=$DISPLAY \
        -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
        -v $(pwd)/data:/app/data:rw \
        fnirs-analyzer
        
else
    echo "Docker не найден. Запуск локальной версии..."
    
    if ! ldconfig -p | grep -q libxcb-cursor; then
        echo "ВНИМАНИЕ: Библиотека libxcb-cursor не найдена."
        echo "Попытка запуска с альтернативным плагином Qt..."
        QT_QPA_PLATFORM=minimal python3 main.py --gui
    else
        python3 main.py --gui
    fi
fi
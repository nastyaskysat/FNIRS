@echo off

echo === FNIRS Анализатор ===

docker --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Docker обнаружен. Запуск через Docker контейнер...
    
    docker image inspect fnirs-analyzer >nul 2>&1
    if %errorlevel% neq 0 (
        echo Сборка Docker образа...
        docker build -t fnirs-analyzer .
    )
    
    echo Убедитесь, что X11 сервер запущен (Xming/VcXsrv)
    echo.
    docker run -it --rm ^
        -e DISPLAY=host.docker.internal:0.0 ^
        -v %CD%/data:/app/data:rw ^
        fnirs-analyzer
        
) else (
    echo Docker не найден. Запуск локальной версии...
    echo Убедитесь, что установлен Python и зависимости
    echo.
    python main.py --gui
)

pause

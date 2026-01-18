@echo off

docker --version >nul 2>&1
if errorlevel 1 (
    echo Ошибка: Docker не установлен. Установите Docker Desktop и повторите попытку.
    pause
    exit /b 1
)


echo Проверка X11 сервера...
echo Убедитесь, что Xming или VcXsrv запущен перед продолжением.
echo.

echo Сборка Docker образа...
docker build -t fnirs-analyzer .

echo Запуск FNIRS анализатора...
echo Убедитесь, что X11 сервер запущен (Xming/VcXsrv)
echo.

docker run -it --rm ^
    --name fnirs-app ^
    -e DISPLAY=host.docker.internal:0.0 ^
    -v %CD%/data:/app/data:rw ^
    fnirs-analyzer

pause

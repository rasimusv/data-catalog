# Выкачиваем из dockerhub образ с python версии 3.9
FROM python:3.9
# Устанавливаем рабочую директорию для проекта в контейнере
WORKDIR /web-server
# Скачиваем/обновляем необходимые библиотеки для проекта 
COPY requirements.txt /web-server
RUN pip3 install --upgrade pip -r requirements.txt
# |ВАЖНЫЙ МОМЕНТ| копируем содержимое папки, где находится Dockerfile, 
# в рабочую директорию контейнера
COPY . /web-server
# Устанавливаем порт, который будет использоваться для сервера
EXPOSE 3000
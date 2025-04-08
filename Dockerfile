# Используем официальный образ Python (можно указать нужную версию, например: python:3.9)
FROM python:3.11-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем зависимости и файлы проекта
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install hf_xet

# Копируем остальные файлы проекта (исключая ненужное через .dockerignore)
COPY .env .
COPY . .

EXPOSE 7860
ENV GRADIO_SERVER_NAME="0.0.0.0"

# Команда для запуска приложения (замените на свою, если нужно)
CMD ["python3", "main.py"]
FROM python:3.11-alpine

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Копирование остальных файлов
COPY . /app

CMD ["python", "bot.py"]
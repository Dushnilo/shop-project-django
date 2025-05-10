FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY static/ /app/static/
CMD bash -c "python manage.py collectstatic --noinput && (python manage.py runserver 0.0.0.0:8000 &) && python bot.py"

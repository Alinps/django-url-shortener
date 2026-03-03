#!/bin/bash

cleanup() {
  echo "Stopping all services..."
  kill $DJANGO_PID $WORKER_PID $BEAT_PID  2>/dev/null
  echo "Stopping Docker observability stack.."
  docker compose -f observability/docker-compose.yml down
  echo "Cleaning prometheus data.."
  rm -rf prometheus_data/*
  exit
}

trap cleanup SIGINT

echo "Starting Docker observability stack..."
docker compose -f observability/docker-compose.yml up -d
echo "Starting Celery worker..."
celery -A urlshortner worker --loglevel=info &
WORKER_PID=$!
echo "Starting Celery beat..."
celery -A urlshortner beat --loglevel=info &
BEAT_PID=$!
echo "Starting Django server..."
python manage.py runserver &
DJANGO_PID=$!





wait
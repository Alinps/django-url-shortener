#!/bin/bash

cleanup() {
  echo "Stopping all services and cleanup prometheus_data/"
  kill $DJANGO_PID $WORKER_PID $BEAT_PID
  rm -rf prometheus_data/*
  exit
}

trap cleanup SIGINT

celery -A urlshortner worker --loglevel=info &
WORKER_PID=$!

celery -A urlshortner beat --loglevel=info &
BEAT_PID=$!

python manage.py runserver &
DJANGO_PID=$!

wait
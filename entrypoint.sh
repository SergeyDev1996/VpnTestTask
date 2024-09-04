#!/bin/sh

# Wait for PostgreSQL to be available
echo "Waiting for PostgreSQL..."
while ! nc -z postgres 5432; do
  sleep 1
done
echo "PostgreSQL is up and running!"

# Run database migrations
echo "Running migrations..."
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start the Django server
echo "Starting Django server..."
exec python manage.py runserver 0.0.0.0:8000
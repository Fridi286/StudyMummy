#!/bin/sh
# Seed static item images into the named volume if not already present
if [ -d "/app/static_seed/items" ] && [ ! -f "/app/static/items/.seeded" ]; then
    echo "Seeding static item images into volume..."
    mkdir -p /app/static/items
    cp -n /app/static_seed/items/* /app/static/items/
    touch /app/static/items/.seeded
    echo "Static items seeded."
fi

mkdir -p /app/static/avatars

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips "*"

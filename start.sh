#!/usr/bin/env bash
set -e

DBFILE="app/app.db"   # adjust if your config puts app.db elsewhere

if [ "$RESET_DB" = "1" ]; then
  echo "==> RESET_DB=1; removing $DBFILE"
  rm -f "$DBFILE"
fi

echo "==> Ensure schema exists..."
python - <<'PY'
from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
    print("db.create_all() done")
PY

echo "==> Starting Gunicorn..."
exec gunicorn -w 2 -k gthread --threads 8 -b 0.0.0.0:${PORT} microblog:app
# or: "app:create_app()" if you don't have microblog.py

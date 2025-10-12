#!/usr/bin/env bash
set -e

echo "==> Running DB migrations (or create_all fallback)..."

# Try Flask-Migrate first (needs FLASK_APP and Flask-Migrate configured)
if flask db upgrade; then
  echo "==> Migrations applied."
else
  echo "==> flask db upgrade failed, falling back to db.create_all()"
  python - <<'PY'
from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
    print("db.create_all() done")
PY
fi

echo "==> Starting Gunicorn..."
# If you have microblog.py exposing "app = create_app()":
exec gunicorn -w 2 -k gthread --threads 8 -b 0.0.0.0:${PORT} microblog:app
# If you DON'T have microblog.py and run the factory directly, use:
# exec gunicorn -w 2 -k gthread --threads 8 -b 0.0.0.0:${PORT} "app:create_app()"

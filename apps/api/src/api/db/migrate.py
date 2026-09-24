"""Run pending SQL migration files from apps/api/migrations/."""

from pathlib import Path

from sqlalchemy import text

from api.db.database import engine

MIGRATIONS_DIR = Path(__file__).resolve().parents[3] / "migrations"


def run_migrations() -> None:
    MIGRATIONS_DIR.mkdir(parents=True, exist_ok=True)

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    filename TEXT PRIMARY KEY,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
        )

        applied = {
            row[0]
            for row in conn.execute(text("SELECT filename FROM schema_migrations"))
        }

        for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            if path.name in applied:
                print(f"skip {path.name}")
                continue

            print(f"apply {path.name}")
            conn.execute(text(path.read_text()))
            conn.execute(
                text("INSERT INTO schema_migrations (filename) VALUES (:filename)"),
                {"filename": path.name},
            )

    print("migrations done")


if __name__ == "__main__":
    run_migrations()

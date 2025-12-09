import os
import psycopg2

MIGRATIONS_DIR = "database/migrations"


def apply_migrations():
    """
    Применяет все SQL миграции из папки database/migrations.
    Скрипт идемпотентен, если сами SQL-миграции аккуратные (IF NOT EXISTS и т.п.).
    """
    dbname = os.getenv("POSTGRES_DB")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = os.getenv("POSTGRES_PORT", "5432")

    conn = psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port,
    )

    conn.autocommit = True
    cursor = conn.cursor()

    print("🔧 Applying migrations...")

    for file in sorted(os.listdir(MIGRATIONS_DIR)):
        if not file.endswith(".sql"):
            continue

        path = os.path.join(MIGRATIONS_DIR, file)
        print(f"📄 Executing migration {file}")

        with open(path, "r", encoding="utf-8") as f:
            sql = f.read()
            cursor.execute(sql)

    cursor.close()
    conn.close()
    print("✅ Migrations completed.")


if __name__ == "__main__":
    apply_migrations()

#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
DB_DIR="$PROJECT_DIR/db"
DB_FILE="$DB_DIR/lab.db"

rm -f "$DB_FILE"
sqlite3 "$DB_FILE" < "$DB_DIR/schema.sql"
sqlite3 "$DB_FILE" < "$DB_DIR/seed.sql"
sqlite3 "$DB_FILE" < "$DB_DIR/seed_forum.sql"

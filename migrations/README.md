# Database Migrations

This directory contains SQL migration scripts for calibre-web-ai.

## Running Migrations

### Option 1: Direct SQL (Recommended)

Run the SQL file directly against your database using `sqlite3`:

```bash
sqlite3 app.db < migrations/003_add_chunk_tables.sql
```

Or if your database is in a different location:

```bash
sqlite3 /path/to/app.db < migrations/003_add_chunk_tables.sql
```

### Option 2: SQLite Command Line

```bash
sqlite3 app.db
.read migrations/003_add_chunk_tables.sql
.quit
```

### Option 3: Python (if you need error handling)

```python
import sqlite3
conn = sqlite3.connect('app.db')
with open('migrations/003_add_chunk_tables.sql', 'r') as f:
    conn.executescript(f.read())
conn.close()
```

## Migration Files

- **001_add_ai_tables.sql** - Creates `book_summaries` and `book_embeddings` tables (Epic 1)
- **002_create_vec_table.sql** - Creates `book_embeddings_vec` virtual table for sqlite-vec (Epic 1)
- **003_add_chunk_tables.sql** - Creates chunk tables for full book indexing (Epic 6)

## Notes

- All migrations use `IF NOT EXISTS` so they're safe to run multiple times
- The virtual table creation requires sqlite-vec extension to be loaded
- SQLite doesn't support schemas, so `app_settings.` prefix is ignored but kept for documentation

## Virtual Table Creation

**Important:** Migration 003 includes a virtual table creation that requires the sqlite-vec extension. If you see an error like `no such module: vec0` when running the migration from command line, **that's okay**. The regular tables will still be created successfully.

The virtual table (`book_chunk_embeddings_vec`) will be created automatically when the application runs, because:
1. The application loads sqlite-vec on startup
2. The code checks for and creates the virtual table if it doesn't exist

### If you want to create the virtual table manually:

**Option 1: Let the app create it** (Recommended)
- Just run the migration - ignore the virtual table error
- Start the app - it will create the virtual table automatically

**Option 2: Create it manually with sqlite3**
```bash
sqlite3 app.db
.load sqlite_vec
CREATE VIRTUAL TABLE IF NOT EXISTS book_chunk_embeddings_vec USING vec0(
    chunk_id INTEGER PRIMARY KEY,
    embedding FLOAT[1536]
);
.quit
```

**Option 3: Use Python to load extension first**
```bash
python -c "import sqlite3, sqlite_vec; conn = sqlite3.connect('app.db'); sqlite_vec.load(conn); conn.execute('CREATE VIRTUAL TABLE IF NOT EXISTS book_chunk_embeddings_vec USING vec0(chunk_id INTEGER PRIMARY KEY, embedding FLOAT[1536])'); conn.commit(); conn.close()"
```


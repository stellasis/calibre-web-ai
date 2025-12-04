# SQLite Vector Extension Migration

## Summary

Successfully migrated from `sqlite-vss` to `sqlite-vec` for vector similarity search functionality.

## Why the Migration?

- **`sqlite-vss`**: Older extension, not available on PyPI for Python 3.13+
- **`sqlite-vec`**: Newer, actively maintained successor by the same author (Alex Garcia)
  - Written in pure C (faster, smaller)
  - Better Python 3.13+ support
  - Available on PyPI with pre-built wheels for Windows/Mac/Linux
  - Simpler API and better performance

## Changes Made

### 1. Python Package
- **Installed**: `sqlite-vec>=0.1.0` (added to `requirements.txt`)
- **Version**: v0.1.6 successfully installed and tested

### 2. Database Migration
- **File renamed**: `migrations/002_create_vss_table.sql` → `migrations/002_create_vec_table.sql`
- **Syntax updated**: Changed from `vss0` module to `vec0` module
- **New table structure**:
  ```sql
  CREATE VIRTUAL TABLE IF NOT EXISTS app_settings.book_embeddings_vec USING vec0(
      book_id INTEGER PRIMARY KEY,
      embedding FLOAT[1536]
  );
  ```

### 3. Code Updates (`cps/db.py`)
- Removed fallback logic (no longer needed)
- **New approach**: Load `sqlite_vec` Python package directly
- **Verification**: Check `vec_version()` on startup
- **Error handling**: Fail fast if extension cannot load (as required)

```python
import sqlite_vec

# Get raw SQLite connection
raw_conn = connection.connection.dbapi_connection
raw_conn.enable_load_extension(True)

# Load extension
sqlite_vec.load(raw_conn)
raw_conn.enable_load_extension(False)

# Verify
vec_version, = raw_conn.execute("select vec_version()").fetchone()
```

### 4. Testing
- **Test script**: `test-extension-load.py` updated to test `sqlite-vec`
- **Result**: ✅ All tests pass

## API Differences

### sqlite-vss (old)
```sql
CREATE VIRTUAL TABLE ... USING vss0(vector(1536));
SELECT * FROM table WHERE vss_search(vector, :query);
```

### sqlite-vec (new)
```sql
CREATE VIRTUAL TABLE ... USING vec0(embedding FLOAT[1536]);
SELECT * FROM table WHERE embedding MATCH :query ORDER BY distance LIMIT 10;
```

## Benefits
1. **No manual binary installation** - Works with `pip install`
2. **Python 3.13 support** - Pre-built wheels available
3. **Better performance** - Pure C implementation
4. **Simpler API** - More intuitive KNN search syntax
5. **Active maintenance** - Newer, better supported project

## Testing

```bash
# Install
pip install sqlite-vec

# Test
python test-extension-load.py

# Expected output:
# ✅ sqlite-vec version v0.1.6 is available!
# ✅ vec0 module is available!
```

## Future Story Updates

When implementing stories for Epic 2, 3, and 4, use the new `sqlite-vec` API:

- **Embedding generation** → Store in `book_embeddings` table
- **Vector search** → Use `vec0` virtual table with `MATCH` operator
- **Similar books** → KNN search with `ORDER BY distance LIMIT k`

## References

- sqlite-vec GitHub: https://github.com/asg017/sqlite-vec
- Documentation: https://github.com/asg017/sqlite-vec/tree/main/site
- PyPI: https://pypi.org/project/sqlite-vec/





# Installing sqlite-vss Extension

The sqlite-vss extension is required for AI features (semantic search, similar books). This guide covers installation for different platforms.

## Quick Install (Recommended)

```bash
# Activate your virtual environment first
source venv/bin/activate  # Linux/macOS
# or
source venv/Scripts/activate  # Windows (Git Bash)

# Install sqlite-vss
pip install sqlite-vss
```

## Verify Installation

After installation, verify it works:

```bash
python test-extension-load.py
```

Or test directly:

```bash
python -c "import sqlite3; import sqlite_vss; conn = sqlite3.connect(':memory:'); conn.enable_load_extension(True); sqlite_vss.load(conn); print('✅ sqlite-vss installed and working!')"
```

## Platform-Specific Instructions

### Windows

**Option 1: pip install (Recommended)**
```bash
pip install sqlite-vss
```

**Option 2: Pre-built Binary**
If pip install fails or causes segfaults:
1. Download pre-built binary from: https://github.com/asg017/sqlite-vss/releases
2. Look for `vector0.dll` for Windows
3. Place it in a directory in your system PATH, or use full path in code

**Troubleshooting Windows:**
- If you get "not authorized" error: Extension loading is disabled by default on Windows
- If you get segfault: The binary might be incompatible with your Python/SQLite version
- Try: `pip install --upgrade sqlite-vss` to get latest version

### Linux

**Option 1: pip install**
```bash
pip install sqlite-vss
```

**Option 2: System Dependencies (if needed)**
Some Linux systems may need additional libraries:
```bash
sudo apt-get update
sudo apt-get install -y libgomp1 libatlas-base-dev liblapack-dev
pip install sqlite-vss
```

**Option 3: Pre-built Binary**
Download `vector0.so` from releases and place in system library path.

### macOS

**Option 1: pip install**
```bash
pip install sqlite-vss
```

**Option 2: Homebrew (if available)**
```bash
brew install sqlite-vss  # If formula exists
```

**Option 3: Pre-built Binary**
Download `vector0.dylib` from releases.

## Installation via requirements.txt

The project already includes sqlite-vss in `requirements.txt`:

```bash
# Install all dependencies including sqlite-vss
pip install -r requirements.txt
```

## Verifying the Extension Works

### Test 1: Python Import Test
```bash
python -c "import sqlite_vss; print('✅ sqlite-vss module imported')"
```

### Test 2: Extension Loading Test
```bash
python test-extension-load.py
```

### Test 3: Version Check
```python
import sqlite3
import sqlite_vss

conn = sqlite3.connect(':memory:')
conn.enable_load_extension(True)
sqlite_vss.load(conn)

version, = conn.execute('SELECT vss_version()').fetchone()
print(f"sqlite-vss version: {version}")
```

## Troubleshooting

### Issue: Segmentation Fault

**Symptom:** App crashes with "Segmentation fault" when loading extension.

**Causes:**
- Extension binary incompatible with Python/SQLite version
- Architecture mismatch (x86 vs x64)
- Corrupted extension file

**Solutions:**
1. Check Python and SQLite versions:
   ```bash
   python --version
   python -c "import sqlite3; print(sqlite3.sqlite_version)"
   ```

2. Reinstall sqlite-vss:
   ```bash
   pip uninstall sqlite-vss
   pip install --upgrade sqlite-vss
   ```

3. Try different version:
   ```bash
   pip install sqlite-vss==0.1.2  # Try specific version
   ```

4. Use pre-built binary matching your system

### Issue: "not authorized"

**Symptom:** Error: "not authorized" when loading extension.

**Solution:** Extension loading is now enabled in the code. If you still get this error, check that `enable_load_extension: True` is in the connection args.

### Issue: "The specified module could not be found"

**Symptom:** Extension file not found.

**Solutions:**
1. Verify installation:
   ```bash
   pip show sqlite-vss
   ```

2. Find extension file location:
   ```bash
   python -c "import sqlite_vss; print(sqlite_vss.__file__)"
   ```

3. Use full path if needed (modify `cps/db.py`)

### Issue: Extension loads but vss functions don't work

**Symptom:** Extension loads but `vss0` module not available.

**Solution:** Make sure both `vector0` and `vss0` are loaded. The current code loads `vector0` which should provide both.

## Alternative: Skip Extension (Development Only)

If you can't get the extension working and just want to develop other features:

```bash
export SKIP_SQLITE_VSS=1
./run-dev.sh
```

**Warning:** AI features will NOT work without the extension!

## Next Steps

After successful installation:
1. Restart the app: `./run-dev.sh`
2. Look for: `"✅ sqlite-vss extension loaded successfully"` in logs
3. If you see this message, the extension is working!

## References

- sqlite-vss GitHub: https://github.com/asg017/sqlite-vss
- Releases: https://github.com/asg017/sqlite-vss/releases
- Documentation: https://github.com/asg017/sqlite-vss#readme

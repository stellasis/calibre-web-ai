# Calibre-Web-AI - Development Guide

**Date:** 2025-01-27

## Prerequisites

- **Python:** Version 3.7 or newer (Python 3.8+ recommended)
- **Imagemagick:** Required for cover extraction from EPUBs
- **Ghostscript:** Required for PDF cover extraction on Windows
- **Calibre Desktop:** Optional, but recommended for:
  - On-the-fly eBook conversion
  - Metadata editing
  - Set path to Calibre's converter tool in admin interface
- **Kepubify Tool:** Optional, for Kobo device support
  - Linux: Place binary in `/opt/kepubify`
  - Windows: Place binary in `C:\Program Files\kepubify`

## Environment Setup

### 1. Create Virtual Environment

It's essential to isolate your Calibre-Web installation to avoid dependency conflicts:

```bash
python3 -m venv calibre-web-env
```

### 2. Activate Virtual Environment

**Linux/macOS:**
```bash
source calibre-web-env/bin/activate
```

**Windows:**
```bash
calibre-web-env\Scripts\activate
```

### 3. Install Dependencies

**Core Installation:**
```bash
pip install calibreweb
```

**Or install from source:**
```bash
git clone <repository-url>
cd calibre-web-ai
pip install -e .
```

**Optional Features:**

Install optional dependencies based on needed features:

```bash
# Google Drive integration
pip install calibreweb[gdrive]

# Gmail integration
pip install calibreweb[gmail]

# Goodreads integration
pip install calibreweb[goodreads]

# LDAP authentication
pip install calibreweb[ldap]

# OAuth support
pip install calibreweb[oauth]

# Metadata providers
pip install calibreweb[metadata]

# Comics support
pip install calibreweb[comics]

# Kobo device support
pip install calibreweb[kobo]
```

**Note for Raspberry Pi OS users:**
If you encounter installation issues, try:
```bash
./venv/bin/python3 -m pip install --upgrade pip
sudo apt install cargo
```

## Local Development

### Start Development Server

After installation, start the application:

```bash
cps
```

The application will start on `http://localhost:8083` by default.

### Configuration

1. **First Run:**
   - Access: `http://localhost:8083`
   - Default credentials:
     - Username: `admin`
     - Password: `admin123`
   - **Important:** Change default password immediately

2. **Database Setup:**
   - If you don't have a Calibre database, download a sample:
     ```bash
     wget https://github.com/janeczku/calibre-web/raw/master/library/metadata.db
     ```
   - Move it out of the Calibre-Web folder to avoid overwriting during updates
   - In admin interface, set `Location of Calibre database` to the path containing your Calibre library
   - Click "Save"

3. **Environment Variables:**
   - `FLASK_DEBUG`: Enable debug mode
   - `SECRET_KEY`: Flask session secret key (auto-generated if not set)
   - `CALIBRE_DBPATH`: Override default config directory
   - `CACHE_DIR`: Override default cache directory
   - `COOKIE_PREFIX`: Prefix for session cookies

## Build Process

This project uses standard Python packaging:

```bash
# Build distribution packages
python -m build

# Install in development mode
pip install -e .
```

## Testing

The project includes test infrastructure (separate repository):

- **Test Repository:** https://github.com/OzzieIsaacs/calibre-web-test
- **Test Framework:** Unit tests and Selenium system tests
- **Python Version:** Tested on Python 3.8+

**Running Tests:**
```bash
# Unit tests (if available locally)
python -m pytest

# Static code analysis
# Codacy is used but may be partially broken
# ESLint configuration available in project root
```

## Development Workflow

### Project Structure

- **Main Package:** `cps/` - All application code
- **Blueprints:** Route modules in `cps/` root (web.py, admin.py, etc.)
- **Services:** Background services in `cps/services/`
- **Templates:** Jinja2 templates in `cps/templates/`
- **Static Assets:** Frontend files in `cps/static/`

### Adding New Features

1. **Routes:** Create or extend a blueprint module
2. **Templates:** Add Jinja2 templates in `cps/templates/`
3. **Static Assets:** Add CSS/JS in `cps/static/`
4. **Services:** Add business logic in `cps/services/`
5. **Background Tasks:** Add task handlers in `cps/tasks/`

### Code Style

- **Language:** Python 3.7+
- **Style:** Follow PEP 8 conventions
- **Testing:** Write unit tests for new features
- **Documentation:** Update docstrings and comments

### Database Changes

- **User Database:** Managed via SQLAlchemy models in `cps/ub.py`
- **Calibre Database:** Read-only access via `cps/db.py`
- **Migrations:** Handle schema changes carefully to maintain compatibility

## Common Development Tasks

### Adding a New Blueprint

1. Create new file: `cps/new_feature.py`
2. Define blueprint:
   ```python
   from flask import Blueprint
   new_feature = Blueprint("new_feature", __name__)
   ```
3. Register in `cps/main.py`:
   ```python
   app.register_blueprint(new_feature)
   ```

### Adding a New Template

1. Create template file in `cps/templates/`
2. Extend base layout:
   ```jinja2
   {% extends "layout.html" %}
   {% block content %}
   <!-- Your content -->
   {% endblock %}
   ```

### Adding Background Tasks

1. Create task handler in `cps/tasks/`
2. Schedule via `cps/services/background_scheduler.py`
3. Track status via `cps/tasks_status.py`

## Debugging

### Enable Debug Mode

```bash
export FLASK_DEBUG=1
cps
```

### View Logs

- Application logs are written to console
- Check for error messages in terminal output
- Log level configured in `cps/logger.py`

### Common Issues

- **Import Errors:** Ensure virtual environment is activated
- **Database Errors:** Verify Calibre database path is correct
- **Port Conflicts:** Change port in configuration or environment
- **Permission Errors:** Check file permissions on database and cache directories

## Deployment

### Production Considerations

- Use a production WSGI server (Gunicorn, uWSGI)
- Set proper `SECRET_KEY` environment variable
- Configure reverse proxy (nginx, Apache)
- Enable HTTPS
- Set up proper logging
- Configure backup strategy for user database

### Docker

Pre-built Docker images available:
- **LinuxServer:** [linuxserver/calibre-web](https://hub.docker.com/r/linuxserver/calibre-web)
- Include Calibre binaries: Set `DOCKER_MODS=linuxserver/mods:universal-calibre`

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed contribution guidelines.

Key points:
- Communication language: English
- Python 3 only (Python 2 no longer supported)
- Test on both Windows and Linux if possible
- Follow existing code style
- Write tests for new features
- Update documentation

---

_Generated using BMAD Method `document-project` workflow_


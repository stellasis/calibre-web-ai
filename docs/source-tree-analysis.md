# Calibre-Web-AI - Source Tree Analysis

**Date:** 2025-01-27

## Overview

This is a monolithic Python Flask web application with a well-organized modular structure. The codebase is contained primarily in the `cps/` directory, which serves as the main application package. The project uses a blueprint-based architecture for route organization and includes comprehensive static assets, templates, and internationalization support.

## Complete Directory Structure

```
calibre-web-ai/
├── cps/                          # Main application package
│   ├── __init__.py              # Flask app initialization
│   ├── main.py                  # Application entry point
│   ├── constants.py             # Application constants and configuration
│   ├── config_sql.py            # SQL-based configuration management
│   ├── db.py                    # Calibre database interface
│   ├── ub.py                    # User database models and utilities
│   ├── server.py                # Web server configuration
│   ├── logger.py                # Logging configuration
│   ├── cli.py                   # Command-line interface parameters
│   ├── dep_check.py             # Dependency checking
│   ├── updater.py               # Auto-update functionality
│   │
│   ├── Blueprints/              # Route modules (Flask blueprints)
│   │   ├── web.py               # Main web interface routes
│   │   ├── admin.py             # Admin interface routes
│   │   ├── search.py            # Search functionality
│   │   ├── search_metadata.py   # Metadata search
│   │   ├── basic.py             # Basic/bare interface routes
│   │   ├── opds.py              # OPDS feed routes
│   │   ├── shelf.py             # Book shelf/collection routes
│   │   ├── editbooks.py         # Book editing routes
│   │   ├── about.py             # About page
│   │   ├── tasks_status.py      # Background task status
│   │   ├── remotelogin.py      # Remote login functionality
│   │   ├── gdrive.py            # Google Drive integration
│   │   ├── kobo.py              # Kobo device sync
│   │   ├── kobo_auth.py         # Kobo authentication
│   │   ├── oauth.py             # OAuth authentication
│   │   ├── oauth_bb.py          # OAuth (alternative)
│   │   └── jinjia.py            # Jinja2 template helpers
│   │
│   ├── services/                # Background services and integrations
│   │   ├── __init__.py
│   │   ├── background_scheduler.py  # Task scheduling
│   │   ├── Metadata.py          # Metadata provider service
│   │   ├── gmail.py             # Gmail integration
│   │   ├── goodreads_support.py # Goodreads integration
│   │   ├── simpleldap.py        # LDAP authentication
│   │   ├── SyncToken.py         # Sync token management
│   │   └── worker.py            # Background worker
│   │
│   ├── metadata_provider/       # Metadata source plugins
│   │   ├── amazon.py
│   │   ├── comicvine.py
│   │   ├── douban.py
│   │   ├── google.py
│   │   ├── lubimyczytac.py
│   │   └── scholar.py
│   │
│   ├── tasks/                    # Background task definitions
│   │   ├── __init__.py
│   │   ├── clean.py             # Cleanup tasks
│   │   ├── convert.py           # Book conversion tasks
│   │   ├── database.py          # Database tasks
│   │   ├── mail.py              # Email tasks
│   │   ├── metadata_backup.py  # Metadata backup
│   │   ├── thumbnail.py         # Thumbnail generation
│   │   └── upload.py            # Upload processing
│   │
│   ├── cw_login/                # Custom login manager
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── login_manager.py
│   │   ├── mixins.py
│   │   ├── signals.py
│   │   └── utils.py
│   │
│   ├── cw_advocate/              # HTTP connection pool management
│   │   ├── __init__.py
│   │   ├── adapters.py
│   │   ├── connection.py
│   │   ├── connectionpool.py
│   │   ├── poolmanager.py
│   │   └── exceptions.py
│   │
│   ├── templates/                # Jinja2 HTML templates
│   │   ├── layout.html          # Base layout template
│   │   ├── index.html           # Home page
│   │   ├── detail.html          # Book detail page
│   │   ├── search.html          # Search page
│   │   ├── admin.html           # Admin interface
│   │   └── [30+ more templates]
│   │
│   ├── static/                   # Static assets
│   │   ├── css/                 # Stylesheets
│   │   ├── js/                  # JavaScript files
│   │   ├── img/                 # Images
│   │   ├── locale/              # Translation files (Fluent)
│   │   ├── fonts/               # Web fonts
│   │   └── standard_fonts/      # PDF fonts
│   │
│   ├── translations/            # Python gettext translations
│   │   └── [30+ language directories]
│   │
│   ├── Helper modules/          # Utility modules
│   │   ├── helper.py
│   │   ├── file_helper.py
│   │   ├── string_helper.py
│   │   ├── embed_helper.py
│   │   ├── epub_helper.py
│   │   ├── clean_html.py
│   │   ├── pagination.py
│   │   ├── render_template.py
│   │   └── reverseproxy.py
│   │
│   └── Format readers/          # eBook format parsers
│       ├── epub.py
│       ├── fb2.py
│       ├── comic.py
│       └── audio.py
│
├── docs/                         # Project documentation
│   ├── prd.md                   # Product Requirements Document
│   └── sprint-artifacts/        # Sprint planning artifacts
│
├── test/                         # Test files
│
├── library/                      # Sample/test library
│   └── metadata.db              # Sample Calibre database
│
├── pyproject.toml               # Python project configuration
├── requirements.txt             # Python dependencies
├── optional-requirements.txt    # Optional dependencies
├── README.md                     # Project readme
├── CONTRIBUTING.md              # Contribution guidelines
├── SECURITY.md                  # Security policy
└── LICENSE                      # GPL v3 license
```

## Critical Directories

### `cps/`

**Purpose:** Main application package containing all application code
**Contains:** Blueprints, services, models, templates, static assets
**Entry Points:** `cps/main.py` → `main()` function, `cps/__init__.py` → `create_app()`

### `cps/templates/`

**Purpose:** Jinja2 HTML templates for server-side rendering
**Contains:** Layout templates, page templates, component fragments
**Integration:** Used by all blueprint modules for rendering HTML responses

### `cps/static/`

**Purpose:** Static web assets (CSS, JavaScript, images, fonts)
**Contains:** Frontend assets, localization files, fonts
**Integration:** Served directly by Flask static file handler

### `cps/services/`

**Purpose:** Background services and external integrations
**Contains:** Task scheduling, metadata providers, authentication services
**Integration:** Used by blueprints and background tasks

### `cps/tasks/`

**Purpose:** Background task definitions
**Contains:** Task handlers for conversion, cleanup, upload, etc.
**Integration:** Scheduled by `background_scheduler.py`

### `cps/metadata_provider/`

**Purpose:** Pluggable metadata source providers
**Contains:** Provider implementations for Amazon, Google, Goodreads, etc.
**Integration:** Used by `services/Metadata.py`

## Entry Points

- **Main Entry:** `cps/main.py` → `main()` function
  - Initializes Flask app via `create_app()`
  - Registers all blueprints
  - Starts web server
  - Entry command: `cps` (via pyproject.toml script)

- **Application Factory:** `cps/__init__.py` → `create_app()` function
  - Creates and configures Flask application instance
  - Initializes database connections
  - Sets up authentication and authorization
  - Configures blueprints

## File Organization Patterns

- **Blueprint Pattern:** Each major feature area has its own blueprint module (web.py, admin.py, search.py)
- **Service Layer:** Business logic separated into `services/` directory
- **Task Pattern:** Background tasks organized in `tasks/` directory
- **Template Organization:** Templates mirror route structure
- **Static Assets:** Organized by type (css/, js/, img/, fonts/)

## Key File Types

### Python Modules
- **Pattern:** `*.py`
- **Purpose:** Application logic, routes, services, utilities
- **Examples:** `web.py`, `db.py`, `helper.py`

### Templates
- **Pattern:** `*.html` in `templates/`
- **Purpose:** Jinja2 HTML templates for server-side rendering
- **Examples:** `layout.html`, `detail.html`, `search.html`

### Static Assets
- **Pattern:** `*.css`, `*.js`, `*.png`, `*.svg` in `static/`
- **Purpose:** Frontend assets served directly
- **Examples:** `main.css`, `reader.js`, `icon.png`

### Configuration
- **Pattern:** `pyproject.toml`, `requirements.txt`, `*.yaml`
- **Purpose:** Project configuration and dependencies
- **Examples:** `pyproject.toml`, `requirements.txt`

## Asset Locations

- **CSS Stylesheets:** `cps/static/css/` (10+ files)
- **JavaScript:** `cps/static/js/` (192+ files)
- **Images:** `cps/static/img/` and `cps/static/css/images/` (100+ files)
- **Fonts:** `cps/static/fonts/` and `cps/static/standard_fonts/` (26+ files)
- **Translations:** `cps/static/locale/` (111 Fluent translation files)

## Configuration Files

- **`pyproject.toml`**: Python project metadata and dependencies
- **`requirements.txt`**: Core Python dependencies
- **`optional-requirements.txt`**: Optional feature dependencies
- **`babel.cfg`**: Babel translation configuration
- **`.env`** (if present): Environment variables

## Notes for Development

- The application uses a dual-database approach: user database (ub) and Calibre database (calibre_db)
- Blueprints are registered in `main.py` after app creation
- Configuration is stored in SQL database via `config_sql.py`
- Background tasks use APScheduler for scheduling
- Static assets are served from `cps/static/` directory
- Templates use Jinja2 with custom filters and helpers
- Internationalization supports both Python gettext and Fluent formats

---

_Generated using BMAD Method `document-project` workflow_


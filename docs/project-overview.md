# Calibre-Web-AI - Project Overview

**Date:** 2025-01-27
**Type:** Web Application (Python Flask)
**Architecture:** Monolithic Server-Side Rendered Web Application

## Executive Summary

Calibre-Web-AI is a Python Flask web application that extends the original Calibre-Web project with AI-powered discovery features. The application provides a web interface for browsing, reading, and downloading eBooks stored in a Calibre database, with plans to add AI-generated book summaries, semantic search, and similar book recommendations.

The codebase is a monolithic Flask application using server-side rendering with Jinja2 templates, SQLAlchemy for database access, and a modular blueprint-based architecture.

## Project Classification

- **Repository Type:** Monolith
- **Project Type(s):** Web Application (Python Flask)
- **Primary Language(s):** Python 3.8+
- **Architecture Pattern:** Blueprint-based modular Flask application with server-side rendering

## Technology Stack Summary

| Category | Technology | Version/Details | Justification |
|----------|-----------|----------------|---------------|
| **Framework** | Flask | >=1.0.2,<3.2.0 | Core web framework |
| **Database ORM** | SQLAlchemy | >=1.3.0,<2.1.0 | Database abstraction layer |
| **Template Engine** | Jinja2 | (via Flask) | Server-side rendering |
| **Authentication** | Flask-Login | (via MyLoginManager) | User session management |
| **Authorization** | Flask-Principal | >=0.3.2,<0.5.1 | Role-based access control |
| **Internationalization** | Flask-Babel | >=3.0.0,<4.1.0 | Multi-language support |
| **Rate Limiting** | Flask-Limiter | >=2.3.0,<3.13.0 | API rate limiting |
| **CSRF Protection** | Flask-WTF | >=0.14.2,<1.3.0 | Cross-site request forgery protection |
| **Task Scheduling** | APScheduler | >=3.6.3,<3.12.0 | Background job scheduling |
| **Web Server** | Tornado | >=6.4.2,<6.6 | WSGI server |
| **PDF Processing** | PyPDF | >=3.15.6,<5.5.0 | PDF manipulation |
| **Image Processing** | Wand | >=0.4.4,<0.7.0 | ImageMagick bindings for cover extraction |
| **HTTP Client** | Requests | >=2.32.0,<2.33.0 | External API calls |
| **XML/HTML Parsing** | lxml | >=4.9.1,<5.4.0 | XML/HTML processing |
| **Security** | Cryptography | >=39.0.0,<45.0.0 | Encryption and security utilities |
| **Text Processing** | Unidecode | >=0.04.19,<1.4.0 | Unicode normalization |
| **Content Sanitization** | Bleach | >=6.0.0,<6.3.0 | HTML sanitization |

## Key Features

- Web-based eBook library management interface
- User authentication and authorization with fine-grained permissions
- Multi-language support (20+ languages)
- OPDS feed for eBook reader apps
- Advanced search and filtering
- Custom book collections (shelves)
- eBook metadata editing
- Metadata download from various sources (extensible via plugins)
- eBook conversion through Calibre binaries
- In-browser eBook reading support for multiple formats
- Upload new books in various formats
- Kobo device synchronization
- Google Drive integration (optional)
- LDAP authentication (optional)
- OAuth support (optional)

## Architecture Highlights

- **Blueprint Architecture:** Modular route organization using Flask blueprints (web, admin, opds, search, etc.)
- **Database Layer:** SQLAlchemy ORM with separate user database (ub) and Calibre database (calibre_db)
- **Service Layer:** Modular services for background tasks, metadata providers, and external integrations
- **Template System:** Jinja2 templates for server-side rendering with static asset management
- **Configuration:** SQL-based configuration storage with encryption support
- **Task System:** Background task processing with status tracking

## Development Overview

### Prerequisites

- Python 3.7 or newer
- Imagemagick (for cover extraction from EPUBs)
- Calibre desktop program (optional, for conversion and metadata editing)
- Kepubify tool (optional, for Kobo device support)

### Getting Started

1. Create a virtual environment: `python3 -m venv calibre-web-env`
2. Activate the virtual environment: `source calibre-web-env/bin/activate`
3. Install Calibre-Web: `pip install calibreweb`
4. Start the application: `cps`
5. Access at: `http://localhost:8083`

### Key Commands

- **Install:** `pip install calibreweb`
- **Dev:** `cps` (runs development server)
- **Entry Point:** `cps/main.py` → `main()` function

## Repository Structure

The project follows a monolithic structure with all code in the `cps/` directory:

- **`cps/`** - Main application package
  - **Blueprints:** Route modules (web.py, admin.py, search.py, etc.)
  - **Services:** Background services and integrations
  - **Templates:** Jinja2 HTML templates
  - **Static:** CSS, JavaScript, images, fonts
  - **Database:** SQLAlchemy models and database utilities
  - **Tasks:** Background task definitions

## Documentation Map

For detailed information, see:

- [index.md](./index.md) - Master documentation index
- [source-tree-analysis.md](./source-tree-analysis.md) - Directory structure
- [development-guide.md](./development-guide.md) - Development workflow

---

_Generated using BMAD Method `document-project` workflow_


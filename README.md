# Calibre-Web

> **stellasis fork:** see [FORK.md](./FORK.md) for remotes, chapter-aware chunking, and tests. Upstream AI: [bluesam1/calibre-web-ai](https://github.com/bluesam1/calibre-web-ai).

Calibre-Web is a web app that offers a clean and intuitive interface for browsing, reading, and downloading eBooks using a valid [Calibre](https://calibre-ebook.com) database.

[![License](https://img.shields.io/github/license/janeczku/calibre-web?style=flat-square)](https://github.com/janeczku/calibre-web/blob/master/LICENSE)
![Commit Activity](https://img.shields.io/github/commit-activity/w/janeczku/calibre-web?logo=github&style=flat-square&label=commits)
[![All Releases](https://img.shields.io/github/downloads/janeczku/calibre-web/total?logo=github&style=flat-square)](https://github.com/janeczku/calibre-web/releases)
[![PyPI](https://img.shields.io/pypi/v/calibreweb?logo=pypi&logoColor=fff&style=flat-square)](https://pypi.org/project/calibreweb/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/calibreweb?logo=pypi&logoColor=fff&style=flat-square)](https://pypi.org/project/calibreweb/)
[![Discord](https://img.shields.io/discord/838810113564344381?label=Discord&logo=discord&style=flat-square)](https://discord.gg/h2VsJ2NEfB)

<details>
<summary><strong>Table of Contents</strong> (click to expand)</summary>

1. [About](#calibre-web)
2. [Features](#features)
3. [AI Features](#ai-features)
   - [AI Summary Generation](#ai-summary-generation)
   - [AI Semantic Search](#ai-semantic-search)
   - [Full Book Indexing](#full-book-indexing)
   - [Book Chatbot](#book-chatbot)
   - [Supported AI Providers](#supported-ai-providers)
4. [Installation](#installation)
   - [Installation via pip (recommended)](#installation-via-pip-recommended)
   - [Quick start](#quick-start)
   - [Requirements](#requirements)
5. [Docker Images](#docker-images)
6. [Troubleshooting](#troubleshooting)
7. [Contributor Recognition](#contributor-recognition)
8. [Contact](#contact)
9. [Contributing to Calibre-Web](#contributing-to-calibre-web)

</details>

*This software is a fork of [library](https://github.com/mutschler/calibreserver) and licensed under the GPL v3 License.*

![Main screen](https://github.com/janeczku/calibre-web/wiki/images/main_screen.png)

## Features

- Modern and responsive Bootstrap 3 HTML5 interface
- Full graphical setup
- Comprehensive user management with fine-grained per-user permissions
- Admin interface
- Multilingual user interface supporting 20+ languages ([supported languages](https://github.com/janeczku/calibre-web/wiki/Translation-Status))
- OPDS feed for eBook reader apps
- Advanced search and filtering options
- Custom book collection (shelves) creation
- eBook metadata editing and deletion support
- Metadata download from various sources (extensible via plugins)
- eBook conversion through Calibre binaries
- eBook download restriction to logged-in users
- Public user registration support
- Send eBooks to E-Readers with a single click
- Sync Kobo devices with your Calibre library
- In-browser eBook reading support for multiple formats
- Upload new books in various formats, including audio formats
- Calibre Custom Columns support
- Content hiding based on categories and Custom Column content per user
- Self-update capability
- "Magic Link" login for easy access on eReaders
- LDAP, Google/GitHub OAuth, and proxy authentication support

## AI Features

Calibre-Web includes powerful AI-powered features to enhance your library experience. All AI features are optional and can be enabled/configured in **Admin → AI Settings**.

### AI Summary Generation
Automatically generate concise summaries for your books using AI:
- One-click summary generation from the book detail page
- Summaries are stored and displayed alongside book metadata
- Supports regeneration to update summaries with different models

### AI Semantic Search
Search your library using natural language queries:
- Find books by meaning, not just keywords
- Toggle between traditional search and AI-powered semantic search
- Results ranked by semantic similarity to your query
- Automatically generates embeddings from book summaries

### Full Book Indexing
Index entire book contents for deep search capabilities:
- Chunks books into semantic segments (~500 tokens each)
- Generates embeddings for each chunk
- Enables searching within book passages and chapters
- Progress tracking for long indexing operations
- Optional auto-indexing when summaries are generated

### Book Chatbot
Ask questions about your books and get AI-powered answers:
- Conversational Q&A interface on book detail pages
- RAG (Retrieval-Augmented Generation) architecture
- Answers are grounded in actual book content
- Maintains chat history for context-aware conversations
- Configurable similarity thresholds and context limits

### Supported AI Providers
- **OpenAI** - GPT-4o, GPT-4o-mini, text-embedding-3-small, etc.
- **Anthropic** - Claude 3 Haiku, Claude 3 Sonnet, etc.
- **Ollama** - Local/self-hosted models (Llama, Mistral, etc.)

### AI Configuration Options
| Setting | Description | Default |
|---------|-------------|---------|
| LLM Model | Model for text generation | gpt-4o-mini |
| Embedding Model | Model for vector embeddings | text-embedding-3-small |
| Max Summary Tokens | Maximum length of generated summaries | 500 |
| Chunk Size | Tokens per chunk for full indexing | 500 |
| Chunk Overlap | Overlap between chunks for context | 50 |
| Max Chunks per Book | Safety limit for large books | 5000 |
| Chatbot Chunks Limit | Context chunks for chatbot answers | 5 |
| Similarity Threshold | Minimum relevance score for results | 0.3 |

## Installation

### Installation via pip (recommended)

1. **Create a virtual environment**: It’s essential to isolate your Calibre-Web installation to avoid dependency conflicts. You can create a virtual environment by running:
   ```
   python3 -m venv calibre-web-env
   ```
2. **Activate the virtual environment**:
   ```
   source calibre-web-env/bin/activate
   ```
3. **Install Calibre-Web**: Use pip to install the application:
   ```
   pip install calibreweb
   ```
4. **Install optional features**: For additional functionality, you may need to install optional features. Refer to [this page](https://github.com/janeczku/calibre-web/wiki/Dependencies-in-Calibre-Web-Linux-and-Windows) for details on what can be installed.
5. **Start Calibre-Web**: After installation, you can start the application with:
   ```
   cps
   ```

*Note: Users of Raspberry Pi OS may encounter installation issues. If you do, try upgrading pip and/or installing cargo as follows:*
   ```
   ./venv/bin/python3 -m pip install --upgrade pip
   sudo apt install cargo
   ```

### Important Links
- For additional installation examples, check the following:
   - [Manual installation](https://github.com/janeczku/calibre-web/wiki/Manual-installation)
   - [Linux Mint installation](https://github.com/janeczku/calibre-web/wiki/How-To:-Install-Calibre-Web-in-Linux-Mint-19-or-20)
   - [Cloud Provider setup](https://github.com/janeczku/calibre-web/wiki/How-To:-Install-Calibre-Web-on-a-Cloud-Provider)

## Quick Start

1. **Access Calibre-Web**: Open your browser and navigate to:
   ```
   http://localhost:8083
   ```
   or for the OPDS catalog:
   ```
   http://localhost:8083/opds
   ```
2. **Log in**: Use the default admin credentials:
   - **Username:** admin
   - **Password:** admin123
3. **Database Setup**: If you do not have a Calibre database, download a sample from:
   ```
   https://github.com/janeczku/calibre-web/raw/master/library/metadata.db
   ```
   Move it out of the Calibre-Web folder to avoid overwriting during updates.
4. **Configure Calibre Database**: In the admin interface, set the `Location of Calibre database` to the path of the folder containing your Calibre library (where `metadata.db` is located) and click "Save".
5. **Google Drive Integration**: For hosting your Calibre library on Google Drive, refer to the [Google Drive integration guide](https://github.com/janeczku/calibre-web/wiki/G-Drive-Setup#using-google-drive-integration).
6. **Admin Configuration**: Configure your instance via the admin page, referring to the [Basic Configuration](https://github.com/janeczku/calibre-web/wiki/Configuration#basic-configuration) and [UI Configuration](https://github.com/janeczku/calibre-web/wiki/Configuration#ui-configuration) guides.

## Requirements

- **Python Version**: Ensure you have Python 3.7 or newer.
- **Imagemagick**: Required for cover extraction from EPUBs. Windows users may also need to install [Ghostscript](https://ghostscript.com/releases/gsdnld.html) for PDF cover extraction.
- **Optional Tools**:
   - **Calibre desktop program**: Recommended for on-the-fly conversion and metadata editing. Set the path to Calibre’s converter tool on the setup page.
   - **Kepubify tool**: Needed for Kobo device support. Download the tool and place the binary in `/opt/kepubify` on Linux or `C:\Program Files\kepubify` on Windows.

## Docker Images

Pre-built Docker images are available:

### **LinuxServer - x64, aarch64**
- **Docker Hub**: [linuxserver/calibre-web](https://hub.docker.com/r/linuxserver/calibre-web)
- **GitHub**: [linuxserver/docker-calibre-web](https://github.com/linuxserver/docker-calibre-web)
- **Optional Calibre layer**: [linuxserver/docker-mods](https://github.com/linuxserver/docker-mods/tree/universal-calibre)

To include the Calibre `ebook-convert` binary (x64 only), add the environment variable:
``` 
DOCKER_MODS=linuxserver/mods:universal-calibre
```
in your Docker run/compose file. Omit this variable for a lightweight image.

- **Paths Configuration**:
   - Set **Path to Calibre Binaries** to `/usr/bin`.
   - Set **Path to Unrar** to `/usr/bin/unrar`.

## Troubleshooting

- **Common Issues**: 
   - If you experience issues starting the application, check the log files located in the `logs` directory for error messages.
   - If eBooks fail to load, verify that the `Location of Calibre database` is correctly set and that the database file is accessible.

- **Configuration Errors**: Ensure that your Calibre database is compatible and properly formatted. Refer to the Calibre documentation for guidance on maintaining the database.

- **Performance Problems**: 
   - If the application is slow, consider increasing the allocated resources (CPU/RAM) to your server or optimizing the Calibre database by removing duplicates and unnecessary entries.
   - Regularly clear the cache in your web browser to improve loading times.

- **User Management Issues**: If users are unable to log in or register, check the user permission settings in the admin interface. Ensure that registration is enabled and that users are being assigned appropriate roles.

- **Support Resources**: For additional help, consider visiting the [FAQ section](https://github.com/janeczku/calibre-web/wiki/FAQ) of the wiki or posting your questions in the [Discord community](https://discord.gg/h2VsJ2NEfB).

## Contributor Recognition

We would like to thank all the [contributors](https://github.com/janeczku/calibre-web/graphs/contributors) and maintainers of Calibre-Web for their valuable input and dedication to the project. Your contributions are greatly appreciated.

## Contact

Join us on [Discord](https://discord.gg/h2VsJ2NEfB)

For more information, How To's, and FAQs, please visit the [Wiki](https://github.com/janeczku/calibre-web/wiki)

## Contributing to Calibre-Web

To contribute, please check our [Contributing Guidelines](https://github.com/janeczku/calibre-web/blob/master/CONTRIBUTING.md). We welcome issues, feature requests, and pull requests from the community.

### Reporting Bugs

If you encounter bugs or issues, please report them in the [issues section](https://github.com/janeczku/calibre-web/issues) of the repository. Be sure to include detailed information about your setup and the problem encountered.

### Feature Requests

We welcome suggestions for new features. Please create a new issue in the repository to discuss your ideas.

## Additional Resources

- **Documentation**: Comprehensive documentation is available on the [Calibre-Web wiki](https://github.com/janeczku/calibre-web/wiki).
- **Community Contributions**: Explore the [community contributions](https://github.com/janeczku/calibre-web/pulls) to see ongoing work and how you can get involved.

---

Thank you for using Calibre-Web! We hope you enjoy managing your eBook library with our tool.

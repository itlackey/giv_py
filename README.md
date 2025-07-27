# giv_cli – Python Port of the `giv` Bash CLI

`giv_cli` is a Python rewrite of the original Bash–based [giv](https://github.com/giv-cli/giv) command line tool.  The Bash project provides a rich set of commands for generating AI‑assisted commit messages, change summaries and release artefacts by analysing your Git history.  This port preserves the high level behaviour of the Bash version while adopting idiomatic Python patterns and a modern development workflow.

## Features

- **Command line interface** – The `giv` executable exposes subcommands such as `message`, `summary`, `document`, `config`, `init` and `version`.  Options closely mirror those from the original argument parser defined in `argument_parser.sh`【410229712243769†L22-L47】.  Global flags like `--verbose` and `--dry-run` are supported.
- **Configuration management** – Key–value pairs are persisted in a `.giv/config` file either in your project or under `~/.giv/config`.  The `config` subcommand implements `list`, `get`, `set` and `unset` operations analogous to those in the Bash script【366625523340174†L69-L87】.
- **Git integration** – The tool shells out to `git diff` to assemble the diff for a revision range or the working tree.  When the `--dry-run` flag is used the generated prompt is printed instead of calling an API.
- **Prompt templates** – Markdown templates from the original project (e.g. `message_prompt.md`, `summary_prompt.md`) have been copied verbatim.  Placeholders such as `[SUMMARY]` and `[PROJECT_TITLE]` are replaced with contextual data before invoking the language model【724309362603056†L9-L30】.
- **Language model client** – A small client wraps calls to an external API.  If no API URL is configured, the tool echoes the generated prompt, which makes it easy to inspect prompts and run tests without network access.  When configured, it sends a JSON payload containing the prompt and model name to the remote service.
- **Project metadata** – The code attempts to infer the project title and version from `pyproject.toml` or `package.json`, falling back to the directory name when unavailable.
- **Cross platform builds** – A GitHub Actions workflow and a PyInstaller configuration are provided.  Running the workflow will build standalone binaries for Linux, macOS and Windows.  Artifacts are archived automatically after a successful build.
- **Tests** – Tests have been converted from Bats to `pytest` and exercise the configuration layer, basic CLI flags and the dry‑run behaviour of the `message` command.

## Getting Started

This project uses [Poetry](https://python-poetry.org/) for dependency management and packaging.  After cloning the repository, install dependencies and run the CLI directly from the virtual environment:

```bash
# Install Poetry and project dependencies
python -m pip install --upgrade pip
pip install poetry
poetry install --no-root

# Run the CLI
poetry run giv --help
```

Alternatively you can install the package in editable mode and call the entry point:

```bash
pip install -e .
giv message --dry-run
```

### Configuration

Configuration values are stored in a simple INI‑style file located in `.giv/config` within your project, or in `~/.giv/config` if the project file does not exist.  Use the following commands to manage configuration:

- `giv config list` – show all keys and values
- `giv config get <key>` – print the value for `key`
- `giv config set <key> <value>` – set `key` to `value`
- `giv config unset <key>` – remove `key` from the config

### Generating a commit message

Run the `message` subcommand in a Git repository to generate a commit message.  With `--dry-run` the generated prompt is printed instead of calling any API:

```bash
giv message --dry-run
```

To generate an actual message using a remote model, configure the API endpoint and key via the config or flags:

```bash
giv config set api_url https://example.com/v1/chat/completions
giv config set api_key YOUR_API_KEY
giv message --revision HEAD~1..HEAD
```

### Creating summaries and documents

The `summary` and `document` subcommands work similarly to `message` but use different templates.  They produce high‑level summaries of your changes, grouped by type and formatted according to Keep a Changelog conventions【422196817908543†L12-L30】.

### Initialising a project

Running `giv init` creates a `.giv` directory in your repository and copies the default prompt templates into it.  You can customise these templates to suit your team’s workflow.

## Development

### Running tests

Tests are written with `pytest`.  Install development dependencies and run:

```bash
poetry install --no-root
poetry run pytest -q
```

### Building executables

The repository includes a GitHub Actions workflow that builds standalone binaries with [PyInstaller](https://pyinstaller.org/).  To build locally you can run:

```bash
pip install pyinstaller
pyinstaller --name giv --onefile giv_cli/main.py
```

The resulting executable will be placed in the `dist/` directory.

## How the port was accomplished

The Bash implementation of `giv` consists of dozens of small scripts orchestrated via a single `giv.sh` dispatcher.  Each subcommand is implemented in its own file and relies on shared library functions for argument parsing, project detection, Git history extraction, markdown processing and API communication.  To port this tool to Python:

1. **Studying the original scripts** – The contents of `argument_parser.sh` were reviewed to enumerate global options and subcommands【410229712243769†L22-L47】.  Configuration handling in `config.sh` was studied to replicate normalisation and key quoting logic【366625523340174†L106-L167】.  The markdown templates used by the AI prompts were copied verbatim from the `templates` directory【724309362603056†L9-L30】【422196817908543†L12-L30】.
2. **Designing a Python module** – A Python package `giv_cli` was created with modules for configuration (`config.py`), Git integration (`git_utils.py`), language model client (`llm_utils.py`), markdown processing (`markdown_utils.py`), and project metadata (`project_metadata.py`).  The command line interface is defined in `cli.py` using `argparse`; it exposes subcommands and global options similar to the Bash version.  The top level entry point lives in `main.py`.
3. **Preserving behaviour** – The `ConfigManager` reads and writes key–value pairs to a file and falls back to `~/.giv/config` when a project file is absent.  `GitHistory` shells out to `git diff` and `git log` via `subprocess.run`, returning empty strings on failure so that the user sees only the template if Git is unavailable.  The `LLMClient` accepts an API URL, key and model and makes a `POST` request to the endpoint; if no API is configured it simply echoes the generated prompt.
4. **Copying templates** – All prompt templates (`message_prompt.md`, `summary_prompt.md`, `final_summary_prompt.md`, `changelog_prompt.md`, `release_notes_prompt.md`, `announcement_prompt.md`) were copied into the `giv_cli/templates` directory.  The placeholders `[SUMMARY]`, `[PROJECT_TITLE]`, `[VERSION]`, etc., are replaced in Python before sending the prompt to the language model.
5. **Testing and tooling** – The original Bats tests were replaced with a small suite of `pytest` tests covering the configuration manager and basic CLI flags.  A `pyproject.toml` file defines dependencies and entry points.  A GitHub Actions workflow runs tests and builds platform–specific executables using PyInstaller.

The result is a portable, testable Python CLI that retains the spirit and core functionality of the original Bash implementation while making it easier to extend and maintain.
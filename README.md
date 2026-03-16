# Bonsai
![CI](https://github.com/BeckettFrey/Bonsai/actions/workflows/test.yml/badge.svg)

**bonsai** is a lightweight Python command-line utility that elegantly displays directory structures while respecting .gitignore patterns. It's perfect for AI-assisted workflows — filtering out clutter to reveal only the meaningful parts of your project for language models, code analysis, or team reviews.

> **Experimental**: Install in development mode and use at your own discretion.

---

## Why Bonsai?

Bonsai filters your file tree just like Git does, producing a minimalist view of the meaningful source structure. This is invaluable for:

- Providing context to AI assistants (codegen, review, summarization)
- Documentation or onboarding diagrams
- CI checks on directory structure
- Quickly exploring unfamiliar codebases

---

## Installation

Install Bonsai using pipx for standard usage:

```bash
pipx install git+https://github.com/BeckettFrey/Bonsai.git
```

Or for active development pip is fine:

```bash
git clone https://github.com/BeckettFrey/Bonsai.git
cd Bonsai
pip install -e .
```

---

## Quick Start

```bash
bonsai [path] [options]
```

---

If no path is provided, Bonsai defaults to the current directory.

### Examples

```bash
# Display current directory tree, respecting .gitignore
bonsai

# Show a specific directory with depth limit
bonsai /path/to/project --max-depth 3

# Include hidden files and disable .gitignore filtering
bonsai . --show-hidden --no-gitignore

# Output as JSON for tooling or further processing
bonsai --format json
```

---

## Options

| Option | Description |
|--------|-------------|
| `-d, --max-depth` | Maximum recursion depth |
| `-a, --show-hidden` | Show hidden files/directories |
| `-i, --icons` | Show icons based on file type |
| `-s, --size` | Show file sizes |
| `--no-color` | Disable colored output |
| `--no-gitignore` | Ignore .gitignore rules |
| `--ignore PATTERN` | Additional ignore pattern (can be used multiple times) |
| `--include PATTERN` | Force include pattern (can be used multiple times) |
| `-o, --output` | Write output to file instead of stdout |
| `-f, --format` | Output format: tree (default) or json |
| `--version` | Show version and exit |

---

## Example Workflow

```bash
❯ bonsai src/ --max-depth 2 --icons --size
📁 src/
├── 🐍 app.py (4.5KB)
├── 📁 components/
│   ├── 📜 header.js (2.1KB)
│   └── 📜 footer.js (1.8KB)
└── 📁 utils/
    └── 📜 helpers.py (3.2KB)
```

Or programmatically:

```bash
❯ bonsai --format json | jq
{
  "name": "src",
  "path": "/absolute/path/to/src",
  "is_dir": true,
  "children": [...]
}
```

---

## Ignore & Include Patterns

Respects .gitignore by default, matching exactly what Git tracks.

Add patterns dynamically with `--ignore` or override with `--include`.

```bash
bonsai --ignore "*.log" --include "!important.log"
```

Customize global patterns in config.json for persistent project-level tweaks.

---

## Configuration

Located at:

```
src/bonsai/config.json
```

Controls:

- Supported file type icons
- Default ignore patterns
- Display options like color themes (future roadmap)

Edit this file to adapt Bonsai to your organization's needs.

---

## Roadmap

Planned enhancements for Bonsai:

- Add YAML output support
- Inline directory statistics summary (file count, size)
- VS Code extension for inline visualization
- CI guardrails for tree shape validation

---

## Testing & Development

Clone the repo and run tests with:

```bash
git clone https://github.com/BeckettFrey/Bonsai.git
cd Bonsai
pip install -e .
pytest
```

🔍 Tests are organized under `tests/` by integration and unit.

---

## License

MIT License. See LICENSE for details.

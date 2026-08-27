# Assignment 3 · Coding - RAG

This project has two main workflows:

1. Embed a DOCX file into Chroma once.
2. Ask questions from the persisted vector store.

## Setup

Activate the local virtual environment and make sure your OpenAI API key is set.

macOS / Linux:

```bash
cd '/Users/barsasson/Documents/Academics/final asingment/Assignment 3 · Coding -RAG'
source .venv/bin/activate
export OPENAI_API_KEY="sk-..."
```

Windows PowerShell:

```powershell
cd 'C:\Users\<you>\Documents\Academics\final asingment\Assignment 3 · Coding -RAG'
.\.venv\Scripts\Activate.ps1
$env:OPENAI_API_KEY = 'sk-...'
```

Windows Command Prompt:

```cmd
cd "C:\Users\<you>\Documents\Academics\final asingment\Assignment 3 · Coding -RAG"
.\.venv\Scripts\activate.bat
set OPENAI_API_KEY=sk-...
```

> On macOS or Linux, add `export OPENAI_API_KEY="sk-..."` to `~/.zshrc` or `~/.bashrc` for permanent access.
> On Windows PowerShell, add `$env:OPENAI_API_KEY = 'sk-...'` to your PowerShell profile for permanent access.

## Embed the DOCX file

This command loads the DOCX, splits it into book-level sections, then chunks and embeds those sections before persisting the Chroma database:

```bash
./.venv/bin/python main.py load otkjb.docx
```

If your document has a different filename:

```bash
./.venv/bin/python main.py load path/to/your-document.docx
```

## Ask a specific question

Run a single question against the already persisted vector store:

```bash
./.venv/bin/python main.py ask "What is the main topic of this document?"
```

## Ask all default questions

Run the built-in question list from `main.py`:

```bash
./.venv/bin/python main.py ask
```

## Notes

- Only run `load` again if the DOCX file changes or you want to rebuild the vector store.
- `ask` uses the existing persisted vector store and does not re-embed the document.
- If the persisted directory is missing, run `load` first.

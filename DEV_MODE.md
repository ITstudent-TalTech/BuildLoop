# Dev Mode: Codex + IDE + Live Preview

## Recommended setup

- **IDE:** VS Code (best balance of Git visibility, integrated terminal, and extensions).
- **AI pair workflow:** keep Codex running in terminal + edit/inspect in VS Code.
- **Live preview:** use FastAPI autoreload now; add a frontend dev server later.

## Why this setup

- You can watch file changes instantly in Source Control.
- You can review diffs per file while Codex writes code.
- You can keep a split view: terminal logs + editor + browser preview.

## Practical run loop

1. Open repo in VS Code.
2. In terminal A, run backend:

```bash
uvicorn app.main:app --reload
```

3. In terminal B, run Codex tasks / git commands.
4. Open preview in browser:

```text
http://127.0.0.1:8000/v1/health
```

## Minimal monitoring checklist

- keep `git status` visible
- review diffs before each commit
- run quick sanity checks (`compileall`, API import, health endpoint)

## Optional next step (when UI starts)

If you add a web UI (e.g., Next.js), run it on a second port and keep both backend+frontend in split terminals.

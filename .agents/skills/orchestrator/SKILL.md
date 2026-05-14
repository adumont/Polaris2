---
name: orchestrator
description: >
  Multi-agent parallel task orchestration using git worktrees.
  Three-phase workflow: Plan (analyze issues) → Execute (parallel agents in worktrees) → Integrate + Cleanup.
  Use when you have multiple independent (or partially dependent) issues to solve concurrently.
---

# Orchestrator Skill

Coordinates multiple parallel agents across git worktrees to solve independent issues concurrently.

## Workflow

```
Phase 1 — Plan        (N parallel agents, read-only analysis)
Phase 1.5 — Infra     (1 agent: create worktrees + env)
Phase 2 — Execute     (N agents in worktrees, per DAG order)
Phase 3 — Review      (coordinator, sequential per branch)
Phase 4 — Integrate   (1 agent: merge into session branch)
Phase 5 — Cleanup     (1 agent: remove worktrees)
```

## Phase Details

### Phase 1 — Issue Analysis (N parallel subagents)

Each agent gets one issue + read-only codebase access.

**Input:** issue description  
**Output:** `{ files_touched: [...], module: "...", complexity: "S/M/L", notes: "..." }`

Coordinator collects all outputs → builds file conflict matrix + dependency DAG.

### Phase 1.5 — Worktree & Env Prep (1 subagent)

Uses `scripts/manage_worktrees.py setup`:

```
python .agents\skills\orchestrator\scripts\manage_worktrees.py setup ^
    --session 2026-05-12-my-session ^
    feature-a feature-b feature-c
```

Repo root is auto-detected from cwd. Override with `--repo-root <path>` if needed.

Worktree path convention: `.worktrees/<session>/<name>` (relative to repo root)

Session name isolates concurrent orchestration runs — no collision between `2026-05-12-fix-bugs` and `2026-05-12-refactor`.

**What the script does per feature:**
1. Pre-flight validation: checks `git`, `uv`, `python` available; repo is clean
2. Checks if branch already exists locally (handles re-runs after cleanup where branches survive)
   - Branch exists → `git worktree add <path> <existing-branch>` (re-attach)
   - No branch → `git worktree add -b feature/<name> <path> HEAD` (create + attach)
3. Copies `.env` from repo root to worktree (if exists)
4. Runs `uv sync --quiet` in the worktree

**"Fails early":** Stop all worktrees on first failure, report error.

**Rollback:** If worktree 4/5 fails during setup, previously created worktrees (1-3) are automatically removed to prevent dangling state.

### Phase 2 — Execution (N subagents, start order per DAG)

Each agent gets:

| Item | Description |
|------|-------------|
| Worktree path | Exists, clean, has `.env`, has `.venv` |
| Branch | `feature/<name>` |
| Issue text | Full description |
| Preliminary file list | From Phase 1 — **marked preliminary** (agent may discover more) |
| Plan pointers | Approach notes from Phase 1 analyst |
| Coding guidelines (MANDATORY) | See below |
| Acceptance criteria | Test commands to verify |

**Coding guidelines (every exec agent must follow):**
- Follow existing code conventions (models, imports, patterns, typings, etc.)
- Sanity check: use /review scoped to your changes to get a review of your changes before you run tests 
- Run `uv run ruff check --fix . && uv run ruff format` — zero errors target
- Run `uv run pytest tests/ -v` — all existing tests pass
- Maintain coverage: ≥90% overall, ≥80% per file (no exclusions)
- No debug artifacts, no commented-out code, no secrets committed
- Commit cleanly to `feature/<name>` in their worktree.

**Start order per DAG:**
- Coordinator starts all parallel-safe tasks simultaneously
- Tasks with dependencies wait — launched only after dependency branch is merged into session branch

### Phase 3 — Review (Coordinator, sequential per branch)

For each completed branch in dependency order:
1. `git diff main...feature/<name>` — inspect changes
2. Run: `uv run ruff check --fix . && uv run ruff format && uv run pytest tests/ -v`
3. Verify: matches issue scope, no regressions, no debug artifacts

**Triage:**
- **Clean** → mark ready for merge
- **Minor issues** (typo, style, small refactor) → coordinator fixes directly in the branch
- **Major issues** (wrong approach, logic errors, broken tests) → coordinator writes fix-notes, sends back to same exec agent (worktree still exists), re-enters Phase 2 for that branch only

### Phase 4 — Integration (1 subagent or coordinator)

Create a session branch from main:
```
git checkout main
git checkout -b session/YYYY-MM-DD-<session-name>
```

For each approved branch in dependency order:
```
git merge feature/<name> --no-ff
```
Resolve conflicts. Session branch accumulates all features.

**Integration intertwines with Phase 2:**
Once branch A is merged into session, branch B (which depends on A) can start its exec agent — it rebases onto session and proceeds.

### Phase 5 — Cleanup (1 subagent)

Uses `scripts/manage_worktrees.py cleanup`:

```
python .agents\skills\orchestrator\scripts\manage_worktrees.py cleanup ^
    --session 2026-05-12-my-session ^
    [--force] ^
    feature-a feature-b feature-c
```

`--session` is required to locate worktrees (since path includes session name).
`--force` passes `--force` to `git worktree remove`, allowing cleanup of dirty worktrees.

Removes each worktree. Branches survive (`git branch --list 'feature/*'`). Session branch remains in repo.

## Worktree Script

See `scripts/manage_worktrees.py` — handles setup, cleanup, and status.

```
Usage:
  setup:   python manage_worktrees.py setup --session <name> [--repo-root <path>] <features...>
  cleanup: python manage_worktrees.py cleanup --session <name> [--repo-root <path>] [--force] <features...>
  status:  python manage_worktrees.py status [--repo-root <path>]
```

Repo root auto-detected from cwd; `--repo-root` only needed when running outside the repo.

The **`status`** subcommand lists all sessions and worktrees for a repo, showing which are dirty. Useful for checking state before cleanup or spotting dangling worktrees.

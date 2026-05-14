"""
Phase 1.5 + 5: Worktree setup and cleanup for parallel feature development.

Repo root is auto-detected from cwd. Override with --repo-root if needed.

Usage:
    # Setup: create worktrees + env for feature branches
    python manage_worktrees.py setup --session <name> <features...>

    # Cleanup: remove worktrees (branches survive)
    python manage_worktrees.py cleanup --session <name> [--force] <features...>

    # Status: list worktrees and their state
    python manage_worktrees.py status

Examples:
    python manage_worktrees.py setup ^
        --session 2026-05-12-fix-bugs ^
        fix-auth add-tests refactor-cli

    python manage_worktrees.py cleanup ^
        --session 2026-05-12-fix-bugs ^
        --force ^
        fix-auth add-tests refactor-cli

    python manage_worktrees.py status
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd, cwd=None, silent=False, check=True):
    resolved = [shutil.which(cmd[0]) or cmd[0], *cmd[1:]]
    result = subprocess.run(resolved, cwd=cwd, capture_output=True, text=True, check=False)  # noqa: S603
    if result.returncode != 0:
        print(f"ERROR: {' '.join(str(c) for c in cmd)} failed (code {result.returncode})")
        if result.stderr.strip():
            print(result.stderr.strip())
        if check:
            sys.exit(1)
    if not silent and result.stdout.strip():
        print(result.stdout.strip())
    return result


def resolve_repo_root(path=None):
    start = path.resolve() if path else Path.cwd().resolve()
    for parent in [start, *start.parents]:
        if (parent / ".git").exists() or (parent / ".git").is_dir():
            return parent
    print("ERROR: Not inside a git repository (no .git found)")
    sys.exit(1)


def resolve_worktree_paths(repo_root, session, features):
    repo_root = repo_root.resolve()
    worktrees_dir = repo_root / ".worktrees" / session
    return [(f"feature/{name}", worktrees_dir / name) for name in features]


def preflight_check(repo_root, silent=False):
    errors = []
    for binary in ["git", "uv", "python"]:
        if shutil.which(binary) is None:
            errors.append(f"Required binary not found: {binary}")
    if errors:
        for e in errors:
            print(f"ERROR: {e}")
        sys.exit(1)

    result = run(["git", "status", "--porcelain"], cwd=str(repo_root), silent=True, check=False)
    if result.returncode != 0:
        print("ERROR: Failed to check git status")
        sys.exit(1)
    if result.stdout.strip():
        print("ERROR: Repository has uncommitted changes. Commit or stash before setting up worktrees.")
        print(result.stdout.strip()[:500])
        sys.exit(1)

    print("Pre-flight checks passed: git, uv, python available, repo clean")
    print()


def branch_exists(repo_root, branch, silent=False):
    result = run(["git", "rev-parse", "--verify", branch], cwd=str(repo_root), silent=True, check=False)
    return result.returncode == 0


def cmd_setup(args):
    repo_root = resolve_repo_root(args.repo_root)
    preflight_check(repo_root, silent=args.silent)

    branches = resolve_worktree_paths(repo_root, args.session, args.features)
    print(f"Setting up {len(branches)} worktrees for session: {args.session}")
    print(f"Repo root: {repo_root}")
    print()

    created_worktrees = []

    try:
        for branch, worktree_path in branches:
            print(f"[{branch}]")
            print(f"  Worktree: {worktree_path}")

            worktree_path.parent.mkdir(parents=True, exist_ok=True)

            if branch_exists(repo_root, branch, silent=args.silent):
                print(f"  Branch exists (re-attaching worktree): {branch}")
                run(
                    ["git", "worktree", "add", str(worktree_path), branch],
                    cwd=str(repo_root),
                    silent=args.silent,
                )
            else:
                run(
                    ["git", "worktree", "add", "-b", branch, str(worktree_path), "HEAD"],
                    cwd=str(repo_root),
                    silent=args.silent,
                )
                print(f"  Branch created: {branch}")
            created_worktrees.append((branch, worktree_path))

            env_src = repo_root / ".env"
            if env_src.exists():
                shutil.copy2(env_src, worktree_path / ".env")
                print("  .env copied")

            print("  uv sync...")
            uv_cmd = ["uv", "sync"]
            if args.silent:
                uv_cmd.append("--quiet")
            run(uv_cmd, cwd=str(worktree_path), silent=args.silent)
            print("  uv sync done")

            print()
    except SystemExit:
        print(f"\nERROR: Setup failed. Rolling back {len(created_worktrees)} created worktrees...")
        for branch, worktree_path in created_worktrees:
            if worktree_path.exists():
                run(
                    ["git", "worktree", "remove", "--force", str(worktree_path)],
                    cwd=str(repo_root),
                    silent=args.silent,
                    check=False,
                )
                print(f"  Removed: {worktree_path}  ({branch})")
        print("Rollback complete.")
        sys.exit(1)

    print(f"All {len(branches)} worktrees ready:")
    for branch, worktree_path in branches:
        print(f"  {worktree_path}  ({branch})")
    print()


def cmd_cleanup(args):
    repo_root = resolve_repo_root(args.repo_root)
    branches = resolve_worktree_paths(repo_root, args.session, args.features)

    print(f"Removing {len(branches)} worktrees...")
    print()

    for branch, worktree_path in branches:
        if worktree_path.exists():
            print(f"  Removing: {worktree_path}  ({branch})")
            cmd = ["git", "worktree", "remove", str(worktree_path)]
            if args.force:
                cmd.append("--force")
            run(cmd, cwd=str(repo_root), silent=args.silent, check=False)
        else:
            print(f"  Skipping (not found): {worktree_path}")

    result = run(
        ["git", "branch", "--list", "feature/*"],
        cwd=str(repo_root),
        silent=True,
        check=False,
    )
    branches_alive = [b.strip() for b in result.stdout.strip().split("\n") if b.strip()]
    if branches_alive:
        print(f"\n  Branches intact in repo ({len(branches_alive)}):")
        for b in branches_alive:
            print(f"    {b}")

    print("\nCleanup complete. Session branch remains in repo.")


def cmd_status(args):
    repo_root = resolve_repo_root(args.repo_root)
    worktrees_base = repo_root / ".worktrees"

    if not worktrees_base.exists():
        print(f"No worktrees found for {repo_root.name}")
        return

    sessions = sorted(s for s in worktrees_base.iterdir() if s.is_dir())
    if not sessions:
        print(f"No worktrees found for {repo_root.name}")
        return

    print(f"Worktrees for {repo_root.name}:")
    print()

    for session_dir in sessions:
        features = sorted(f for f in session_dir.iterdir() if f.is_dir())
        if not features:
            continue

        print(f"  Session: {session_dir.name}")
        for f in features:
            branch = f"feature/{f.name}"
            result = run(["git", "status", "--porcelain"], cwd=str(f), silent=True, check=False)
            is_dirty = bool(result.stdout.strip())
            dirty_mark = " [DIRTY]" if is_dirty else ""
            print(f"    {f.name}  ({branch}){dirty_mark}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Manage git worktrees for parallel feature development")
    parser.add_argument("--silent", action="store_true", help="Less verbose output")
    subparsers = parser.add_subparsers(dest="command", required=True)

    setup_parser = subparsers.add_parser("setup", help="Create worktrees + environment")
    setup_parser.add_argument(
        "--repo-root", type=Path, default=None, help="Git repository root (auto-detected from cwd)"
    )
    setup_parser.add_argument("--session", required=True, help="Session name (e.g. 2026-05-12-fix-bugs)")
    setup_parser.add_argument("features", nargs="+", help="Feature names")

    cleanup_parser = subparsers.add_parser("cleanup", help="Remove worktrees (branches survive)")
    cleanup_parser.add_argument(
        "--repo-root", type=Path, default=None, help="Git repository root (auto-detected from cwd)"
    )
    cleanup_parser.add_argument("--session", required=True, help="Session name used during setup")
    cleanup_parser.add_argument("--force", action="store_true", help="Force remove even if dirty")
    cleanup_parser.add_argument("features", nargs="+", help="Feature names")

    status_parser = subparsers.add_parser("status", help="List worktrees and their state")
    status_parser.add_argument(
        "--repo-root", type=Path, default=None, help="Git repository root (auto-detected from cwd)"
    )

    args = parser.parse_args()

    if args.command == "setup":
        cmd_setup(args)
    elif args.command == "cleanup":
        cmd_cleanup(args)
    elif args.command == "status":
        cmd_status(args)


if __name__ == "__main__":
    main()

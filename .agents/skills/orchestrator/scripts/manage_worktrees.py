"""
Phase 1.5 + 5: Worktree setup and cleanup for parallel feature development.

Usage:
    # Setup: create worktrees + env for feature branches
    python manage_worktrees.py setup --repo-root <path> --session <name> <features...>

    # Cleanup: remove worktrees (branches survive)
    python manage_worktrees.py cleanup --repo-root <path> <features...>

Examples:
    python manage_worktrees.py setup ^
        --repo-root C:\\Projects\\Polaris2 ^
        --session 2026-05-12-fix-bugs ^
        fix-auth add-tests refactor-cli

    python manage_worktrees.py cleanup ^
        --repo-root C:\\Projects\\Polaris2 ^
        fix-auth add-tests refactor-cli
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd, cwd=None, silent=False):
    resolved = [shutil.which(cmd[0]) or cmd[0], *cmd[1:]]
    result = subprocess.run(resolved, cwd=cwd, capture_output=True, text=True, check=False)  # noqa: S603
    if result.returncode != 0:
        print(f"ERROR: {' '.join(str(c) for c in cmd)} failed (code {result.returncode})")
        if result.stderr.strip():
            print(result.stderr.strip())
        sys.exit(1)
    if not silent and result.stdout.strip():
        print(result.stdout.strip())


def resolve_worktree_paths(repo_root, features):
    repo_root = repo_root.resolve()
    worktrees_dir = Path.home() / ".worktrees" / repo_root.name
    return [(f"feature/{name}", worktrees_dir / name) for name in features]


def cmd_setup(args):
    repo_root = args.repo_root.resolve()
    if not (repo_root / ".git").exists() and not (repo_root / ".git").is_dir():
        print(f"ERROR: {repo_root} is not a git repository (no .git)")
        sys.exit(1)

    branches = resolve_worktree_paths(repo_root, args.features)
    print(f"Setting up {len(branches)} worktrees for session: {args.session}")
    print(f"Repo root: {repo_root}")
    print()

    for branch, worktree_path in branches:
        print(f"[{branch}]")
        print(f"  Worktree: {worktree_path}")

        worktree_path.parent.mkdir(parents=True, exist_ok=True)

        # git worktree add (fails early on collision)
        run(
            ["git", "worktree", "add", "-b", branch, str(worktree_path), "HEAD"],
            cwd=str(repo_root),
            silent=args.silent,
        )
        print(f"  Branch created: {branch}")

        # Copy .env if exists
        env_src = repo_root / ".env"
        if env_src.exists():
            shutil.copy2(env_src, worktree_path / ".env")
            print("  .env copied")

        # uv sync
        print("  uv sync...")
        uv_cmd = ["uv", "sync"]
        if args.silent:
            uv_cmd.append("--quiet")
        run(uv_cmd, cwd=str(worktree_path), silent=args.silent)
        print("  uv sync done")

        print()

    print(f"All {len(branches)} worktrees ready:")
    for branch, worktree_path in branches:
        print(f"  {worktree_path}  ({branch})")
    print()


def cmd_cleanup(args):
    repo_root = args.repo_root.resolve()
    branches = resolve_worktree_paths(repo_root, args.features)

    print(f"Removing {len(branches)} worktrees...")
    print()

    for branch, worktree_path in branches:
        if worktree_path.exists():
            print(f"  Removing: {worktree_path}  ({branch})")
            run(
                ["git", "worktree", "remove", str(worktree_path)],
                cwd=str(repo_root),
                silent=args.silent,
            )
        else:
            print(f"  Skipping (not found): {worktree_path}")

    # Verify branches survive
    git_exe = shutil.which("git")
    result = subprocess.run(  # noqa: S603
        [git_exe, "branch", "--list", "feature/*"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    branches_alive = [b.strip() for b in result.stdout.strip().split("\n") if b.strip()]
    if branches_alive:
        print(f"\n  Branches intact in repo ({len(branches_alive)}):")
        for b in branches_alive:
            print(f"    {b}")

    print("\nCleanup complete. Session branch remains in repo.")


def main():
    parser = argparse.ArgumentParser(description="Manage git worktrees for parallel feature development")
    parser.add_argument("--silent", action="store_true", help="Less verbose output")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Setup subcommand
    setup_parser = subparsers.add_parser("setup", help="Create worktrees + environment")
    setup_parser.add_argument("--repo-root", type=Path, required=True, help="Git repository root")
    setup_parser.add_argument("--session", required=True, help="Session name (e.g. 2026-05-12-fix-bugs)")
    setup_parser.add_argument("features", nargs="+", help="Feature names")

    # Cleanup subcommand
    cleanup_parser = subparsers.add_parser("cleanup", help="Remove worktrees (branches survive)")
    cleanup_parser.add_argument("--repo-root", type=Path, required=True, help="Git repository root")
    cleanup_parser.add_argument("features", nargs="+", help="Feature names")

    args = parser.parse_args()

    if args.command == "setup":
        cmd_setup(args)
    elif args.command == "cleanup":
        cmd_cleanup(args)


if __name__ == "__main__":
    main()

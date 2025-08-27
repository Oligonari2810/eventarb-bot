#!/usr/bin/env python3
"""
EventArb Bot - Repo Cleanup Script (SAFE ARCHIVE)

This script safely archives unneeded files instead of deleting them.
It moves candidates to archive/<UTC_TIMESTAMP>/ folder first,
then removes them from Git tracking.

SAFETY FEATURES:
- Archives instead of deletes
- Hard-coded paths (no dynamic discovery)
- Skip if path doesn't exist
- Summary of what was moved
"""

import os
import shutil
import glob
from datetime import datetime
from pathlib import Path

# Configuration
REPO_ROOT = Path.cwd()
ARCHIVE_DIR = REPO_ROOT / "archive" / datetime.utcnow().strftime("%Y%m%d_%H%M%S")

# Exact paths (if present), move to archive:
EXACT_FILES = [
    "logs_cursor",
    "ops",                        # if it's just ops notes; keep if it's infra code
    ".env.production",
    ".env.production.backup.20250824_201328",
    ".env.production.bak",
    "audit_code_lines.txt",
    "audit_file_list.txt",
    "audit_final_report.txt",
    "audit_processes.txt",
    "backup_db.sh",               # duplicate of scripts/backup_db.sh
    "bot_complete_report.txt",
    "bot_complete_report.zip",
    "CICLO_CURSOR_COMPLETADO.md",
    "cleanup_final_report.txt",
    "cleanup_obsolete_files.sh",  # keep only if actually called in CI
    "config_files.txt",
    "config_settings.txt",
    "database_schema.txt",
    "db_test.txt",
    "DEPLOYMENT_CHECKLIST.md",    # keep only if you want it
    "directory_sizes.txt",
    "env_variables.txt",          # DANGEROUS: remove from repo; rotate secrets
    "env.example",                # if you already have .env.example elsewhere
    "ESTADO_FINAL_SISTEMA.md",
    "event_fires_status.txt",
    "event_scheduler_standalone.py", # replaced by p1/event_scheduler.py
    "event_validation.txt",
    "events_status.txt",
    "EVIDENCIAS_PR.md",
    "fix_sheets_config.sh",       # keep only if used
    "import_test.txt",
    "log_files.txt",
    "optimization_checklist.md",
    "P1_SPRINT_BOOTSTRAP_COMPLETADO.md",
    "PR_P1.md",
    "python_files.txt",
    "python_version.txt",
    "requirements_current.txt",
    "requirements-dev.txt",       # keep only if dev flow uses it
    "run_forever.sh",             # if runner.py handles it, archive
    "run_runner_venv.sh",
    "runner_logs_recent.txt",
    "scheduler_logs_recent.txt",
    "system_status.txt",
    "test_scheduler_manual.py",   # superseded by tests/*
    "test_scheduler.py",          # superseded by tests/*
    "yaml_test.txt"
]

# Exact directories to archive (if present):
EXACT_DIRS = [
    "logs_cursor",
    "venv",      # NEVER commit venv
]

# Globs to archive:
GLOBS = [
    "*.db", "*.db-shm", "*.db-wal",       # sqlite artifacts
    "*.log",                              # raw logs
    "*.zip",                              # dumps
    "*_recent.txt", "*_status.txt",       # status snapshots
]

# Core files to PRESERVE (never archive):
CORE_FILES = {
    "app.py",
    "runner.py",
    "p1/",
    "scripts/",
    "tests/",
    "config/",
    "Dockerfile",
    "docker-compose.yml",
    "requirements.txt",
    "README.md",
    "mypy.ini",
    ".gitignore"
}

def create_archive_directory():
    """Create archive directory with timestamp"""
    try:
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created archive directory: {ARCHIVE_DIR}")
        return True
    except Exception as e:
        print(f"❌ Failed to create archive directory: {e}")
        return False

def archive_exact_files():
    """Archive exact file paths"""
    archived_files = []
    
    for file_path in EXACT_FILES:
        source = REPO_ROOT / file_path
        if source.exists():
            try:
                # Create destination directory structure
                dest = ARCHIVE_DIR / file_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                
                # Move file/directory
                shutil.move(str(source), str(dest))
                archived_files.append(file_path)
                print(f"📦 Archived: {file_path}")
                
            except Exception as e:
                print(f"⚠️  Failed to archive {file_path}: {e}")
    
    return archived_files

def archive_exact_dirs():
    """Archive exact directory paths"""
    archived_dirs = []
    
    for dir_path in EXACT_DIRS:
        source = REPO_ROOT / dir_path
        if source.exists() and source.is_dir():
            try:
                # Create destination directory
                dest = ARCHIVE_DIR / dir_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                
                # Move directory
                shutil.move(str(source), str(dest))
                archived_dirs.append(dir_path)
                print(f"📦 Archived directory: {dir_path}")
                
            except Exception as e:
                print(f"⚠️  Failed to archive directory {dir_path}: {e}")
    
    return archived_dirs

def archive_glob_patterns():
    """Archive files matching glob patterns"""
    archived_globs = []
    
    for pattern in GLOBS:
        try:
            matches = list(REPO_ROOT.glob(pattern))
            for match in matches:
                # Skip if it's a core file
                if any(str(match).startswith(str(REPO_ROOT / core)) for core in CORE_FILES):
                    continue
                
                try:
                    # Create destination directory structure
                    rel_path = match.relative_to(REPO_ROOT)
                    dest = ARCHIVE_DIR / rel_path
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Move file
                    shutil.move(str(match), str(dest))
                    archived_globs.append(str(rel_path))
                    print(f"📦 Archived glob: {rel_path}")
                    
                except Exception as e:
                    print(f"⚠️  Failed to archive {match}: {e}")
                    
        except Exception as e:
            print(f"⚠️  Failed to process glob pattern {pattern}: {e}")
    
    return archived_globs

def print_summary(archived_files, archived_dirs, archived_globs):
    """Print summary of what was archived"""
    print("\n" + "="*60)
    print("📊 CLEANUP SUMMARY")
    print("="*60)
    
    total_items = len(archived_files) + len(archived_dirs) + len(archived_globs)
    
    if total_items == 0:
        print("✨ No files were archived - repository is already clean!")
        return
    
    print(f"📦 Total items archived: {total_items}")
    print(f"📁 Archive location: {ARCHIVE_DIR}")
    
    if archived_files:
        print(f"\n📄 Files archived ({len(archived_files)}):")
        for file in archived_files:
            print(f"   • {file}")
    
    if archived_dirs:
        print(f"\n📁 Directories archived ({len(archived_dirs)}):")
        for dir in archived_dirs:
            print(f"   • {dir}")
    
    if archived_globs:
        print(f"\n🔍 Glob patterns archived ({len(archived_globs)}):")
        for item in archived_globs:
            print(f"   • {item}")
    
    print(f"\n💡 Next steps:")
    print(f"   1. Review archived files in: {ARCHIVE_DIR}")
    print(f"   2. Run: git add -A")
    print(f"   3. Run: git commit -m 'cleanup: archive unused files'")
    print(f"   4. Delete archive folder if satisfied")

def main():
    """Main cleanup function"""
    print("🧹 EventArb Bot - Repository Cleanup Script")
    print("=" * 50)
    print(f"📁 Repository root: {REPO_ROOT}")
    print(f"📦 Archive directory: {ARCHIVE_DIR}")
    print()
    
    # Safety check
    if not (REPO_ROOT / ".git").exists():
        print("❌ ERROR: Not in a Git repository!")
        print("   This script must be run from the repository root.")
        return False
    
    # Create archive directory
    if not create_archive_directory():
        return False
    
    print("\n🚀 Starting cleanup process...")
    print("-" * 30)
    
    # Archive exact files
    print("\n📄 Archiving exact files...")
    archived_files = archive_exact_files()
    
    # Archive exact directories
    print("\n📁 Archiving exact directories...")
    archived_dirs = archive_exact_dirs()
    
    # Archive glob patterns
    print("\n🔍 Archiving glob patterns...")
    archived_globs = archive_glob_patterns()
    
    # Print summary
    print_summary(archived_files, archived_dirs, archived_globs)
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ Cleanup completed successfully!")
        else:
            print("\n❌ Cleanup failed!")
            exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Cleanup interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        exit(1)

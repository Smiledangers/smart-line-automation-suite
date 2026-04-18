#!/usr/bin/env python
"""
Database backup and restore script.
Supports PostgreSQL backup/restore with compression.
"""
import os
import sys
import subprocess
import argparse
from datetime import datetime
from pathlib import Path

# Configuration
DEFAULT_BACKUP_DIR = "backups"
DEFAULT_RETENTION_DAYS = 7


def get_database_url():
    """Get database URL from environment."""
    return os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/demo_project")


def get_backup_dir():
    """Get or create backup directory."""
    backup_dir = Path(os.getenv("BACKUP_DIR", DEFAULT_BACKUP_DIR))
    backup_dir.mkdir(exist_ok=True)
    return backup_dir


def create_backup(backup_name: str = None) -> str:
    """
    Create a database backup.
    Returns the backup file path.
    """
    db_url = get_database_url()
    backup_dir = get_backup_dir()
    
    # Generate backup name if not provided
    if not backup_name:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}.sql"
    
    backup_path = backup_dir / backup_name
    
    # Extract connection parameters from DATABASE_URL
    # Format: postgresql://user:password@host:port/dbname
    if "@" not in db_url:
        print("Error: Invalid DATABASE_URL format")
        sys.exit(1)
    
    # Build pg_dump command
    # Use environment variable to avoid exposing password in process list
    env = os.environ.copy()
    env["PGPASSWORD"] = db_url.split(":")[-1].split("@")[0].split("//")[-1]
    
    # Extract connection parts
    connection = db_url.replace("postgresql://", "")
    user_host = connection.split("@")
    user = user_host[0].split(":")[0]
    host_port_db = user_host[1].split("/")
    host_port = host_port_db[0].split(":")
    host = host_port[0]
    port = host_port[1] if len(host_port) > 1 else "5432"
    dbname = host_port_db[1].split("?")[0]
    
    cmd = [
        "pg_dump",
        "-h", host,
        "-p", port,
        "-U", user,
        "-F", "c",  # Custom format (compressed)
        "-b",  # Include large objects
        "-v",  # Verbose
        "-f", str(backup_path),
        dbname,
    ]
    
    print(f"Creating backup: {backup_path}")
    print(f"Database: {dbname}@{host}:{port}")
    
    try:
        result = subprocess.run(
            cmd,
            env=env,
            check=True,
            capture_output=True,
            text=True
        )
        print("Backup created successfully!")
        
        # Get file size
        size = backup_path.stat().st_size
        print(f"Backup size: {size / (1024*1024):.2f} MB")
        
        return str(backup_path)
    except subprocess.CalledProcessError as e:
        print(f"Backup failed: {e.stderr}")
        sys.exit(1)


def list_backups() -> list:
    """List all available backups."""
    backup_dir = get_backup_dir()
    backups = sorted(backup_dir.glob("*.sql"), key=lambda p: p.stat().st_mtime, reverse=True)
    
    if not backups:
        print("No backups found")
        return []
    
    print("\nAvailable backups:")
    print("-" * 60)
    for backup in backups:
        size = backup.stat().st_size / (1024 * 1024)
        mtime = datetime.fromtimestamp(backup.stat().st_mtime)
        print(f"{backup.name:30} {size:>8.2f} MB  {mtime.strftime('%Y-%m-%d %H:%M')}")
    print("-" * 60)
    
    return [str(b) for b in backups]


def restore_backup(backup_file: str, target_db: str = None) -> None:
    """
    Restore a database backup.
    """
    db_url = get_database_url()
    backup_path = Path(backup_file)
    
    if not backup_path.exists():
        print(f"Error: Backup file not found: {backup_file}")
        sys.exit(1)
    
    # Build connection parameters
    env = os.environ.copy()
    env["PGPASSWORD"] = db_url.split(":")[-1].split("@")[0].split("//")[-1]
    
    connection = db_url.replace("postgresql://", "")
    user_host = connection.split("@")
    user = user_host[0].split(":")[0]
    host_port_db = user_host[1].split("/")
    host_port = host_port_db[0].split(":")
    host = host_port[0]
    port = host_port[1] if len(host_port) > 1 else "5432"
    dbname = target_db or host_port_db[1].split("?")[0]
    
    # Drop existing database and recreate
    print(f"Dropping existing database: {dbname}")
    drop_cmd = [
        "dropdb",
        "--if-exists",
        "-h", host,
        "-p", port,
        "-U", user,
        dbname,
    ]
    
    try:
        subprocess.run(drop_cmd, env=env, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Warning: Could not drop database: {e}")
        print("Trying to restore into existing database...")
    
    print(f"Creating database: {dbname}")
    create_cmd = [
        "createdb",
        "-h", host,
        "-p", port,
        "-U", user,
        dbname,
    ]
    
    try:
        subprocess.run(create_cmd, env=env, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error creating database: {e}")
        sys.exit(1)
    
    # Restore backup
    print(f"Restoring backup: {backup_file}")
    cmd = [
        "pg_restore",
        "-h", host,
        "-p", port,
        "-U", user,
        "-d", dbname,
        "-v",  # Verbose
        str(backup_path),
    ]
    
    try:
        result = subprocess.run(cmd, env=env, check=True, capture_output=True, text=True)
        print("Restore completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Restore failed: {e.stderr}")
        sys.exit(1)


def cleanup_old_backups(retention_days: int = DEFAULT_RETENTION_DAYS) -> None:
    """Remove backups older than retention period."""
    backup_dir = get_backup_dir()
    cutoff = datetime.now().timestamp() - (retention_days * 86400)
    
    removed = 0
    for backup in backup_dir.glob("*.sql"):
        if backup.stat().st_mtime < cutoff:
            backup.unlink()
            removed += 1
            print(f"Removed old backup: {backup.name}")
    
    if removed > 0:
        print(f"Cleaned up {removed} old backup(s)")
    else:
        print("No old backups to clean up")


def main():
    parser = argparse.ArgumentParser(description="Database backup and restore utility")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Create backup
    backup_parser = subparsers.add_parser("create", help="Create a database backup")
    backup_parser.add_argument("-n", "--name", help="Backup file name")
    
    # List backups
    subparsers.add_parser("list", help="List all backups")
    
    # Restore backup
    restore_parser = subparsers.add_parser("restore", help="Restore a backup")
    restore_parser.add_argument("file", help="Backup file to restore")
    restore_parser.add_argument("-d", "--database", help="Target database name")
    
    # Cleanup old backups
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up old backups")
    cleanup_parser.add_argument(
        "--days",
        type=int,
        default=DEFAULT_RETENTION_DAYS,
        help=f"Retention days (default: {DEFAULT_RETENTION_DAYS})"
    )
    
    args = parser.parse_args()
    
    if args.command == "create":
        create_backup(args.name)
    elif args.command == "list":
        list_backups()
    elif args.command == "restore":
        restore_backup(args.file, args.database)
    elif args.command == "cleanup":
        cleanup_old_backups(args.days)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
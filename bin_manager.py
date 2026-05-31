"""
Bisdom Recycle Bin Manager
==========================
Handles saving deleted content to the bin/, restoring it, and auto-cleanup after 7 days.

Usage:
    # Save database records to bin before deleting
    from bin_manager import BinManager
    bm = BinManager()
    bm.save_db_records(records, source_name="signals")

    # Save deleted code to bin before removing
    bm.save_code(content, original_filename="bedrock_processor.py")

    # Restore latest item from bin
    bm.list_bin()

    # Clean up files older than 7 days
    bm.cleanup(days=7)
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

BIN_DIR = Path(__file__).parent / "bin"
BIN_DIR.mkdir(exist_ok=True)


class BinManager:
    def __init__(self):
        self.bin_dir = BIN_DIR

    def _timestamp(self):
        return datetime.utcnow().strftime("%Y-%m-%d_%H%M%S")

    def save_db_records(self, records: list[dict], source_name: str = "signals") -> str:
        """Save a list of database records (as dicts) to the bin as JSON."""
        filename = f"{source_name}_{self._timestamp()}.json"
        filepath = self.bin_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, default=str)
        print(f"[BIN] Saved {len(records)} records → bin/{filename}")
        return str(filepath)

    def save_code(self, content: str, original_filename: str) -> str:
        """Save deleted code content to the bin preserving the file extension."""
        ext = Path(original_filename).suffix
        stem = Path(original_filename).stem
        filename = f"{stem}_{self._timestamp()}{ext}"
        filepath = self.bin_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[BIN] Saved code → bin/{filename}")
        return str(filepath)

    def list_bin(self):
        """List all files currently in the bin with their age."""
        files = sorted(self.bin_dir.glob("*"), key=os.path.getmtime, reverse=True)
        files = [f for f in files if f.name != "README.md"]
        if not files:
            print("[BIN] Bin is empty.")
            return
        now = datetime.utcnow()
        print(f"\n{'File':<50} {'Age':<15} {'Expires In'}")
        print("-" * 80)
        for f in files:
            mtime = datetime.utcfromtimestamp(os.path.getmtime(f))
            age = now - mtime
            expires_in = timedelta(days=7) - age
            age_str = f"{age.days}d {age.seconds // 3600}h ago"
            exp_str = f"{max(0, expires_in.days)}d {max(0, expires_in.seconds // 3600)}h left" if expires_in.total_seconds() > 0 else "EXPIRED"
            print(f"{f.name:<50} {age_str:<15} {exp_str}")

    def restore_latest(self, keyword: str = None) -> str:
        """Return the content of the latest bin file matching an optional keyword."""
        files = sorted(self.bin_dir.glob("*"), key=os.path.getmtime, reverse=True)
        files = [f for f in files if f.name != "README.md"]
        if keyword:
            files = [f for f in files if keyword.lower() in f.name.lower()]
        if not files:
            print(f"[BIN] No files found{' matching: ' + keyword if keyword else ''}.")
            return None
        latest = files[0]
        print(f"[BIN] Restoring: bin/{latest.name}")
        return latest.read_text(encoding="utf-8")

    def cleanup(self, days: int = 7):
        """Permanently delete files older than `days` days from BOTH local disk AND git."""
        import subprocess
        now = datetime.utcnow()
        files = [f for f in self.bin_dir.glob("*") if f.name != "README.md"]
        deleted = 0
        for f in files:
            mtime = datetime.utcfromtimestamp(os.path.getmtime(f))
            if (now - mtime).days >= days:
                # Step 1: Remove from git tracking (in case it was ever committed)
                try:
                    subprocess.run(
                        ["git", "rm", "--cached", "--force", str(f)],
                        capture_output=True, cwd=str(self.bin_dir.parent)
                    )
                except Exception:
                    pass  # If not tracked by git, that's fine

                # Step 2: Delete from local disk
                f.unlink()
                print(f"[BIN] Permanently deleted from local + git: {f.name} (older than {days} days)")
                deleted += 1

        # Step 3: If anything was removed from git, commit the removal
        if deleted > 0:
            try:
                subprocess.run(
                    ["git", "commit", "-m", f"BIN cleanup: permanently removed {deleted} expired file(s)"],
                    capture_output=True, cwd=str(self.bin_dir.parent)
                )
                subprocess.run(
                    ["git", "push"],
                    capture_output=True, cwd=str(self.bin_dir.parent)
                )
                print(f"[BIN] Git cleanup committed and pushed.")
            except Exception as e:
                print(f"[BIN] Git push skipped: {e}")
        else:
            print(f"[BIN] Nothing to clean up. All files are within {days} days.")
        return deleted



if __name__ == "__main__":
    bm = BinManager()
    bm.list_bin()
    bm.cleanup(days=7)

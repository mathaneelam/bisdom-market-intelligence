# 🗑️ Bisdom Recycle Bin

This folder acts as a **Recycle Bin** for the project.

## How it works

- **Nothing is ever permanently deleted immediately.**
- When database records or code is deleted, a copy is saved here first with a datestamp.
- Files are kept for **7 days**.
- After 7 days with no restore request, the file is permanently removed.

## File Naming Format

| What was deleted | Saved as |
|---|---|
| Database signals | `signals_YYYY-MM-DD_HHMMSS.json` |
| Code from a Python file | `filename_YYYY-MM-DD_HHMMSS.py` |

## To Restore

Just tell the agent: **"Bring it back"** or **"Restore from bin"** and it will put the data back exactly where it came from.

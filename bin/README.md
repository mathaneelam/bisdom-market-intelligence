# 🗑️ Bisdom Cloud Recycle Bin

This is a **cloud-based Recycle Bin** stored in Supabase Postgres.

## How it works

- **Nothing is ever permanently deleted immediately.**
- When database records are deleted, they are first saved to the `deleted_signals` table in Supabase with a 7-day expiry timestamp.
- Every day at **3:00 AM IST**, Render automatically purges records older than 7 days.
- This works **24/7 whether your laptop is on or off** because it runs on the cloud server.

## Database Table: `deleted_signals`

| Column | Description |
|---|---|
| `id` | Unique bin record ID |
| `original_id` | The original signal's ID before deletion |
| `source_name` | Where it came from (e.g. "signals") |
| `content` | Full original record stored as JSON |
| `deleted_reason` | Why it was deleted |
| `deleted_at` | When it was moved to the bin |
| `expires_at` | `deleted_at + 7 days` — permanent delete date |

## To Restore

Just tell the agent: **"Bring it back"** or **"Restore from bin"** and it will restore the records directly from Supabase back into the live database.

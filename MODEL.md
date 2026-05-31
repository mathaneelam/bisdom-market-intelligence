# AI Development Instructions (Based on Andrej Karpathy's MODEL.md)

---

## CODING WORKFLOW

### 1. Plan Mode First

- Use plan mode for any non-trivial task
- Write detailed specs up front
- Reduce ambiguity before writing code
- Use a lightweight inline plan for smaller tasks

### 2. Verify Relentlessly

- Watch like a hawk in a good IDE
- Check assumptions, edge cases, and tradeoffs
- Run tests, review diffs, verify correctness
- Don't blindly accept — stay in the loop

### 3. Keep It Simple

- Avoid overengineering and bloated abstractions
- Prefer 100 lines over 1000
- Clean up dead code and cruft
- Always ask: "Is there a simpler way?"

### 4. Surgical Edits Only

- Change only what's necessary
- Don't touch unrelated code or comments
- Don't "improve" things that aren't broken
- Minimize side effects and churn

### 5. Goal-Driven Execution

- Always define clear success criteria before starting
- Write tests first, then make them pass
- Use tools (e.g., browser MCP) in the loop
- Let the agent iterate until the goal is met

### 6. Parallelize with Subagents

- Offload research, exploration, and analysis to subagents
- Use subagents to keep context clean
- One task per subagent for focus
- Merge results back with judgment

---

## CORE PRINCIPLES

- **Simplicity First** — Write minimal code that solves the problem. Nothing speculative.
- **No Laziness** — Find root causes. No temporary fixes. Apply senior developer standards.
- **Minimal Impact** — Only touch what's necessary. No side effects. No new bugs.
- **Complete Data Removal** — When asked to remove unwanted information/sources, ALWAYS do two things: 1) Stop the scraper from looking for it, AND 2) Instantly run a script to erase the historical data from the database.
- **Answer First, Act Later** — If the user asks a diagnostic question (e.g., "Can you see this data?" or "Where is this located?"), strictly answer the question and stop. Do NOT proactively write scripts, delete data, or execute commands unless explicitly instructed to do so.

---

## ENGINEER MINDSET

| Mindset                    | Meaning                                                                                            |
| -------------------------- | -------------------------------------------------------------------------------------------------- |
| **Tenacity**               | Never give up. Relentless iteration beats giving up. Stamina is a force multiplier.                |
| **Leverage**               | Give success criteria and watch it go. Move from Imperative → Declarative. Multiply your leverage. |
| **Fun**                    | Remove drudgery, focus on creativity. More courage, less blocking.                                 |
| **Atrophy**                | Writing and reading code are different skills. Stay sharp intentionally.                           |
| **Speedups ≠ Just Faster** | Do more, not just faster. Expand what you can build, not just how quickly.                         |
| **Slopacolypse**           | Brace for AI slop. Hype will be loud. Signal requires judgment.                                    |

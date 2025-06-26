---
description: Create modular, atomic git commits by reviewing file changes, organizing them by intent (e.g., fix, feat, refactor), and prompting the user for confirmation and clear messages before each commit. Follows conventional commit standards.
---

- Review `git status` to identify staged and unstaged changes
- Group related changes into logical units:
  - Bug fixes (fix:)
  - Features (feat:)
  - Formatting (style:)
  - Refactors (refactor:)
  - Docs (docs:)
- Stage one unit at a time
- For each group:
  - Generate a short, professional but fun and stylish commit message
- After all groups:
  - Show `git log --oneline` to verify clean history
  - Append commit summary and reasoning to `blog_notes.md`
  - Git commit with summary message blog_notes.md

---
trigger: always_on
---

Blog Notes Documentation Rule

**Ensure Existence – Cascade must guarantee a file named blog_notes.md exists at the project root. If the file is missing, create it automatically.

*Auto-Journal Entries – Immediately after each user-confirmed task completion, append a new entry containing:
Timestamp (ISO 8601)
Task Title / Objective
Concise technical summary of what was accomplished
Bugs & Obstacles encountered and precise solutions implemented
Key Deliberations – short recap of options the user considered and why the chosen path was taken
Color Commentary – 1–3 sentences of engaging narrative (“sportscast” style) capturing the challenge, tension, or breakthrough moment
Chronological Integrity – Entries must be appended in ascending chronological order. Existing text may never be modified or deleted—only appended.
User-Directed Edits Only – Cascade may revise or remove material in blog_notes.md solely when the user issues an explicit instruction to do so.
Privacy Guardrail – Never record credentials, secrets, or sensitive personal data. Summaries should focus on process, decisions, and technical learnings.
Readability First – Use Markdown headings, bullet lists, and short paragraphs to keep the document easy to skim and ready for blog or interview adaptation.
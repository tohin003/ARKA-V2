# ARKA Memory Policy

This policy defines what ARKA stores, how it is retrieved, and how it is deleted.

## Memory Types
- Events: raw session logs (user messages, agent results, tool calls).
- Facts: distilled, structured memories (subject, predicate, object, confidence).
- Episodes: short summaries of completed tasks (one per run).

## Auto-Capture Rules
- Only *safe* facts are auto-extracted from user messages.
- Sensitive content is not auto-stored. Examples: passwords, API keys, OTPs, private keys, credit cards.
- Sensitive content can be stored only via explicit user instruction and should be marked `sensitive`.

## Retention Defaults
- Events: 90 days
- Episodes: 180 days
- Facts: retained indefinitely unless deleted or expired

## Updates & Conflicts
- Facts with the same (subject, predicate) are **upserted**. Older values are preserved in metadata history.
- Manual memories (`remember_fact`) are stored as `note` facts and do not overwrite existing facts.

## Deletion
- Expired facts are auto-deleted unless locked.
- Users can delete facts by ID.
- Locked facts are protected from auto-deletion.

## Retrieval
- Memory recall uses retrieval + token budgeting; it does not dump entire memory.
- By default, sensitive facts are excluded from recall unless explicitly enabled.

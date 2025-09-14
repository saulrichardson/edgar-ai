Architecture Decision Records (ADRs)

This folder contains the original “tickets” converted into ADRs (Architecture Decision Records).

What they are
- Historical design notes and decisions captured as markdown files.
- Named with their original IDs (e.g., DISC-01, SCH-01, TST-01) to preserve continuity.

How to use
- Treat each file as a point-in-time decision or exploration.
- Prefer adding a new ADR for a superseding decision rather than rewriting history.
- Cross-link related ADRs when you deprecate or replace a decision.

Format guidance (lightweight)
- Title: Clear, action-oriented (e.g., “Goal-Aware Discoverer”).
- Status: proposed | accepted | deprecated.
- Context: Why this mattered.
- Decision: What was chosen.
- Consequences: Tradeoffs and follow-ups.
- References: Links to specs/guides or experiments.

Scope
- ADRs document architectural decisions. Implementation details belong in guides or inline code comments.

Notes
- Older entries may read like RFCs or work tickets; they are preserved verbatim for provenance.


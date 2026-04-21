# Storage + Tools + Settings

This document focuses only on:

- the **SQLite-related storage design**
- the **Calendar tool**
- the **USD price tool**
- the **settings file**

The design assumes that if we later migrate from **SQLite to PostgreSQL**, only the adapter layer should change.

---

# 1. Design Goal

The main rule is:

> **Business logic should not depend on SQLite directly.**

Instead, storage access should go through repository interfaces / ports.  
SQLite is just the first adapter implementation.

That means:

- orchestrator depends on repositories
- tools depend on services or repositories
- repositories depend on interfaces
- SQLite is only one concrete implementation

Later, PostgreSQL should be added as another adapter implementing the same contracts.

---

# 2. What should be stored in SQLite for this app

For the current version of the app, the relevant persisted data is:

- conversations
- messages
- runs
- run steps
- memory items
- calendar events
- optionally cached FX quotes

That is enough for:

- conversation persistence
- execution traceability
- memory-based tools
- a local calendar tool
- optional quote caching

---

# 3. Storage Architecture

## Rule

Never let the rest of the app write SQL directly.

Use this layering:

```text
Application logic
    |
    v
Repository / Service interfaces
    |
    v
SQLite adapters
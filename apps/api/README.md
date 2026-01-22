# Sanity Bingo API

Application summary and TODO, cheers gippity

---

## Goals

Build a production-lean API that supports:

1. **Events management**
2. **Teams CRUD (scoped to an event)**
3. **Board CRUD (scoped to an event; 1:1 event↔board)**
    - Board owns **Tiles** (CRUD + reorder)
4. **Catalogue management**
    - Bosses, Items (global, reusable)
5. **Submissions (scoped to an event)**
    - Teams submit tiles (or claims) with evidence/notes, reviewed and approved/rejected

Design priorities:

- Feature-based structure (modules)
- Clear resource ownership (scoping)
- Avoid async lazy-load pitfalls (no accidental DB IO during serialization)
- Predictable endpoints and query shapes for clients
- Strong constraints and simple invariants (make invalid states impossible)

---

## High-level domain model (recommended)

### Core entities

- **Event**
    - Owns: one Board, many Teams, many Submissions
- **Board** (1:1 with Event)
    - Owns: many Tiles (ordered)
- **Tile** (N:1 with Board)
    - Optionally references catalogue item/boss
    - Stores snapshot fields required for historical correctness
- **Team** (N:1 with Event)
- **Submission** (N:1 with Event)
    - Belongs to a Team
    - Targets a Tile
    - Has status workflow: PENDING → APPROVED/REJECTED (optional resubmissions)

### Catalogue entities (global)

- **Boss**
    - Owns: many Items
- **Item**
    - Belongs to Boss
    - Stores metadata used to create tiles (and/or snapshot into tiles)

---

## API route philosophy

### Scoped routes for _create/list_

Use nesting where it describes ownership:

- Teams are created/listed under an Event
- Board is created/fetched under an Event (1:1)
- Submissions are created/listed under an Event

### Canonical routes for _read/update/delete_

Once a resource exists, prefer short, canonical endpoints:

- `/teams/{team_id}`
- `/boards/{board_id}`
- `/tiles/{tile_id}`
- `/submissions/{submission_id}`

### Convenience view routes (UI-friendly)

Optional, but recommended:

- `/events/{event_id}/page` for “event dashboard” payloads (event + board + tiles + teams + submission summary)

---

## Suggested endpoints (v1)

Base prefix: `/v1/bingo`

### Events

- `POST   /events`
- `GET    /events`
- `GET    /events/{event_id}`
- `PATCH  /events/{event_id}`
- `DELETE /events/{event_id}`

### Teams (scoped to event; canonical by id)

- `POST   /events/{event_id}/teams`
- `GET    /events/{event_id}/teams`
- `GET    /teams/{team_id}`
- `PATCH  /teams/{team_id}`
- `DELETE /teams/{team_id}`

### Board (1:1 to event)

- `POST   /events/{event_id}/board` (create board for event; conflict if exists)
- `GET    /events/{event_id}/board` (fetch board for event)
- `GET    /boards/{board_id}` (returns board + tiles ordered)
- `PATCH  /boards/{board_id}`
- `DELETE /boards/{board_id}`

### Tiles (owned by board; ordered)

- `POST   /boards/{board_id}/tiles`
- `PATCH  /tiles/{tile_id}`
- `DELETE /tiles/{tile_id}`
- `PUT    /boards/{board_id}/tiles/order` (batch reorder)

### Catalogue

- `POST   /catalogue/bosses`
- `GET    /catalogue/bosses`
- `GET    /catalogue/bosses/{boss_id}`
- `PATCH  /catalogue/bosses/{boss_id}`
- `DELETE /catalogue/bosses/{boss_id}`

- `POST   /catalogue/bosses/{boss_id}/items`
- `GET    /catalogue/bosses/{boss_id}/items`
- `GET    /catalogue/items/{item_id}`
- `PATCH  /catalogue/items/{item_id}`
- `DELETE /catalogue/items/{item_id}`

### Submissions (per-event)

- `POST   /events/{event_id}/submissions`
- `GET    /events/{event_id}/submissions` (filter by status/team)
- `GET    /submissions/{submission_id}`
- `PATCH  /submissions/{submission_id}` (edit evidence/notes, if allowed)

Moderation / review actions (keep explicit):

- `POST   /submissions/{submission_id}/approve`
- `POST   /submissions/{submission_id}/reject`

Optional team-scoped listing:

- `GET    /events/{event_id}/teams/{team_id}/submissions`

### Views (optional but useful)

- `GET /events/{event_id}/page`
- `GET /events/{event_id}/tiles` (shortcut to list tiles for the event)

---

## Data integrity rules (enforce in DB + service)

### Event

- event exists before any dependent resource
- deleting event cascades (board, teams, submissions)

### Board

- exactly **one** board per event
    - enforce with `board.event_id UNIQUE`
- deleting board cascades tiles

### Tiles

- belong to a board
- always have `order_index` (0..n-1)
- reorder operation updates many tiles in a single transaction

### Teams

- team belongs to event
- team name unique within event (recommended constraint)

### Catalogue

- items belong to bosses
- deleting boss: either cascade delete items OR soft-delete (choose policy)
- tiles should not break when catalogue changes:
    - **snapshot** critical catalogue fields into tile at creation time

### Submissions

- submission belongs to event AND team AND tile
- (optional) enforce: team.event_id == submission.event_id
- (optional) enforce: tile.board.event_id == submission.event_id
- status workflow enforced server-side:
    - PENDING → APPROVED/REJECTED
    - prevent approving twice, prevent editing after approval (policy choice)

---

## Implementation path (top-down)

This order minimizes rework and keeps invariants clear.

### Phase 0 — Foundation (app + DB)

- [x] Create project structure under `apps/bingo-api/`
- [x] Add deps in `pyproject.toml` (FastAPI, SQLAlchemy async, Alembic, Pydantic, etc.)
- [x] Create app entrypoint `sanity/main.py` + router composition
- [x] Implement config + logging
- [x] Implement DB engine + async session dependency
- [x] Configure Alembic + initial migration pipeline

### Phase 1 — Catalogue (global data first)

Catalogue is a stable dependency for tiles.

- [x] Implement `Boss` model + schemas + CRUD endpoints
- [x] Implement `Item` model + schemas + CRUD endpoints
- [ ] Add seed endpoint or seed script (optional) for development

Acceptance checks:

- [ ] Can create/list/update bosses and items
- [ ] Items cannot exist without a boss
- [ ] List items by boss works

### Phase 2 — Events (the root aggregate)

- [ ] Implement `Event` model + schemas + CRUD endpoints
- [ ] Add validation on schedule window (starts_at < ends_at)
- [ ] Add event state fields if needed (DRAFT/ACTIVE/COMPLETED) (optional)

Acceptance checks:

- [ ] Can create/list/get/update/delete events

### Phase 3 — Board + Tiles (board is 1:1 with event)

- [ ] Implement `Board` model with `event_id UNIQUE`
- [ ] Implement `Tile` model with `board_id` + `order_index`
- [ ] Implement board create under event: `POST /events/{event_id}/board`
- [ ] Implement `GET /boards/{board_id}` returning board + tiles in order
- [ ] Implement tile CRUD under board
- [ ] Implement tile reorder endpoint (batch)

Tile creation rules:

- [ ] Support creating tiles from catalogue references
- [ ] Snapshot catalogue fields into tile (name/points/etc.) to preserve history

Acceptance checks:

- [ ] Creating second board for same event returns 409 Conflict
- [ ] Tiles are always ordered
- [ ] Reorder is atomic (single transaction)
- [ ] Tiles are returned in correct order after reorder

### Phase 4 — Teams (scoped per event)

- [ ] Implement `Team` model with `event_id`
- [ ] Implement team create/list under event + canonical RUD by id
- [ ] Enforce unique team name per event (recommended)

Acceptance checks:

- [ ] Teams list only includes those within event
- [ ] Team cannot be moved across events (policy choice)

### Phase 5 — Submissions (scoped per event; approval workflow)

- [ ] Decide submission payload:
    - tile_id
    - team_id
    - evidence (URL(s) / text)
    - notes
- [ ] Implement `Submission` model with:
    - `event_id`, `team_id`, `tile_id`
    - `status` enum (PENDING/APPROVED/REJECTED)
    - audit fields (reviewed_by, reviewed_at, reason)
- [ ] Implement create/list/get/update endpoints
- [ ] Implement approve/reject action endpoints
- [ ] Add filters:
    - `?status=pending`
    - `?team_id=...`
    - `?tile_id=...`

Validation checks (service-level):

- [ ] Ensure team belongs to event
- [ ] Ensure tile belongs to event (through board)
- [ ] Prevent double-approval / invalid transitions
- [ ] Decide whether edits are allowed after approval

Acceptance checks:

- [ ] Create submission for a team in the wrong event fails
- [ ] Approve/reject works and is idempotent or safely guarded
- [ ] List submissions by event + filter works

### Phase 6 — Views (API ergonomics, optional)

- [ ] Add `GET /events/{event_id}/page` returning:
    - event
    - board summary
    - tiles
    - teams
    - submission counts by status (optional)
- [ ] Ensure this endpoint does not trigger lazy loads (explicit queries only)

Acceptance checks:

- [ ] Single call returns everything needed for an “event dashboard”

---

## Architecture & module layout (feature-based)

```
  event/      (event CRUD + page views)
  team/       (team CRUD)
  board/      (board CRUD + board read with tiles)
  tile/       (tile CRUD + reorder)
  catalogue/  (router only)
    boss/
    item/
  submission/ (submission workflow)
```

Each feature contains:

- `model.py` (SQLAlchemy models)
- `schema.py` (Pydantic DTOs)
- `repo.py` (DB queries)
- `service.py` (business logic)
- `router.py` (HTTP layer)

---

## Critical implementation rules (avoid common async SQLAlchemy traps)

- Do **not** return ORM objects that require lazy loading during serialization.
- Use explicit loading strategies for read endpoints:
    - `selectinload()` for board → tiles when returning board with tiles
    - or explicit join queries + manual assembly
- Keep “page” endpoints as service-level compositions of repo calls.
- Prefer canonical query keys / query shapes (stable for clients).

---

## API quality checklist (do as you go)

- [ ] Consistent HTTP status codes (404 not found, 409 conflict, 422 validation)
- [ ] Pagination for list endpoints (optional for MVP, add early if easy)
- [ ] OpenAPI tags per feature
- [ ] Example request/response payloads in docstrings or schema config
- [ ] Centralized error handling (domain exceptions → HTTP mapping)

---

## Milestones

- [x] M0: App boots, migrations run, health endpoint OK
- [x] M1: Catalogue CRUD complete
- [ ] M2: Events CRUD complete
- [ ] M3: Board + Tiles CRUD + reorder complete
- [ ] M4: Teams CRUD complete
- [ ] M5: Submissions workflow complete
- [ ] M6: Optional “event page” view endpoint complete

---

## Out of scope (for this README)

- Authentication / RBAC
- Deploy strategy
- Web client implementation details

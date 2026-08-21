# YouTube Shorts AI — Backend Documentation

**A RAG-powered pipeline that turns any YouTube video into ready-to-post Shorts scripts.**

---

## 1. What This Project Does

Given a YouTube video URL, the backend:

1. Pulls the video's transcript
2. Cleans and splits it into timestamp-aware chunks
3. Embeds each chunk into a vector space
4. Stores chunks + vectors in PostgreSQL (via `pgvector`)
5. Retrieves the most "short-worthy" moments using semantic (RAG) search
6. Sends those moments to an LLM (Groq) to rank and script them
7. Returns structured JSON — title, hook, script, duration, score, and exact source timestamps — ready for a frontend or a video-rendering pipeline

In short: **YouTube video → transcript → RAG → AI-written Shorts scripts**, with no video rendering in the MVP.

---

## 2. Core Use Cases

| Use Case                               | Description                                                                                                                                                                                 |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Content repurposing for creators**   | A podcaster/YouTuber pastes a long-form video URL and gets 5+ candidate Shorts with hooks and scripts already written.                                                                      |
| **Clip-hunting automation**            | Replaces manual scrubbing through a video to find "quotable" or viral moments — the RAG layer finds them semantically (surprising facts, emotional beats, hot takes) instead of by keyword. |
| **Agency / bulk workflows**            | A social media agency processes multiple client videos, storing all transcripts, chunks, and generated Shorts per video for later reuse or regeneration.                                    |
| **Script-first, video-later pipeline** | Because MP4 rendering is deliberately deferred, the same backend can plug into any downstream renderer (FFmpeg, Remotion, CapCut API, etc.) later without redesigning the data model.       |
| **Regeneration / iteration**           | The `shorts/{id}/regenerate` endpoint lets a user re-roll a specific Short's script without re-processing the whole video.                                                                  |

---

## 3. Tech Stack

| Layer               | Technology                                                                  |
| ------------------- | --------------------------------------------------------------------------- |
| API framework       | FastAPI + Uvicorn                                                           |
| ORM / DB access     | SQLAlchemy 2.x (async) + asyncpg                                            |
| Migrations          | Alembic                                                                     |
| Database            | PostgreSQL + `pgvector` extension, hosted on **Neon** (serverless)          |
| Validation          | Pydantic v2                                                                 |
| LLM                 | Groq (chat completions, structured JSON output)                             |
| Embeddings          | `sentence-transformers` (`all-MiniLM-L6-v2`, 384-dim), run locally          |
| Transcript source   | `youtube-transcript-api`                                                    |
| Deployment target   | Render (Free tier for MVP, Docker-based) for the API; Neon for the database |
| Frontend (separate) | Next.js                                                                     |

**Deliberate design choice:** no Prisma anywhere in this backend. One ORM/migration system only — SQLAlchemy + Alembic — with raw SQL used specifically for `pgvector` similarity queries, since SQLAlchemy doesn't need to model vector math itself.

---

## 4. System Architecture

```
                         ┌──────────────┐
                         │   YouTube    │
                         └──────┬───────┘
                                │
                                ▼
┌──────────┐              ┌──────────────┐
│ Next.js  │─────────────▶│   FastAPI    │
└──────────┘              └──────┬───────┘
                                 │
                    ┌────────────┼─────────────┐
                    ▼            ▼             ▼
               Transcript    Embeddings      Groq
                    │            │             │
                    ▼            ▼             │
                  Chunks ──▶ pgvector ◀────────┘
                                 │
                                 ▼
                              RAG
                                 │
                                 ▼
                            Short Scripts
```

### Pipeline, step by step

```
YouTube URL
   → Extract video ID
   → Fetch transcript
   → Clean transcript
   → Time-aware chunking (80–150 words/chunk)
   → Generate embeddings (384-dim)
   → Store chunks + vectors in Postgres
   → Multi-query RAG retrieval
   → Deduplicate candidates
   → Groq: rank moments
   → Groq: write Short scripts (structured JSON)
   → Persist Shorts + sources
   → Return structured JSON to client
```

---

## 5. Project Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI app entrypoint
│   ├── core/
│   │   ├── config.py            # Pydantic settings (env vars)
│   │   └── database.py          # Async engine + session factory
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── video.py
│   │   ├── transcript_chunk.py
│   │   ├── short.py
│   │   └── short_source.py
│   ├── schemas/                 # Pydantic request/response models
│   ├── api/                     # FastAPI routers
│   │   ├── health.py
│   │   ├── videos.py
│   │   └── shorts.py
│   ├── services/                # Business logic
│   │   ├── youtube.py           # Video ID extraction
│   │   ├── transcript.py        # Transcript fetching
│   │   ├── chunker.py           # Cleaning + chunking
│   │   ├── embeddings.py        # Local embedding model
│   │   ├── vector_store.py      # pgvector read/write helpers
│   │   ├── rag.py               # Similarity search + retrieval
│   │   ├── groq_service.py      # LLM calls
│   │   └── short_generator.py   # End-to-end Short generation
│   └── prompts/                 # System prompts for Groq
│       ├── moments.py
│       └── shorts.py
├── alembic/                     # DB migrations
├── tests/
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

## 6. Data Model

### `videos`

Stores each submitted YouTube video and its processing state.

| Column                             | Type               | Notes                                   |
| ---------------------------------- | ------------------ | --------------------------------------- |
| id                                 | int, PK            |                                         |
| youtube_id                         | string(32), unique | Extracted from URL                      |
| youtube_url                        | string(500)        | Original URL                            |
| title, channel_name, thumbnail_url | nullable           | Metadata (fillable later)               |
| duration_seconds                   | int, nullable      |                                         |
| transcript_text                    | text, nullable     | Full raw transcript                     |
| status                             | enum               | `PENDING → PROCESSING → READY / FAILED` |

### `transcript_chunks`

Timestamp-aware segments of the transcript, each with a vector embedding.

| Column                | Type          | Notes                                                                                  |
| --------------------- | ------------- | -------------------------------------------------------------------------------------- |
| id                    | int, PK       |                                                                                        |
| video_id              | FK → videos   | Cascade delete                                                                         |
| chunk_index           | int           | Order within the video                                                                 |
| start_time / end_time | float         | Seconds                                                                                |
| text                  | text          | Cleaned chunk text                                                                     |
| embedding             | `vector(384)` | Added via raw SQL, not a mapped SQLAlchemy column — HNSW-indexed for cosine similarity |

### `shorts`

Generated Short scripts.

| Column              | Type            | Notes                                                                    |
| ------------------- | --------------- | ------------------------------------------------------------------------ |
| id                  | int, PK         |                                                                          |
| video_id            | FK → videos     |                                                                          |
| title, hook, script | text            | Groq output                                                              |
| duration_seconds    | int             | Target length (15–60s)                                                   |
| score               | float, nullable | Groq-assigned quality/virality score                                     |
| style               | enum            | VIRAL / EDUCATIONAL / STORYTELLING / NEWS / MOTIVATIONAL / CONTROVERSIAL |
| status              | enum            | GENERATING / READY / FAILED                                              |

### `short_sources`

Traceability: which transcript chunk(s) each Short was built from.

| Column                | Type                   | Notes           |
| --------------------- | ---------------------- | --------------- |
| short_id              | FK → shorts            |                 |
| chunk_id              | FK → transcript_chunks |                 |
| start_time / end_time | float                  | Exact span used |

**Why this matters:** every generated Short can be traced back to its exact source timestamps — needed both for factual grounding (no hallucinated claims) and for eventually cutting the real video clip.

---

## 7. Database Schema (DDL)

Raw SQL equivalent of the SQLAlchemy models above — this is effectively what `alembic upgrade head` produces on Neon. Run once, in order:

```sql
-- Enable pgvector (Neon: run in the SQL editor, or let the Alembic migration do it)
CREATE EXTENSION IF NOT EXISTS vector;

-- Enums
CREATE TYPE video_status AS ENUM ('PENDING', 'PROCESSING', 'READY', 'FAILED');
CREATE TYPE short_status AS ENUM ('GENERATING', 'READY', 'FAILED');
CREATE TYPE short_style AS ENUM (
  'VIRAL', 'EDUCATIONAL', 'STORYTELLING', 'NEWS', 'MOTIVATIONAL', 'CONTROVERSIAL'
);

-- videos
CREATE TABLE videos (
    id                SERIAL PRIMARY KEY,
    youtube_id        VARCHAR(32)  NOT NULL UNIQUE,
    youtube_url       VARCHAR(500) NOT NULL,
    title             VARCHAR(500),
    channel_name      VARCHAR(255),
    duration_seconds  INTEGER,
    thumbnail_url     VARCHAR(1000),
    transcript_text   TEXT,
    status            video_status NOT NULL DEFAULT 'PENDING',
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX idx_videos_youtube_id ON videos (youtube_id);

-- transcript_chunks
CREATE TABLE transcript_chunks (
    id           SERIAL PRIMARY KEY,
    video_id     INTEGER NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    chunk_index  INTEGER NOT NULL,
    start_time   FLOAT   NOT NULL,
    end_time     FLOAT   NOT NULL,
    text         TEXT    NOT NULL,
    embedding    VECTOR(384),          -- added via raw SQL, matches EMBEDDING_DIMENSIONS
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_transcript_chunks_video_id ON transcript_chunks (video_id);

-- HNSW index for cosine similarity search
CREATE INDEX transcript_chunks_embedding_idx
    ON transcript_chunks
    USING hnsw (embedding vector_cosine_ops);

-- shorts
CREATE TABLE shorts (
    id                SERIAL PRIMARY KEY,
    video_id          INTEGER NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    title             VARCHAR(500) NOT NULL,
    hook              TEXT NOT NULL,
    script            TEXT NOT NULL,
    duration_seconds  INTEGER NOT NULL,
    score             FLOAT,
    style             short_style  NOT NULL,
    status            short_status NOT NULL DEFAULT 'GENERATING',
    video_url         VARCHAR(1000),   -- populated post-MVP once Cloudinary rendering exists
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_shorts_video_id ON shorts (video_id);

-- short_sources
CREATE TABLE short_sources (
    id          SERIAL PRIMARY KEY,
    short_id    INTEGER NOT NULL REFERENCES shorts(id) ON DELETE CASCADE,
    chunk_id    INTEGER NOT NULL REFERENCES transcript_chunks(id) ON DELETE CASCADE,
    start_time  FLOAT NOT NULL,
    end_time    FLOAT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_short_sources_short_id ON short_sources (short_id);
CREATE INDEX idx_short_sources_chunk_id ON short_sources (chunk_id);
```

### Entity relationships

```
videos (1) ───< transcript_chunks (many)
   │
   └──< shorts (many) ───< short_sources (many) >─── transcript_chunks
```

- One video → many transcript chunks
- One video → many generated Shorts
- One Short → many source records (a Short can be assembled from more than one chunk)
- `short_sources` is the join table that links a Short back to the exact transcript chunk(s) and timestamp span it was generated from

### Notes specific to Neon

- `CREATE EXTENSION IF NOT EXISTS vector;` must be run with a role that has extension privileges — on Neon this works out of the box from the SQL editor or via Alembic's first migration, no extra setup needed
- The `vector` type and `hnsw` index work identically to self-hosted Postgres — Neon is wire-compatible, nothing pgvector-specific changes
- If using Neon **branching** for a dev/staging split, re-run `alembic upgrade head` (or this DDL) on each new branch — branches copy data but migrations still need to be tracked per-branch via Alembic's version table

---

## 8. Why pgvector via Raw SQL (not full ORM mapping)

SQLAlchemy handles the standard CRUD and relationships. The one operation that matters for RAG — cosine similarity (`embedding <=> query_embedding`) — is run as raw SQL because:

- It keeps SQLAlchemy simple and avoids fighting the ORM over a specialized type
- The HNSW index and vector casting are best expressed directly in SQL anyway

```sql
SELECT id, text, 1 - (embedding <=> :query_embedding) AS similarity
FROM transcript_chunks
WHERE video_id = :video_id AND embedding IS NOT NULL
ORDER BY embedding <=> :query_embedding
LIMIT :limit;
```

---

## 9. RAG Strategy: Multi-Query Retrieval

Instead of a single similarity search, the system runs several fixed "angle" queries against each video's chunks and merges the results:

- "most surprising moments"
- "most useful advice"
- "most emotional stories"
- "most controversial opinions"
- "unexpected facts and revelations"

Results are deduplicated by chunk ID and sorted by similarity score. This surfaces a diverse candidate pool instead of one narrow cluster of similar chunks — important because "good Shorts material" isn't a single semantic concept.

---

## 10. LLM Usage (Groq)

Two distinct prompts, used in sequence:

1. **Moment-finding** — given transcript chunks, identify which spans are Shorts-worthy, scored 0–100, with strict grounding rules (never invent information, must cite source timestamps).
2. **Script-writing** — given the chosen chunks, write a HOOK → CONTEXT → MAIN IDEA → PAYOFF → CTA script, again constrained to only use supplied transcript content.

**Recommended output format:** structured JSON (not free text), so results map directly onto the `shorts` table:

```json
{
  "title": "...",
  "hook": "...",
  "script": "...",
  "duration_seconds": 52,
  "score": 94,
  "sources": [{ "chunk_id": 12, "start_time": 732, "end_time": 781 }]
}
```

> Groq's model lineup changes over time — check current model availability and structured-output support before hard-coding a model name in `groq_service.py`.

---

## 11. API Reference

| Method | Endpoint                      | Purpose                                             |
| ------ | ----------------------------- | --------------------------------------------------- |
| GET    | `/api/health`                 | Health check                                        |
| POST   | `/api/videos`                 | Submit a YouTube URL, creates a `Video` row         |
| GET    | `/api/videos/{id}`            | Fetch video details/status                          |
| POST   | `/api/videos/{id}/process`    | Fetch transcript → chunk → embed → mark READY       |
| GET    | `/api/videos/{id}/chunks`     | Inspect stored transcript chunks                    |
| POST   | `/api/shorts/generate`        | Run RAG + Groq to generate Shorts for a READY video |
| GET    | `/api/shorts`                 | List generated Shorts                               |
| GET    | `/api/shorts/{id}`            | Fetch a single Short                                |
| POST   | `/api/shorts/{id}/regenerate` | Re-run script generation for one Short              |

Interactive docs are auto-generated by FastAPI at `/docs` and `/redoc`.

### Example flow

```http
POST /api/videos
{ "youtube_url": "https://www.youtube.com/watch?v=XXXXXXXXXXX" }
→ { "id": 1, "youtube_id": "XXXXXXXXXXX", "status": "PENDING" }

POST /api/videos/1/process
→ { "id": 1, "status": "READY" }

POST /api/shorts/generate
{ "video_id": 1, "count": 5, "duration": 60, "style": "VIRAL" }
→ { "video_id": 1, "status": "GENERATED", "shorts": [ ... ] }
```

---

## 12. Environment Variables

| Variable                | Purpose                                            |
| ----------------------- | -------------------------------------------------- |
| `DATABASE_URL`          | `postgresql+asyncpg://...` connection string       |
| `GROQ_API_KEY`          | Groq API key                                       |
| `EMBEDDING_MODEL`       | Default: `sentence-transformers/all-MiniLM-L6-v2`  |
| `EMBEDDING_DIMENSIONS`  | Default: `384` — must match the `vector(N)` column |
| `FRONTEND_URL`          | Used for CORS                                      |
| `CLOUDINARY_CLOUD_NAME` | Cloudinary account identifier                      |
| `CLOUDINARY_API_KEY`    | Cloudinary API key                                 |
| `CLOUDINARY_API_SECRET` | Cloudinary API secret                              |

---

## 13. Deployment Notes

**Database — Neon (serverless Postgres):**

- Create a project at neon.tech, enable the `vector` extension in the SQL editor (`CREATE EXTENSION IF NOT EXISTS vector;`) — same command used in the Alembic migration, so it's idempotent either way
- Copy the pooled connection string into `DATABASE_URL`, using the `asyncpg` driver prefix: `postgresql+asyncpg://user:pass@ep-xxxx.neon.tech/dbname`
- Neon's **branching** feature is genuinely useful here: create a branch per environment (e.g. `dev`, `staging`) or per test run, so schema/embedding experiments never touch production data — then delete the branch when done
- Neon separates storage/compute and scales to zero when idle, which fits an MVP with bursty, low-frequency traffic (compute wakes on the first request after idle — expect a short cold-start delay)
- Free tier is generous enough for MVP development (multiple projects/branches, a few GB of storage); check Neon's current published limits before relying on it for production load, since free-tier terms change

**API hosting — Render:**

- **Build:** `pip install -r requirements.txt && alembic upgrade head` (migrations run automatically on deploy — never create tables manually)
- **Start:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Docker alternative:** provided `Dockerfile` does the same, reading `$PORT` at runtime
- Only `DATABASE_URL` needs to point at Neon — nothing else in the FastAPI app changes, since Neon is a standard Postgres endpoint
- The embedding model still consumes RAM on the Render Free web service; if that becomes the bottleneck, swap `embeddings.py` to call a hosted embedding API. This is a separate concern from the database, which no longer lives on Render at all.

---

## 14. Media Storage: Cloudinary

Cloudinary replaces raw S3/R2 for all media assets — it's the storage layer for anything that isn't text/JSON in Postgres.

**Add a new service:**

```
app/services/cloudinary_service.py
```

```python
import cloudinary
import cloudinary.uploader

from app.core.config import settings

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,
)


def upload_thumbnail(image_url_or_path: str, video_id: int) -> str:
    result = cloudinary.uploader.upload(
        image_url_or_path,
        folder="youtube-shorts-ai/thumbnails",
        public_id=f"video_{video_id}",
        overwrite=True,
    )
    return result["secure_url"]


def upload_rendered_short(file_path: str, short_id: int) -> dict:
    result = cloudinary.uploader.upload(
        file_path,
        resource_type="video",
        folder="youtube-shorts-ai/shorts",
        public_id=f"short_{short_id}",
        overwrite=True,
    )
    return {
        "url": result["secure_url"],
        "duration": result.get("duration"),
        "thumbnail": cloudinary.CloudinaryImage(result["public_id"]).build_url(
            resource_type="video", format="jpg"
        ),
    }
```

Add to `requirements.txt`:

```
cloudinary
```

**Where Cloudinary plugs into the pipeline:**

| Asset                               | Uploaded when                                                                    | Stored where                                                                              |
| ----------------------------------- | -------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| Video thumbnail                     | On video creation/processing (from YouTube's own thumbnail, or a captured frame) | `videos.thumbnail_url` ← Cloudinary secure URL                                            |
| Rendered Short (MP4)                | Post-MVP, after FFmpeg/rendering step produces a clip                            | New `shorts.video_url` column ← Cloudinary secure URL                                     |
| Auto-generated caption/cover images | Post-MVP, if generating branded cover frames per Short                           | Same `shorts` table or a new `short_assets` table if multiple images per Short are needed |

**Model change needed for the roadmap phase (V2):**

```python
# app/models/short.py — add once rendering exists
video_url: Mapped[str | None] = mapped_column(String(1000))
```

**Why Cloudinary here specifically:**

- On-the-fly video transformations (resizing to 9:16, compression, format conversion) without a separate FFmpeg service for every case
- Automatic thumbnail generation from uploaded video via `resource_type="video"`
- Free tier is workable for MVP testing, same spirit as Render Free — swap for a paid tier once real usage starts
- One less piece of infra to self-host compared to S3 + a CDN + a transcoding step

This replaces the `S3/R2` line from the original roadmap (Section 15) — object storage in this project now means Cloudinary end to end.

---

## 15. Known MVP Limitations (By Design)

- **No video rendering.** The pipeline stops at structured script + source timestamps. TTS, captions, FFmpeg cutting, and MP4 storage are explicitly deferred to a later phase.
- **Synchronous processing.** `POST /videos/{id}/process` currently does transcript fetch + chunking + embedding inline within one HTTP request. This is acceptable for MVP testing but should move to a job-queue pattern (`POST /process` → job created → `GET /jobs/{id}`) before handling longer videos or production traffic.
- **`youtube-transcript-api` version sensitivity.** Its interface has changed across versions — pin a version and test it rather than assuming a fixed method signature.

---

## 16. Recommended Build Order

1. FastAPI skeleton + `/api/health`
2. PostgreSQL + SQLAlchemy + Alembic wiring
3. `pgvector` extension, embedding column, similarity query
4. YouTube ID extraction → transcript fetch → chunking
5. Embedding generation + storage
6. RAG retrieval (multi-query + dedup)
7. Groq: moment-finding
8. Groq: script generation (structured JSON)
9. Persist Shorts + sources, wire up API responses
10. Next.js frontend
11. _(Post-MVP)_ TTS → captions → FFmpeg rendering → storage

---

## 17. Roadmap After MVP

| Phase | Addition                                                                     |
| ----- | ---------------------------------------------------------------------------- |
| V1.1  | Job/status architecture for `/process` (background workers)                  |
| V1.2  | Hosted embedding API to remove local-model RAM pressure                      |
| V2    | TTS voiceover generation                                                     |
| V2    | Auto-captioning synced to script timestamps                                  |
| V2    | FFmpeg-based clip cutting from source video using `short_sources` timestamps |
| V2    | Cloudinary upload of rendered MP4s + auto-thumbnails                         |
| V2.1  | Regeneration history / A-B scoring across Short variants                     |

---

## 18. Development Methodology: Agile-V Model & Sprint Plan

This project follows the **Agile-V model** — V-Model verification/validation discipline (each build phase has a paired test phase, planned up front) executed through **Scrum** (time-boxed sprints, daily standups, review/retro cadence) instead of one long waterfall pass. Every sprint delivers a working increment _and_ its corresponding verification activity, rather than pushing all testing to the end.

### 18.1 The V-Model Mapping

```
Requirements Analysis ───────────────────────────► Acceptance Testing
       System Design ─────────────────────────► System Testing
            Architecture Design ─────────► Integration Testing
                 Module Design ───────► Unit Testing
                          Implementation
```

Each left-side phase is paired with its right-side verification counterpart, defined _before_ coding starts for that phase — that pairing is planned during Sprint Planning and confirmed during Sprint Review, not bolted on afterward.

### 18.2 Sprint Structure (2-week sprints, adjust to team velocity)

| Sprint                            | V-Model Phase (build)                         | V-Model Phase (verify, planned in parallel)    | Scrum Ceremonies                                                  |
| --------------------------------- | --------------------------------------------- | ---------------------------------------------- | ----------------------------------------------------------------- |
| **Sprint 0 — Inception**          | Requirements Analysis                         | Acceptance Test Planning                       | Backlog creation, Sprint 0 planning                               |
| **Sprint 1 — Foundation**         | System Design                                 | System Test Planning                           | Sprint Planning, Daily Scrum, Review, Retro                       |
| **Sprint 2 — Data Layer**         | Architecture Design                           | Integration Test Planning                      | Sprint Planning, Daily Scrum, Review, Retro                       |
| **Sprint 3 — Ingestion Pipeline** | Module Design (transcript/chunking)           | Unit Test Planning                             | Sprint Planning, Daily Scrum, Review, Retro                       |
| **Sprint 4 — RAG Core**           | Module Design (embeddings/retrieval)          | Unit Testing                                   | Sprint Planning, Daily Scrum, Review, Retro                       |
| **Sprint 5 — AI Generation**      | Implementation (Groq integration)             | Unit Testing                                   | Sprint Planning, Daily Scrum, Review, Retro                       |
| **Sprint 6 — API Surface**        | Implementation (REST endpoints)               | Integration Testing                            | Sprint Planning, Daily Scrum, Review, Retro                       |
| **Sprint 7 — Media & Storage**    | Implementation (Cloudinary, Neon prod config) | System Testing                                 | Sprint Planning, Daily Scrum, Review, Retro                       |
| **Sprint 8 — Hardening & UAT**    | Bug fixing, performance pass                  | Acceptance Testing (against Sprint 0 criteria) | Sprint Planning, Daily Scrum, Review, Retro, **Release Sign-off** |

### 18.3 Detailed Sprint Backlog

**Sprint 0 — Inception & Requirements**

- Define user stories: submit video, process transcript, generate Shorts, regenerate a Short
- Write acceptance criteria for each story (this becomes the Sprint 8 UAT checklist)
- Confirm tech stack: FastAPI, Neon Postgres + pgvector, Groq, Cloudinary, Render
- Deliverable: Product backlog, acceptance criteria doc, architecture diagram (Section 4)

**Sprint 1 — Foundation**

- `/api/health` endpoint
- FastAPI app skeleton, `core/config.py`, `core/database.py`
- Neon project + branch setup, Alembic wiring
- System test plan: what "the system is up" means end-to-end
- Deliverable: deployable skeleton on Render, connected to Neon

**Sprint 2 — Data Layer**

- All SQLAlchemy models (`Video`, `TranscriptChunk`, `Short`, `ShortSource`)
- Alembic migration incl. `CREATE EXTENSION vector`, HNSW index (Section 7 DDL)
- Integration test plan: model ↔ DB round-trip tests
- Deliverable: schema live on Neon, migrations reproducible on a fresh branch

**Sprint 3 — Ingestion Pipeline**

- `youtube.py` (video ID extraction), `transcript.py` (fetch), `chunker.py` (clean + time-aware chunking)
- Unit tests: URL parsing edge cases, chunk boundary correctness
- Deliverable: `POST /videos` + `POST /videos/{id}/process` working against real YouTube URLs

**Sprint 4 — RAG Core**

- `embeddings.py` (local model), `vector_store.py` (pgvector writes), `rag.py` (similarity search + multi-query retrieval + dedup)
- Unit tests: embedding dimension consistency, similarity ordering, dedup correctness
- Deliverable: `GET /videos/{id}/chunks` returns chunks with populated embeddings; manual similarity queries return sane results

**Sprint 5 — AI Generation**

- `groq_service.py`, `prompts/moments.py`, `prompts/shorts.py`, structured JSON output parsing
- Unit tests: prompt-building functions, JSON schema validation of Groq responses, grounding checks (no invented timestamps)
- Deliverable: given a fixed candidate set, the pipeline reliably returns valid Short JSON

**Sprint 6 — API Surface**

- `POST /shorts/generate`, `GET /shorts`, `GET /shorts/{id}`, `POST /shorts/{id}/regenerate`
- Integration tests: full flow from video submission → generated Shorts, including failure paths (`FAILED` status handling)
- Deliverable: complete documented API, all endpoints in Section 11 live and testable via `/docs`

**Sprint 7 — Media & Storage**

- `cloudinary_service.py` (thumbnail + rendered-clip upload), Neon production branch + connection pooling review
- System tests: end-to-end run against production-like Neon branch and Cloudinary account, load/timeout checks around the synchronous `/process` call
- Deliverable: thumbnails populated automatically; storage layer ready for post-MVP rendering work

**Sprint 8 — Hardening & UAT**

- Bug bash, error-handling pass, logging/observability check
- Acceptance testing against Sprint 0 criteria with real stakeholders/users
- Deliverable: Release candidate, sign-off, tagged version for deployment

### 18.4 Scrum Ceremonies (applied every sprint from Sprint 1 onward)

| Ceremony             | Cadence         | Purpose                                                                                        |
| -------------------- | --------------- | ---------------------------------------------------------------------------------------------- |
| Sprint Planning      | Start of sprint | Select backlog items, define sprint goal + Definition of Done, confirm the paired V&V activity |
| Daily Scrum          | Daily, 15 min   | Progress, blockers, alignment                                                                  |
| Backlog Refinement   | Mid-sprint      | Groom upcoming stories, re-estimate, split oversized items                                     |
| Sprint Review        | End of sprint   | Demo the working increment, gather feedback                                                    |
| Sprint Retrospective | End of sprint   | What worked / what didn't / action items for next sprint                                       |

### 18.5 Definition of Done (applies to every sprint)

- Code merged with passing tests at the level specified by that sprint's V-Model pairing (unit / integration / system / acceptance)
- Migrations applied cleanly to a fresh Neon branch
- Endpoint(s) documented and visible in `/docs`
- No secrets committed; `.env.example` updated if new variables were introduced
- Sprint Review demo completed and accepted by the product owner

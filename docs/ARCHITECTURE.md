# Getitright Architecture and System Design Specification

## 1. System Overview

Getitright is a high-concurrency, cross-platform polling and survey ecosystem engineered for organizations, academic institutions, enterprises, and individual respondents. The system is designed to handle high-velocity vote ingestion, structured poll track management, multi-step qualitative surveys, and real-time consensus broadcasting with sub-5 millisecond latency.

---

## 2. Technology Stack and Feature-First Architecture

The architecture enforces a strict Feature-First separation of concerns across all platform layers:

```
getitright/
|-- backend/                       # Python (FastAPI) API & Orchestration
|   `-- api/
|       |-- core/                  # Database, Config, Security, JWT
|       |-- middleware/            # Rate Limiting, CORS, Auth Validation
|       `-- features/
|           |-- auth/              # Registration, Login, Role Verification
|           |-- polls/             # Polls CRUD, Voting Rules, Expiry
|           |-- surveys/           # Multi-question Surveys, Question Logic
|           |-- analytics/         # Aggregated Telemetry, Metrics
|           `-- users/             # Profile and Permissions
|
|-- engine/                        # Rust Real-Time High-Throughput Ingestion Engine
|   `-- src/
|       |-- main.rs                # Async Tokio runtime entrypoint
|       |-- ws_handler.rs          # WebSocket connection pool and broadcasts
|       |-- vote_processor.rs      # Atomic in-memory tallying and lockless ringbuffer
|       `-- analytics.rs           # Real-time rate calculation (velocity/sec)
|
|-- native/                        # C and C++ High Performance Modules
|   |-- pdf_export/                # C Module: Direct PDF report generation
|   `-- image_processor/           # C++ Module: SIMD/AVX image watermark and optimization
|
|-- web/                           # Web Platform (Vanilla CSS + HTML5 + JS Engine)
|   |-- index.html                 # Page 1: Landing Page with Role-Based Routing
|   |-- pages/
|   |   |-- auth.html              # Page 2: Split-screen Role-Based Authentication
|   |   |-- vote.html              # Page 5: Public Real-Time Community Polls Feed
|   |   `-- surveys.html           # Page 6: Public Survey Explorer and Step-by-Step Taker
|   |-- console/
|   |   |-- dashboard.html         # Page 3: Organization KPI Dashboard and Activity
|   |   |-- polls.html             # Page 4: Organization Poll Tracks Manager
|   |   |-- surveys.html           # Organization Surveys Builder and Manager
|   |   `-- analytics.html         # Organization Real-Time Telemetry and PDF Export
|   |-- css/
|   |   |-- index.css              # Core design tokens, dark neon theme, variables
|   |   `-- pages.css              # Comprehensive component and layout stylesheet
|   `-- js/
|       |-- core/
|       |   |-- app.js             # Core Application Engine, Toasts, Modals
|       |   `-- icons.js           # Pure SVG Icon System (Zero Emojis)
|       `-- features/
|
|-- mobile/                        # Cross-Platform Flutter + Dart Mobile App
|   |-- pubspec.yaml               # Dependencies
|   `-- lib/
|       |-- main.dart              # Entrypoint and Root Navigation Coordinator
|       |-- core/
|       |   |-- theme/             # Dark Neon Palette, Typography, Corner Radii
|       |   |-- network/           # HTTP API Client and WebSocket Stream Client
|       |   `-- models/            # Immutable Data Models
|       `-- features/
|           |-- auth/              # Mobile Authentication & Role Selection
|           |-- polls/             # Interactive Poll Feed & Live Animated Bars
|           |-- surveys/           # Multi-step Survey Taking Wizard
|           `-- dashboard/         # Mobile Organization Console Overview
|
|-- shared/
|   `-- proto/
|       `-- poll_events.proto      # Canonical Protobuf Schema for cross-service events
|
`-- docs/
    |-- ARCHITECTURE.md            # System Architecture and Route Design
    `-- WORKFLOW_DIAGRAMS.md       # Mermaid Workflow and Data Pipeline Diagrams
```

---

## 3. The 6 Production Web Pages Plan

### Page 1: Landing Page (`web/index.html`)
- **Target Audience:** Unauthenticated visitors, enterprises, universities, individual voters.
- **Key Capabilities:**
  - Hero banner with live platform pulse.
  - Role-based redirect selector cards:
    - Route A: "Organization / Institution" -> routes to registration configured for Organization Console.
    - Route B: "Voter / Participant" -> routes to public participation feed.
  - Interactive feature cards, platform statistics (2,400+ polls, 84k+ votes, 320+ orgs).
  - SVG icon-driven illustrations with zero emojis.

### Page 2: Authentication & Role Gate (`web/pages/auth.html`)
- **Target Audience:** All registering and returning users.
- **Key Capabilities:**
  - Split-screen layout: left form panel, right platform capability showcase.
  - Dynamic Role Toggle:
    - Organization: exposes Institution Name, Org Type (Corporate, University, Community DAO), sets `gir_role='org'`.
    - Voter / Participant: streamlined email or anonymous sign-up, sets `gir_role='user'`.
  - Automatic post-authentication redirection:
    - `org` -> `web/console/dashboard.html`
    - `user` -> `web/pages/vote.html`

### Page 3: Organization Console Dashboard (`web/console/dashboard.html`)
- **Target Audience:** Verified institutions and poll administrators.
- **Key Capabilities:**
  - High-level metric KPI cards: Total Responses, Active Poll Tracks, Avg Completion Rate, Ingestion Velocity.
  - Active poll track cards with completion percentage bars and team participant avatars.
  - Real-time recent activity stream and platform status.
  - Quick action to spawn new poll tracks or trigger analytics.

### Page 4: Organization Poll Tracks Manager (`web/console/polls.html`)
- **Target Audience:** Organizations grouping polls into targeted tracks.
- **Key Capabilities:**
  - Track clustering: Allows grouping sequential or thematic polls together (e.g. "Q4 Product Roadmap", "Customer Sentiment").
  - Status filters: Active, Draft, Archived.
  - Modal builder: Add title, track category, connected polls, and release dates.

### Page 5: Public Live Polls Feed (`web/pages/vote.html`)
- **Target Audience:** Registered voters and anonymous respondents.
- **Key Capabilities:**
  - Category filters: Engineering, Architecture, Governance, Community.
  - Interactive Poll Cards: One-click voting updates visual percentage bars instantly with smooth CSS transitions.
  - Real-time vote count incrementation with WebSocket synchronization badge.
  - Featured organization tracks sidebar.

### Page 6: Public Survey Response Wizard (`web/pages/surveys.html`)
- **Target Audience:** Respondents answering detailed surveys.
- **Key Capabilities:**
  - Clean card directory of available institutional surveys.
  - Interactive multi-step wizard modal (Step 1 of N progress bar, radio questions, rating scale, text comments).
  - Instant submission and verification receipt.

### Supporting Console Pages:
- `web/console/surveys.html`: Organization survey authoring, question tree creation, draft saving, publishing.
- `web/console/analytics.html`: Real-time ingestion velocity SVG chart, platform breakdown (Web, iOS, Android), export report via native C module.

---

## 4. Visual Design System and Aesthetic Tokens

The design follows a dark mode palette with neon green accents, glassmorphic headers, and crisp geometric cards matching the provided visual requirements:

| Design Token | Hex / CSS Variable | Purpose |
|---|---|---|
| Background Primary | `#0D0D0D` / `--bg-primary` | Root document canvas |
| Background Card | `#1A1A2E` / `--bg-card` | Container cards, panels, list items |
| Background Elevated | `#16213E` / `--bg-elevated` | Input fields, active pills, table headers |
| Accent Primary | `#00E676` / `--accent-primary` | Vibrant neon green for CTAs, active meters, glow |
| Accent Glow | `rgba(0, 230, 118, 0.25)` | Drop shadows, focus halos, pulse dots |
| Text Primary | `#FFFFFF` / `--text-primary` | Main headings, option labels, titles |
| Text Secondary | `#A0A0B0` / `--text-secondary` | Subtitles, timestamps, metadata |
| Border | `#2A2A3E` / `--border-color` | Dividers, card strokes, outlines |
| Success | `#00E676` | Confirmation toasts, positive deltas |
| Warning | `#FFD740` | Draft status, notice badges |
| Error | `#FF5252` | Validation alerts, network failures |

### Zero Emojis Policy
In compliance with strict engineering constraints, no emojis are used in the codebase, database entries, API responses, terminal logs, or UI elements. All visual cues use custom inline SVG icons defined in `web/js/core/icons.js` and standard vector `IconData` in Flutter.

---

## 5. Scalability and Production Readiness

1. **Rust Ingestion Engine (`engine/`):**
   - Built on Tokio async I/O.
   - Atomic counters (`AtomicU64`) and lockless ringbuffers for processing up to 250,000 votes per second on commodity cloud hardware.
   - Non-blocking broadcasts to connected WebSocket clients via Tokio broadcast channels.

2. **Native C/C++ Performance Modules (`native/`):**
   - `pdf_export.c`: Generates vector PDF summary reports directly without headless browser overhead or Node dependencies.
   - `image_proc.cpp`: SIMD-optimized processing for survey image attachments and organization branding assets.

3. **Cross-Platform Synchronization:**
   - Real-time updates delivered concurrently to Web and Flutter mobile applications using standard WebSocket channels with fallback polling to FastAPI.

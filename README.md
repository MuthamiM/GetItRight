# GetItRight (PollTrack) Platform

**GetItRight (PollTrack)** is a high-integrity, tamper-evident polling, survey, and election verification platform. Designed for transparency, speed, and privacy, GetItRight provides real-time community polling, election observation verification, and cryptographic auditability across mobile, web, and backend services.

---

## 🌟 Key Features & Highlights

- **Real-Time Polls & Surveys (Mobile & Web)**:
  - Interactive voting with real-time percentage breakdowns, animated pie charts, and status filtering (`ALL`, `CLOSING`, `ENDED`).
  - Seamless back-to-top navigation with smart state management and toast notifications when already at top.
  - Vote state persistence via local storage so page reloads or feed refreshes do not erase cast votes.
  - Expiry and auto-archiving logic (5-hour post-vote / post-countdown retention rules).

- **Client-Side Cryptographic Verification**:
  - Zero-knowledge evidence hash computation using the native Web Crypto API (`SHA-256`).
  - Visitor photos and sensitive documents never leave the local device; hashes are checked against published ledger checkpoints and Merkle trees.

- **Interactive Observer Simulator**:
  - Responsive mobile observer capture simulator (`mobile-app.html`) demonstrating skew/glare detection, ECDSA P-256 hardware key signing simulation, encrypted outbox delivery, and silent duress alerts.

- **Dual-Currency & Tiered Access**:
  - Native dual-currency pricing toggle (Kenyan Shilling `KES` and `USD`).
  - Role-based navigation (`Poll Creator`, `Observer`, `Reviewer`, `Auditor`, `Org Admin`, `Platform Admin`) with explicit tier gating (`Free`, `Pro`, `Organisation`, `Election`).

---

## 🏗️ Project Architecture & Repository Structure

```
POLL/
├── backend/                  # API Services
│   ├── api/                  # Python FastAPI service (Auth, Polls, Surveys, WebSocket)
│   ├── csharp/               # C# .NET API service (Enterprise services & ledger)
│   └── Dockerfile            # Backend production container
├── mobile/                   # Flutter Mobile Application
│   ├── lib/                  # Application source code
│   │   ├── core/             # API client, network models, WebSocket client, themes
│   │   ├── features/         # Auth, Polls, Surveys, Org Dashboard, Settings
│   │   └── main.dart         # Flutter entry point & bottom navigation bar
│   ├── android/              # Android native manifest & build config
│   └── pubspec.yaml          # Flutter dependencies
├── web/                      # Web Frontend & Verifier Tooling
│   ├── index.html            # Core landing portal
│   ├── landing.html          # Product landing page
│   ├── pricing.html          # Tiered pricing & dual-currency conversion
│   ├── verifier.html         # Client-side SHA-256 evidence verifier
│   └── mobile-app.html       # Web-based observer mobile simulator
├── engine/                   # Cryptographic engine & Merkle tree verifiers
├── shared/                   # Shared schemas, DTOs, and utility modules
├── docker-compose.yml        # Multi-container orchestration
├── ASSUMPTIONS.md            # Architectural and design decision record
└── README.md                 # Project documentation
```

---

## 🚀 Quick Start & Installation

### Prerequisites
- **Flutter SDK**: 3.x or higher (for mobile development)
- **Python**: 3.10+ (for FastAPI backend)
- **.NET SDK**: 8.0+ (for C# service, optional)
- **Docker & Docker Compose**: (for containerized deployment)

---

### 1. Running via Docker Compose

To start the full stack (FastAPI Backend + Nginx Web Server):

```bash
docker-compose up --build -d
```

- **Web Portal**: Navigate to `http://localhost:8888` or `http://localhost:8090`
- **Backend API**: Accessible at `http://localhost:5000`

---

### 2. Running the Python Backend Locally

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --reload --host 0.0.0.0 --port 5000
```

---

### 3. Running the Mobile App (Flutter)

```bash
cd mobile
flutter pub get
flutter run
```

To build a release APK for Android:

```bash
cd mobile
flutter build apk --release
```

---

## 🔒 Security & Privacy Commitments

1. **Zero Raw Photo Transmission**: Observer photos in evidence workflows are hashed locally in the browser/client; raw images are never sent to third-party endpoints.
2. **Immutability Rules**: Ledger entries cannot be updated or deleted in place. Corrections create new superseding records backed by mandatory cryptographic signatures and justifications.
3. **JWT Authentication & Role Gating**: All protected API endpoints validate signed JWT access tokens with strict claims enforcement for organization and admin features.

---

## 📜 License & Compliance

All rights reserved. GetItRight / PollTrack platform code adheres to production-grade engineering standards with strict zero-emoji, high-contrast, accessible UI standards.

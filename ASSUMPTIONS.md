# PollTrack: Architectural & Design Assumptions

This document lists sensible design and implementation choices made where the specification was silent or allowed agent discretion.

---

### 1. Plan Catalog & Pricing
- **Assumption:** Kenya pricing is defined by the server plan catalog: Starter is free, Pro is KES 499 per 30 days, and Organization is KES 899 per 30 days. Election is retained only for existing legacy accounts and is not offered for new subscriptions.
- **Implementation:** Signup and pricing screens load prices and quotas from the public server catalog. No exchange-rate estimate is shown.

### 2. Client-Side Cryptographic Verifier
- **Assumption:** To satisfy the strict privacy requirement ("the visitor's photo never leaves their device"), file hashing is performed client-side using the native browser Web Crypto API (`crypto.subtle.digest('SHA-256')`).
- **Implementation:** When an observer photo is dropped into the dropzone or a hash is pasted, the browser computes the 256-bit hash locally before querying the published ledger checkpoints and Merkle trees.

### 3. Role-Based Navigation & Tier Gating
- **Assumption:** To allow intuitive demonstration of all roles (`Poll Creator`, `Observer`, `Reviewer`, `Auditor`, `Org Admin`, `Platform Admin`) and tiers (`Starter`, `Pro`, `Organization`), interactive role and plan switchers are provided in the console shell topbar. Existing Election accounts remain readable as legacy records.
- **Implementation:** 
  - On `Free` plan, election-grade items (`Stations`, `Observers`, `Anomalies`, `Disputes`, `Checkpoints`) remain fully visible in the sidebar but are tagged with a purple `Locked` badge.
  - Clicking any gated feature opens the upgrade flow explaining the tier requirement.
  - The UI strictly prevents editing or deleting ledger records across all roles; corrections generate new superseding versions with mandatory justification.

### 4. Interactive Mobile Observer Simulator
- **Assumption:** For testing the mobile observer capture workflow on web browsers, a phone-first responsive simulator (`mobile-app.html`) demonstrates the camera quality gate (blur, glare, skew detection), hardware key signing simulation (ECDSA P-256), arithmetic sum validation, encrypted outbox, and silent duress trigger.

### 5. Multi-Language (i18n) Engine
- **Assumption:** English (`en`) and Kiswahili (`sw`) strings are externalized in `web/js/core/i18n.js` with instant runtime switching without full-page reloads.

### 6. Zero Emojis Compliance
- **Assumption:** In accordance with production-grade engineering constraints, all UI elements, status badges, console logs, and reports use pure SVG icons from `Icons` system, paired with descriptive text labels.

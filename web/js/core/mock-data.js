/* =============================================================
   POLLTRACK — Canonical Mock Data Store
   Adheres strictly to Section 8 Data Model.
   Realistic sample data with no real election/org fabrication.
   Zero emojis.
   ============================================================= */

const MockData = {
  currentOrg: {
    id: "org-kenya-civic",
    name: "Civic Transparency Initiative",
    plan: "election", // "free", "pro", "org", "election"
    limits: {
      activePolls: 9999,
      responsesPerPoll: 500000,
      stationsAllocated: 250,
      stationsReported: 242,
    },
  },

  currentUser: {
    id: "usr-01",
    name: "Faith Mwangi",
    role: "reviewer", // "creator", "observer", "reviewer", "auditor", "admin", "platform"
    mfaEnabled: true,
    orgId: "org-kenya-civic",
  },

  stations: [
    {
      id: "ST-042",
      name: "St. Jude Primary Hall (PS-042)",
      region: "Kiambu Central",
      registeredVoters: 750,
      status: "Verified",
      observerIds: ["obs-01", "obs-02"],
      geofence: "-1.1714, 36.8356 (radius 50m)",
      submissionsCount: 2,
      flags: 0,
      tally: { candidateA: 342, candidateB: 289, candidateC: 78, spoilt: 12, total: 721 },
      lastUpdated: "8 min ago",
      currentCheckpoint: 142,
      entryHash: "0x8f2a93c7e1b4f09d8213ba4e67120cda59e41b7f0129ad8412bc4890cf319a2e"
    },
    {
      id: "ST-108",
      name: "Umoja Community Center (PS-108)",
      region: "Nairobi East",
      registeredVoters: 920,
      status: "Frozen",
      observerIds: ["obs-03", "obs-04"],
      geofence: "-1.2841, 36.8924 (radius 50m)",
      submissionsCount: 2,
      flags: 1,
      tally: { candidateA: 410, candidateB: 395, candidateC: 45, spoilt: 18, total: 868 },
      lastUpdated: "12 min ago",
      currentCheckpoint: 141,
      entryHash: "0x4c91e87f2a1b9c3e5d710842ba67120cda59e41b7f0129ad8412bc4890cf8821"
    },
    {
      id: "ST-019",
      name: "Township Secondary (PS-019)",
      region: "Mombasa Urban",
      registeredVoters: 600,
      status: "Flagged",
      observerIds: ["obs-05"],
      geofence: "-4.0435, 39.6682 (radius 50m)",
      submissionsCount: 1,
      flags: 1,
      tally: { candidateA: 480, candidateB: 62, candidateC: 15, spoilt: 3, total: 560 },
      lastUpdated: "25 min ago",
      currentCheckpoint: 140,
      entryHash: "0x1b7f0129ad8412bc4890cf319a2e8f2a93c7e1b4f09d8213ba4e67120cda59e4"
    },
    {
      id: "ST-230",
      name: "Highway Polytechnic (PS-230)",
      region: "Nakuru West",
      registeredVoters: 840,
      status: "Pending sync",
      observerIds: ["obs-06"],
      geofence: "-0.3031, 36.0800 (radius 50m)",
      submissionsCount: 1,
      flags: 0,
      tally: { candidateA: 310, candidateB: 320, candidateC: 80, spoilt: 10, total: 720 },
      lastUpdated: "3 min ago (SMS fallback)",
      currentCheckpoint: 142,
      entryHash: "0x59e41b7f0129ad8412bc4890cf319a2e8f2a93c7e1b4f09d8213ba4e67120cda"
    },
    {
      id: "ST-311",
      name: "Lakeview Academy (PS-311)",
      region: "Kisumu Central",
      registeredVoters: 550,
      status: "Verified",
      observerIds: ["obs-07"],
      geofence: "-0.0917, 34.7680 (radius 50m)",
      submissionsCount: 1,
      flags: 0,
      tally: { candidateA: 215, candidateB: 260, candidateC: 35, spoilt: 8, total: 518 },
      lastUpdated: "40 min ago",
      currentCheckpoint: 139,
      entryHash: "0x7e1b4f09d8213ba4e67120cda59e41b7f0129ad8412bc4890cf319a2e8f2a93c"
    }
  ],

  observers: [
    {
      id: "obs-01",
      name: "Alice Njeri",
      phone: "+254 712 345 678",
      verified: true,
      mfaStatus: "Hardware Key (FIDO2)",
      stationIds: ["ST-042"],
      devices: [
        {
          id: "dev-pixel-01",
          model: "Google Pixel 8",
          publicKey: "04a29f8c...3e1b7",
          attestation: "trusted",
          lastSeen: "2 min ago",
          revoked: false
        }
      ]
    },
    {
      id: "obs-02",
      name: "Brian Otieno",
      phone: "+254 723 456 789",
      verified: true,
      mfaStatus: "App TOTP",
      stationIds: ["ST-042"],
      devices: [
        {
          id: "dev-sams-02",
          model: "Samsung Galaxy A54",
          publicKey: "04bc12e8...7a9f0",
          attestation: "trusted",
          lastSeen: "7 min ago",
          revoked: false
        }
      ]
    },
    {
      id: "obs-03",
      name: "Charles Mutua",
      phone: "+254 734 567 890",
      verified: true,
      mfaStatus: "Hardware Key (FIDO2)",
      stationIds: ["ST-108"],
      devices: [
        {
          id: "dev-pixel-03",
          model: "Google Pixel 7a",
          publicKey: "04de7108...42ba6",
          attestation: "trusted",
          lastSeen: "12 min ago",
          revoked: false
        }
      ]
    },
    {
      id: "obs-04",
      name: "Diana Wekesa",
      phone: "+254 745 678 901",
      verified: true,
      mfaStatus: "SMS OTP",
      stationIds: ["ST-108"],
      devices: [
        {
          id: "dev-nokia-04",
          model: "Nokia G42 5G",
          publicKey: "048f0129...c4890",
          attestation: "trusted",
          lastSeen: "14 min ago",
          revoked: false
        }
      ]
    }
  ],

  disputes: [
    {
      id: "disp-108",
      stationId: "ST-108",
      stationName: "Umoja Community Center (PS-108)",
      status: "Frozen",
      reason: "Tally count mismatch between Observer Charles Mutua and Observer Diana Wekesa",
      observerA: {
        observerName: "Charles Mutua",
        observerId: "obs-03",
        deviceId: "dev-pixel-03 (Trusted Attestation)",
        capturedAt: "2026-09-30 02:45 UTC (14 min ago)",
        gps: "-1.2840, 36.8925 (Inside geofence - 4m delta)",
        imageHash: "0x8f2a93c7e1b4f09d8213ba4e67120cda59e41b7f0129ad8412bc4890cf319a2e",
        phash: "d41d8cd98f00b204e9800998ecf8427e",
        qualityScores: { blur: "98% (Sharp)", glare: "0% (None)", skew: "1.2 deg (Valid)" },
        tally: { candidateA: 410, candidateB: 395, candidateC: 45, spoilt: 18, total: 868 },
        arithmeticValid: true
      },
      observerB: {
        observerName: "Diana Wekesa",
        observerId: "obs-04",
        deviceId: "dev-nokia-04 (Trusted Attestation)",
        capturedAt: "2026-09-30 02:47 UTC (12 min ago)",
        gps: "-1.2842, 36.8922 (Inside geofence - 9m delta)",
        imageHash: "0x3e1b7f0129ad8412bc4890cf319a2e8f2a93c7e1b4f09d8213ba4e67120cda59",
        phash: "d41d8cd98f00b204e9800998ecf8427e",
        qualityScores: { blur: "94% (Sharp)", glare: "2% (Low)", skew: "2.1 deg (Valid)" },
        tally: { candidateA: 410, candidateB: 415, candidateC: 45, spoilt: 18, total: 888 },
        arithmeticValid: true // Note: candidateB has 415 vs 395!
      },
      differingFields: [
        { field: "Candidate B Count", valA: 395, valB: 415, diff: "+20 votes" },
        { field: "Total Valid Votes", valA: 850, valB: 870, diff: "+20 votes" },
        { field: "Grand Total Cast", valA: 868, valB: 888, diff: "+20 votes" }
      ]
    }
  ],

  ledgerEntries: [
    {
      seq: 14208,
      stationId: "ST-042",
      observerId: "obs-01",
      deviceId: "dev-pixel-01",
      counts: { candidateA: 342, candidateB: 289, candidateC: 78 },
      spoilt: 12,
      total: 721,
      imageSha256: "0x8f2a93c7e1b4f09d8213ba4e67120cda59e41b7f0129ad8412bc4890cf319a2e",
      phash: "e3b0c44298fc1c149afbf4c8996fb924",
      gps: "-1.1714, 36.8356",
      capturedAt: "2026-09-30 02:40:12 UTC",
      deviceSigStatus: "Hardware Key Valid (ECDSA P-256)",
      prevHash: "0x7a1b9c3e5d710842ba67120cda59e41b7f0129ad8412bc4890cf88214c91e8",
      entryHash: "0x91e87f2a1b9c3e5d710842ba67120cda59e41b7f0129ad8412bc4890cf88214c",
      checkpoint: 142,
      status: "Verified",
      supersedes: null,
      reason: null,
      inclusionProof: [
        { level: 1, position: "right", hash: "0x4b7f0129ad8412bc4890cf319a2e8f2a93c7e1b4f09d8213ba4e67120cda59e4" },
        { level: 2, position: "left", hash: "0x12bc4890cf319a2e8f2a93c7e1b4f09d8213ba4e67120cda59e44b7f0129ad84" },
        { level: 3, position: "right", hash: "0x93c7e1b4f09d8213ba4e67120cda59e44b7f0129ad8412bc4890cf319a2e8f2a" }
      ]
    },
    {
      seq: 14207,
      stationId: "ST-108",
      observerId: "obs-03",
      deviceId: "dev-pixel-03",
      counts: { candidateA: 410, candidateB: 395, candidateC: 45 },
      spoilt: 18,
      total: 868,
      imageSha256: "0x4c91e87f2a1b9c3e5d710842ba67120cda59e41b7f0129ad8412bc4890cf8821",
      phash: "d41d8cd98f00b204e9800998ecf8427e",
      gps: "-1.2840, 36.8925",
      capturedAt: "2026-09-30 02:35:45 UTC",
      deviceSigStatus: "Hardware Key Valid (ECDSA P-256)",
      prevHash: "0x5d710842ba67120cda59e41b7f0129ad8412bc4890cf88214c91e87a1b9c3e",
      entryHash: "0x7a1b9c3e5d710842ba67120cda59e41b7f0129ad8412bc4890cf88214c91e8",
      checkpoint: 141,
      status: "Frozen",
      supersedes: null,
      reason: null
    }
  ],

  checkpoints: [
    {
      number: 142,
      treeSize: 14210,
      root: "0x00e676a91e87f2a1b9c3e5d710842ba67120cda59e41b7f0129ad8412bc4890c",
      signedAt: "2026-09-30 02:45:00 UTC (15 min ago)",
      signatureStatus: "Ed25519 Platform Authority (Verified)",
      anchors: [
        { target: "Bitcoin Block #884120", txId: "f83a...91bc", confirmations: 3, status: "Anchored" },
        { target: "OpenTimestamps Calendar", receipt: "ots-884120", status: "Anchored" },
        { target: "Ethereum Sepolia #5419082", txId: "0x3b1c...4a20", confirmations: 64, status: "Anchored" }
      ],
      mirrors: ["mirror-fra.polltrack.io (Synced)", "mirror-nbo.polltrack.io (Synced)"]
    },
    {
      number: 141,
      treeSize: 13950,
      root: "0x3e5d710842ba67120cda59e41b7f0129ad8412bc4890cf88214c91e87a1b9c00",
      signedAt: "2026-09-30 02:15:00 UTC (45 min ago)",
      signatureStatus: "Ed25519 Platform Authority (Verified)",
      anchors: [
        { target: "Bitcoin Block #884117", txId: "e71b...842a", confirmations: 6, status: "Anchored" },
        { target: "OpenTimestamps Calendar", receipt: "ots-884117", status: "Anchored" }
      ],
      mirrors: ["mirror-fra.polltrack.io (Synced)", "mirror-nbo.polltrack.io (Synced)"]
    }
  ],

  anomalies: [
    {
      id: "anom-01",
      stationId: "ST-019",
      rule: "Turnout Spike vs Regional Baseline",
      severity: "High",
      evidence: "Station turnout is 93.3% while surrounding 14 stations average 68.2% (+25.1% variance).",
      status: "Open",
      assignee: "Faith Mwangi (Reviewer)",
      time: "25 min ago"
    },
    {
      id: "anom-02",
      stationId: "ST-108",
      rule: "Dual-Observer Count Variance",
      severity: "High",
      evidence: "Observer A records 395 for Candidate B, Observer B records 415 (20 vote difference).",
      status: "In Review",
      assignee: "Faith Mwangi (Reviewer)",
      time: "14 min ago"
    },
    {
      id: "anom-03",
      stationId: "ST-088",
      rule: "Last-Digit (Benford) Distribution Variance",
      severity: "Medium",
      evidence: "Sub-tally round numbers: 6 out of 8 candidates end with zero or five (p = 0.008).",
      status: "Open",
      assignee: "Unassigned",
      time: "1 hour ago"
    }
  ],

  auditLog: [
    {
      id: "aud-9021",
      actor: "Faith Mwangi (Reviewer)",
      action: "STATION_FREEZE",
      target: "Station PS-108",
      time: "2026-09-30 02:48:15 UTC",
      source: "Console (IP 102.134.88.12 - 2FA active)",
      prevEventHash: "0x12a8...4f1e",
      eventHash: "0x88fc...992a"
    },
    {
      id: "aud-9020",
      actor: "Diana Wekesa (Observer)",
      action: "SUBMIT_STATION_RESULT",
      target: "Station PS-108 / Entry #14207",
      time: "2026-09-30 02:47:02 UTC",
      source: "Mobile App (Nokia G42 5G - Attested)",
      prevEventHash: "0x992a...e3b0",
      eventHash: "0x12a8...4f1e"
    },
    {
      id: "aud-9019",
      actor: "Charles Mutua (Observer)",
      action: "SUBMIT_STATION_RESULT",
      target: "Station PS-108 / Entry #14206",
      time: "2026-09-30 02:45:18 UTC",
      source: "Mobile App (Pixel 7a - Hardware Signed)",
      prevEventHash: "0x4b7f...91bc",
      eventHash: "0x992a...e3b0"
    },
    {
      id: "aud-9018",
      actor: "System Engine (Checkpoint Daemon)",
      action: "CHECKPOINT_PUBLISH",
      target: "Merkle Root #142 (Tree Size 14,210)",
      time: "2026-09-30 02:45:00 UTC",
      source: "Engine Core (Ed25519 Key #01)",
      prevEventHash: "0x319a...7e1b",
      eventHash: "0x4b7f...91bc"
    }
  ],

  // 17 Engines Specification (Section 6)
  engines: [
    { id: 1, name: "Poll Engine", purpose: "Simple polls, counts & tier limit enforcement", status: "Healthy", throughput: "420 req/s", errorRate: "0.00%", lag: "0 ms", lastEvent: "2s ago" },
    { id: 2, name: "Identity & Access Engine", purpose: "MFA, observer verification & key revocation", status: "Healthy", throughput: "85 req/s", errorRate: "0.00%", lag: "1 ms", lastEvent: "10s ago" },
    { id: 3, name: "Entitlement & Billing Engine", purpose: "Plan tiers, feature gates & Daraja M-Pesa", status: "Healthy", throughput: "12 req/s", errorRate: "0.00%", lag: "0 ms", lastEvent: "1m ago" },
    { id: 4, name: "Capture & Quality Engine (Native C/C++)", purpose: "Blur/glare/skew checks, perceptual hash & QR", status: "Healthy", throughput: "28 frames/s", errorRate: "0.01%", lag: "4.2 ms", lastEvent: "3s ago" },
    { id: 5, name: "Validation Engine", purpose: "Arithmetic and business rules on entered results", status: "Healthy", throughput: "140 req/s", errorRate: "0.00%", lag: "0.8 ms", lastEvent: "3s ago" },
    { id: 6, name: "Signing & Crypto Engine", purpose: "Hardware ECDSA P-256 & server Ed25519 proofs", status: "Healthy", throughput: "95 ops/s", errorRate: "0.00%", lag: "1.4 ms", lastEvent: "3s ago" },
    { id: 7, name: "Attestation Engine", purpose: "Verify hardware keystore, mock GPS & anti-root", status: "Healthy", throughput: "35 checks/s", errorRate: "0.05%", lag: "2.1 ms", lastEvent: "12s ago" },
    { id: 8, name: "Sync Engine (Offline First)", purpose: "Encrypted outbox, retries & SMS fallback", status: "Healthy", throughput: "48 msgs/s", errorRate: "0.00%", lag: "40 ms", lastEvent: "4s ago" },
    { id: 9, name: "Ledger Engine", purpose: "Append-only hash chain & versioned corrections", status: "Healthy", throughput: "620 ops/s", errorRate: "0.00%", lag: "0.5 ms", lastEvent: "1s ago" },
    { id: 10, name: "Reconciliation Engine", purpose: "Multi-observer cross-comparison & mismatch flags", status: "Healthy", throughput: "18 pairs/s", errorRate: "0.00%", lag: "2.8 ms", lastEvent: "8s ago" },
    { id: 11, name: "Anomaly Engine", purpose: "Benford law, turnout spikes & neighbour variance", status: "Healthy", throughput: "24 evaluations/s", errorRate: "0.00%", lag: "6.0 ms", lastEvent: "15s ago" },
    { id: 12, name: "Dispute Workflow Engine", purpose: "Flag, freeze, review & create new ledger versions", status: "Healthy", throughput: "2 events/s", errorRate: "0.00%", lag: "0.4 ms", lastEvent: "12m ago" },
    { id: 13, name: "Checkpoint & Anchoring Engine", purpose: "Merkle tree commit, Bitcoin/OTS anchoring", status: "Healthy", throughput: "1 block / 30m", errorRate: "0.00%", lag: "Nominal", lastEvent: "15m ago" },
    { id: 14, name: "Verification Engine (Open Source)", purpose: "In-browser recomputing of roots & proofs", status: "Healthy", throughput: "Client-side", errorRate: "0.00%", lag: "0 ms", lastEvent: "Real-time" },
    { id: 15, name: "Audit-Log Engine", purpose: "Hash-chained immutable administrative trails", status: "Healthy", throughput: "110 events/s", errorRate: "0.00%", lag: "0.9 ms", lastEvent: "2s ago" },
    { id: 16, name: "Notification & Alert Engine", purpose: "Duress alerts, threshold flags & SMS broadcast", status: "Healthy", throughput: "15 alerts/s", errorRate: "0.00%", lag: "12 ms", lastEvent: "12m ago" },
    { id: 17, name: "Reporting & Export Engine", purpose: "Native C PDF generation, CSV & certified bundles", status: "Healthy", throughput: "8 jobs/s", errorRate: "0.00%", lag: "1.2s", lastEvent: "4m ago" }
  ]
};

if (typeof module !== 'undefined' && module.exports) {
  module.exports = MockData;
}

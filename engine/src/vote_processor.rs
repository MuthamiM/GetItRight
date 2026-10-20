use std::collections::HashMap;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;
use std::time::{SystemTime, UNIX_EPOCH};

use crossbeam_queue::ArrayQueue;
use parking_lot::RwLock;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

/// Incoming vote submission payload from mobile/web clients or ingestion API.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VotePayload {
    pub poll_id: String,
    pub option_id: String,
    pub option_label: String,
    pub voter_id: String,
    pub voter_name: String,
    pub county: String,
    pub device_name: String,
    pub device_os: String,
    pub timestamp: Option<String>,
}

/// Processed vote record with atomic sequence ID and cryptographic receipt hash.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessedVote {
    pub sequence_id: u64,
    pub payload: VotePayload,
    pub receipt_hash: String,
    pub processed_at_us: u64,
}

/// Snapshot of an option's current tally and vote share percentage.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OptionTallySnapshot {
    pub option_label: String,
    pub votes: u64,
    pub percentage: f64,
}

/// Real-time consensus tally snapshot for a poll.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PollTallySnapshot {
    pub poll_id: String,
    pub total_votes: u64,
    pub options: Vec<OptionTallySnapshot>,
    pub county_distribution: HashMap<String, u64>,
    pub updated_at_us: u64,
}

/// Internal thread-safe atomic state for an active poll.
pub struct PollState {
    pub poll_id: String,
    pub options: RwLock<HashMap<String, Arc<AtomicU64>>>,
    pub counties: RwLock<HashMap<String, Arc<AtomicU64>>>,
    pub total_votes: AtomicU64,
}

impl PollState {
    pub fn new(poll_id: String) -> Self {
        Self {
            poll_id,
            options: RwLock::new(HashMap::new()),
            counties: RwLock::new(HashMap::new()),
            total_votes: AtomicU64::new(0),
        }
    }

    pub fn record_vote(&self, option_label: &str, county: &str) -> u64 {
        // Increment option counter
        {
            let options = self.options.read();
            if let Some(counter) = options.get(option_label) {
                counter.fetch_add(1, Ordering::Relaxed);
            } else {
                drop(options);
                let mut options_mut = self.options.write();
                let counter = options_mut
                    .entry(option_label.to_string())
                    .or_insert_with(|| Arc::new(AtomicU64::new(0)));
                counter.fetch_add(1, Ordering::Relaxed);
            }
        }

        // Increment county counter
        {
            let counties = self.counties.read();
            if let Some(counter) = counties.get(county) {
                counter.fetch_add(1, Ordering::Relaxed);
            } else {
                drop(counties);
                let mut counties_mut = self.counties.write();
                let counter = counties_mut
                    .entry(county.to_string())
                    .or_insert_with(|| Arc::new(AtomicU64::new(0)));
                counter.fetch_add(1, Ordering::Relaxed);
            }
        }

        self.total_votes.fetch_add(1, Ordering::SeqCst) + 1
    }

    pub fn snapshot(&self) -> PollTallySnapshot {
        let total = self.total_votes.load(Ordering::SeqCst);
        let options_read = self.options.read();
        let counties_read = self.counties.read();

        let mut option_snapshots = Vec::new();
        for (label, counter) in options_read.iter() {
            let cnt = counter.load(Ordering::Relaxed);
            let pct = if total > 0 {
                (cnt as f64 / total as f64) * 100.0
            } else {
                0.0
            };
            option_snapshots.push(OptionTallySnapshot {
                option_label: label.clone(),
                votes: cnt,
                percentage: (pct * 10.0).round() / 10.0,
            });
        }

        option_snapshots.sort_by(|a, b| b.votes.cmp(&a.votes));

        let mut county_dist = HashMap::new();
        for (cty, counter) in counties_read.iter() {
            county_dist.insert(cty.clone(), counter.load(Ordering::Relaxed));
        }

        let now_us = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_micros() as u64)
            .unwrap_or(0);

        PollTallySnapshot {
            poll_id: self.poll_id.clone(),
            total_votes: total,
            options: option_snapshots,
            county_distribution: county_dist,
            updated_at_us: now_us,
        }
    }
}

/// Ultra-high performance lock-free in-memory vote processing engine.
pub struct VoteProcessor {
    polls: RwLock<HashMap<String, Arc<PollState>>>,
    ringbuffer: Arc<ArrayQueue<ProcessedVote>>,
    sequence_counter: AtomicU64,
    total_ingested: AtomicU64,
}

impl VoteProcessor {
    pub fn new(capacity: usize) -> Self {
        Self {
            polls: RwLock::new(HashMap::new()),
            ringbuffer: Arc::new(ArrayQueue::new(capacity)),
            sequence_counter: AtomicU64::new(1),
            total_ingested: AtomicU64::new(0),
        }
    }

    /// Process an authenticated citizen ballot with atomic tallying and cryptographic hashing.
    pub fn ingest_vote(&self, payload: VotePayload) -> ProcessedVote {
        let seq = self.sequence_counter.fetch_add(1, Ordering::SeqCst);
        let now_us = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_micros() as u64)
            .unwrap_or(0);

        // Generate cryptographic receipt hash: SHA256(seq:poll_id:option:voter:time)
        let mut hasher = Sha256::new();
        let preimage = format!(
            "{}:{}:{}:{}:{}:{}",
            seq,
            payload.poll_id,
            payload.option_label,
            payload.voter_id,
            payload.county,
            now_us
        );
        hasher.update(preimage.as_bytes());
        let receipt_hash = format!("0x{}", hex::encode(hasher.finalize()));

        // Update in-memory atomic tally
        let poll_state = {
            let polls = self.polls.read();
            if let Some(state) = polls.get(&payload.poll_id) {
                state.clone()
            } else {
                drop(polls);
                let mut polls_mut = self.polls.write();
                polls_mut
                    .entry(payload.poll_id.clone())
                    .or_insert_with(|| Arc::new(PollState::new(payload.poll_id.clone())))
                    .clone()
            }
        };

        poll_state.record_vote(&payload.option_label, &payload.county);
        self.total_ingested.fetch_add(1, Ordering::Relaxed);

        let processed = ProcessedVote {
            sequence_id: seq,
            payload,
            receipt_hash,
            processed_at_us: now_us,
        };

        // Push to lockless ringbuffer (drops oldest if full to avoid blocking ingestion)
        if self.ringbuffer.push(processed.clone()).is_err() {
            let _ = self.ringbuffer.pop();
            let _ = self.ringbuffer.push(processed.clone());
        }

        processed
    }

    /// Retrieve consensus tally snapshot for a specific poll.
    pub fn get_tally(&self, poll_id: &str) -> Option<PollTallySnapshot> {
        let polls = self.polls.read();
        polls.get(poll_id).map(|p| p.snapshot())
    }

    /// Retrieve snapshots for all active polls in the engine.
    pub fn get_all_tallies(&self) -> Vec<PollTallySnapshot> {
        let polls = self.polls.read();
        polls.values().map(|p| p.snapshot()).collect()
    }

    /// Retrieve recent vote audit stream from the lockless ringbuffer.
    #[allow(dead_code)]
    pub fn get_recent_votes(&self, limit: usize) -> Vec<ProcessedVote> {
        let mut votes = Vec::new();
        let len = self.ringbuffer.len();
        let fetch_count = limit.min(len);

        // Read snapshot of recent entries
        for _ in 0..fetch_count {
            if let Some(v) = self.ringbuffer.pop() {
                votes.push(v);
            }
        }

        // Reinsert popped elements to maintain buffer
        for v in &votes {
            let _ = self.ringbuffer.push(v.clone());
        }

        votes.reverse();
        votes
    }

    pub fn total_ingested(&self) -> u64 {
        self.total_ingested.load(Ordering::Relaxed)
    }
}

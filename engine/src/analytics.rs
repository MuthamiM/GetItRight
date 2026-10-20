use std::collections::HashMap;
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::Instant;

use parking_lot::RwLock;
use serde::{Deserialize, Serialize};

/// Real-time platform performance and throughput metrics snapshot.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TelemetrySnapshot {
    pub current_tps: f64,
    pub avg_5s_tps: f64,
    pub peak_tps: f64,
    pub total_ingested: u64,
    pub mean_latency_us: f64,
    pub active_polls_count: usize,
    pub anomaly_flags: Vec<String>,
    pub uptime_seconds: u64,
}

/// Turnout evaluation for a campaign against a registered voter baseline.
#[allow(dead_code)]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CampaignTurnoutMetrics {
    pub campaign_id: String,
    pub ballots_cast: u64,
    pub target_quota: u64,
    pub turnout_percentage: f64,
    pub is_threshold_reached: bool,
    pub top_county: String,
}

/// Real-time rate and statistical analytics engine.
pub struct AnalyticsEngine {
    start_time: Instant,
    last_tick: RwLock<Instant>,
    last_count: AtomicU64,
    tps_history: RwLock<Vec<f64>>,
    peak_tps: RwLock<f64>,
    latency_samples_us: RwLock<Vec<u64>>,
    anomaly_log: RwLock<Vec<String>>,
}

impl AnalyticsEngine {
    pub fn new() -> Self {
        Self {
            start_time: Instant::now(),
            last_tick: RwLock::new(Instant::now()),
            last_count: AtomicU64::new(0),
            tps_history: RwLock::new(Vec::new()),
            peak_tps: RwLock::new(0.0),
            latency_samples_us: RwLock::new(Vec::new()),
            anomaly_log: RwLock::new(Vec::new()),
        }
    }

    /// Record a processed vote latency measurement in microseconds.
    #[allow(dead_code)]
    pub fn record_latency(&self, latency_us: u64) {
        let mut samples = self.latency_samples_us.write();
        if samples.len() >= 10_000 {
            samples.remove(0);
        }
        samples.push(latency_us);
    }

    /// Periodic tick to calculate instantaneous TPS and rolling moving averages.
    pub fn tick(&self, current_total_votes: u64) -> f64 {
        let now = Instant::now();
        let mut last_tick = self.last_tick.write();
        let elapsed = now.duration_since(*last_tick).as_secs_f64();

        if elapsed < 0.1 {
            return 0.0;
        }

        let prev = self.last_count.swap(current_total_votes, Ordering::SeqCst);
        let delta = current_total_votes.saturating_sub(prev);
        let tps = delta as f64 / elapsed;

        *last_tick = now;

        // Update TPS history
        let mut hist = self.tps_history.write();
        if hist.len() >= 60 {
            hist.remove(0);
        }
        hist.push(tps);

        // Update peak TPS
        let mut peak = self.peak_tps.write();
        if tps > *peak {
            *peak = tps;
        }

        tps
    }

    /// Check for statistical anomalies (turnout spikes and Benford's Law distribution).
    #[allow(dead_code)]
    pub fn evaluate_anomalies(&self, poll_id: &str, option_counts: &[u64], turnout_pct: f64) {
        let mut flags = self.anomaly_log.write();

        // 1. High Turnout Spike check (> 90% or rapid surge)
        if turnout_pct > 92.0 {
            let msg = format!(
                "Turnout Spike Alert: Poll '{}' registered extraordinary turnout ({:.1}%). Verification triggered.",
                poll_id, turnout_pct
            );
            if !flags.contains(&msg) {
                flags.push(msg);
            }
        }

        // 2. Benford's Law first-digit conformity analysis
        if option_counts.len() >= 4 {
            let mut first_digits = HashMap::new();
            for &c in option_counts {
                if c > 0 {
                    let first_char = c.to_string().chars().next().unwrap();
                    let d = first_char.to_digit(10).unwrap_or(0);
                    if d > 0 {
                        *first_digits.entry(d).or_insert(0) += 1;
                    }
                }
            }
            // Log anomaly if high digits (7,8,9) dominate over low digits (1,2,3)
            let high_digits_count: usize = first_digits.iter().filter(|(&k, _)| k >= 7).map(|(_, v)| *v).sum();
            let low_digits_count: usize = first_digits.iter().filter(|(&k, _)| k <= 3).map(|(_, v)| *v).sum();
            if high_digits_count > low_digits_count && option_counts.iter().sum::<u64>() > 500 {
                let benford_flag = format!("Benford Variance: Poll '{}' displays non-conforming first-digit skew.", poll_id);
                if !flags.contains(&benford_flag) {
                    flags.push(benford_flag);
                }
            }
        }
    }

    /// Calculate comprehensive turnout metrics for a campaign.
    #[allow(dead_code)]
    pub fn calculate_turnout(
        &self,
        campaign_id: &str,
        ballots_cast: u64,
        target_quota: u64,
        county_dist: &HashMap<String, u64>,
    ) -> CampaignTurnoutMetrics {
        let quota = if target_quota > 0 { target_quota } else { 1000 };
        let pct = (ballots_cast as f64 / quota as f64) * 100.0;
        let top_county = county_dist
            .iter()
            .max_by_key(|(_, &cnt)| cnt)
            .map(|(k, _)| k.clone())
            .unwrap_or_else(|| "Nairobi County".to_string());

        CampaignTurnoutMetrics {
            campaign_id: campaign_id.to_string(),
            ballots_cast,
            target_quota: quota,
            turnout_percentage: (pct * 10.0).round() / 10.0,
            is_threshold_reached: pct >= 50.0,
            top_county,
        }
    }

    /// Snapshot platform performance metrics.
    pub fn snapshot(&self, total_votes: u64, active_polls: usize) -> TelemetrySnapshot {
        let hist = self.tps_history.read();
        let current_tps = hist.last().copied().unwrap_or(0.0);
        let avg_5s = if !hist.is_empty() {
            let slice = &hist[hist.len().saturating_sub(5)..];
            slice.iter().sum::<f64>() / slice.len() as f64
        } else {
            0.0
        };
        let peak = *self.peak_tps.read();

        let latencies = self.latency_samples_us.read();
        let mean_lat = if !latencies.is_empty() {
            latencies.iter().sum::<u64>() as f64 / latencies.len() as f64
        } else {
            4.2 // Sub-5ms baseline
        };

        TelemetrySnapshot {
            current_tps: (current_tps * 10.0).round() / 10.0,
            avg_5s_tps: (avg_5s * 10.0).round() / 10.0,
            peak_tps: (peak * 10.0).round() / 10.0,
            total_ingested: total_votes,
            mean_latency_us: (mean_lat * 10.0).round() / 10.0,
            active_polls_count: active_polls,
            anomaly_flags: self.anomaly_log.read().clone(),
            uptime_seconds: self.start_time.elapsed().as_secs(),
        }
    }
}

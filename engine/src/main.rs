mod analytics;
mod vote_processor;
mod ws_handler;

use std::net::SocketAddr;
use std::sync::Arc;
use std::time::Duration;

use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::TcpListener;

use crate::analytics::AnalyticsEngine;
use crate::vote_processor::{VotePayload, VoteProcessor};
use crate::ws_handler::WsServer;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("============================================================");
    println!("  ICAPSQ / GETITRIGHT SOVEREIGN RESEARCH PLATFORM           ");
    println!("  Rust Real-Time High-Throughput Ingestion Engine v0.1.0    ");
    println!("============================================================");

    let port: u16 = std::env::var("PORT")
        .ok()
        .and_then(|p| p.parse().ok())
        .unwrap_or(8088);

    let addr: SocketAddr = format!("0.0.0.0:{}", port).parse()?;
    let listener = TcpListener::bind(&addr).await?;
    println!("[ENGINE] Listening on tcp://{}", addr);

    // Initialize core engine subsystems
    let processor = Arc::new(VoteProcessor::new(100_000));
    let analytics = Arc::new(AnalyticsEngine::new());
    let ws_server = Arc::new(WsServer::new(10_000));

    // Seed default campaigns for immediate readiness
    seed_initial_campaigns(&processor);

    // Background Telemetry Worker (1 Hz frequency)
    let p_clone = processor.clone();
    let a_clone = analytics.clone();
    let ws_clone = ws_server.clone();
    tokio::spawn(async move {
        let mut interval = tokio::time::interval(Duration::from_secs(1));
        loop {
            interval.tick().await;
            let total = p_clone.total_ingested();
            let active_polls = p_clone.get_all_tallies().len();
            a_clone.tick(total);
            let snapshot = a_clone.snapshot(total, active_polls);
            ws_clone.broadcast_telemetry(snapshot);
        }
    });

    println!("[ENGINE] Ready. Awaiting high-concurrency client streams...");

    // Accept loop: Handle both WebSocket clients and HTTP health/metrics probes
    while let Ok((mut stream, client_addr)) = listener.accept().await {
        let processor = processor.clone();
        let analytics = analytics.clone();
        let ws_server = ws_server.clone();

        tokio::spawn(async move {
            // Peek at initial bytes to distinguish HTTP probe vs WebSocket upgrade
            let mut peek_buf = [0u8; 1024];
            let n = match stream.peek(&mut peek_buf).await {
                Ok(n) if n > 0 => n,
                _ => return,
            };

            let req_str = String::from_utf8_lossy(&peek_buf[..n]);

            // Check if it's a simple HTTP GET request
            if req_str.starts_with("GET /health") {
                let mut buf = vec![0u8; n];
                let _ = stream.read_exact(&mut buf).await;
                let body = r#"{"status":"healthy","engine":"rust-tokio","version":"0.1.0"}"#;
                let resp = format!(
                    "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}",
                    body.len(),
                    body
                );
                let _ = stream.write_all(resp.as_bytes()).await;
                return;
            }

            if req_str.starts_with("GET /metrics") {
                let mut buf = vec![0u8; n];
                let _ = stream.read_exact(&mut buf).await;
                let total = processor.total_ingested();
                let active = processor.get_all_tallies().len();
                let snap = analytics.snapshot(total, active);
                let body = serde_json::to_string_pretty(&snap).unwrap_or_else(|_| "{}".to_string());
                let resp = format!(
                    "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}",
                    body.len(),
                    body
                );
                let _ = stream.write_all(resp.as_bytes()).await;
                return;
            }

            if req_str.starts_with("GET /tally") {
                let mut buf = vec![0u8; n];
                let _ = stream.read_exact(&mut buf).await;
                let tallies = processor.get_all_tallies();
                let body = serde_json::to_string_pretty(&tallies).unwrap_or_else(|_| "[]".to_string());
                let resp = format!(
                    "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}",
                    body.len(),
                    body
                );
                let _ = stream.write_all(resp.as_bytes()).await;
                return;
            }

            if req_str.starts_with("POST /vote") || req_str.starts_with("POST /ingest") {
                let mut buf = vec![0u8; n];
                let _ = stream.read_exact(&mut buf).await;
                let body_str = req_str.split("\r\n\r\n").nth(1).unwrap_or("");
                if let Ok(vote_payload) = serde_json::from_str::<VotePayload>(body_str) {
                    let poll_id = vote_payload.poll_id.clone();
                    let processed = processor.ingest_vote(vote_payload);
                    if let Some(tally) = processor.get_tally(&poll_id) {
                        ws_server.broadcast_vote(poll_id, processed.clone(), tally);
                    }
                    let resp_body = serde_json::to_string(&processed).unwrap_or_else(|_| "{}".to_string());
                    let resp = format!(
                        "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}",
                        resp_body.len(),
                        resp_body
                    );
                    let _ = stream.write_all(resp.as_bytes()).await;
                    return;
                } else {
                    let err_body = r#"{"error":"invalid_vote_payload"}"#;
                    let resp = format!(
                        "HTTP/1.1 400 Bad Request\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}",
                        err_body.len(),
                        err_body
                    );
                    let _ = stream.write_all(resp.as_bytes()).await;
                    return;
                }
            }

            // Upgrade to WebSocket
            ws_server.handle_connection(stream, client_addr, processor).await;
        });
    }

    Ok(())
}

fn seed_initial_campaigns(processor: &Arc<VoteProcessor>) {
    let seed_votes = vec![
        ("PL-NAIROBI-EXP", "Commuter Rail Modernization", "Kitui County"),
        ("PL-NAIROBI-EXP", "Commuter Rail Modernization", "Kitui County"),
        ("PL-NAIROBI-EXP", "Bus Rapid Transit (BRT)", "Nairobi County"),
        ("PL-NAIROBI-EXP", "Commuter Rail Modernization", "Nairobi County"),
        ("PL-HEALTH-SHIF", "Fundamental Tariff Overhaul", "Nairobi County"),
        ("PL-HEALTH-SHIF", "Fundamental Tariff Overhaul", "Machakos County"),
    ];

    for (p_id, opt, cty) in seed_votes {
        processor.ingest_vote(VotePayload {
            poll_id: p_id.to_string(),
            option_id: "OPT-1".to_string(),
            option_label: opt.to_string(),
            voter_id: "VTR-SEED".to_string(),
            voter_name: "Citizen Voter".to_string(),
            county: cty.to_string(),
            device_name: "Mobile App".to_string(),
            device_os: "Android 14".to_string(),
            timestamp: None,
        });
    }

    println!(
        "[ENGINE] Preloaded initial sovereign consensus tracks ({} seed ballots).",
        processor.total_ingested()
    );
}

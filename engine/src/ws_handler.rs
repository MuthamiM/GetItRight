use std::collections::HashSet;
use std::net::SocketAddr;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Arc;

use futures_util::{SinkExt, StreamExt};
use parking_lot::RwLock;
use serde::{Deserialize, Serialize};
use tokio::net::TcpStream;
use tokio::sync::broadcast;
use tokio_tungstenite::tungstenite::Message;

use crate::analytics::TelemetrySnapshot;
use crate::vote_processor::{PollTallySnapshot, ProcessedVote, VotePayload, VoteProcessor};

/// Real-time message broadcasted over WebSockets to mobile and web clients.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum WsBroadcastMessage {
    #[serde(rename = "vote_update")]
    VoteUpdate {
        poll_id: String,
        vote: ProcessedVote,
        tally: PollTallySnapshot,
    },
    #[serde(rename = "telemetry")]
    Telemetry {
        snapshot: TelemetrySnapshot,
    },
    #[serde(rename = "pong")]
    Pong {
        timestamp_ms: u64,
    },
}

/// Incoming client commands received over WebSocket.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "action")]
pub enum ClientCommand {
    #[serde(rename = "subscribe")]
    Subscribe { poll_id: String },
    #[serde(rename = "unsubscribe")]
    Unsubscribe { poll_id: String },
    #[serde(rename = "ping")]
    Ping,
    #[serde(rename = "cast_vote")]
    CastVote { payload: VotePayload },
}

/// WebSocket connection coordinator managing active subscribers and broadcasts.
pub struct WsServer {
    broadcast_tx: broadcast::Sender<WsBroadcastMessage>,
    active_connections: Arc<AtomicUsize>,
}

impl WsServer {
    pub fn new(capacity: usize) -> Self {
        let (tx, _) = broadcast::channel(capacity);
        Self {
            broadcast_tx: tx,
            active_connections: Arc::new(AtomicUsize::new(0)),
        }
    }

    /// Broadcast a vote update to all listening clients with sub-5ms latency.
    pub fn broadcast_vote(&self, poll_id: String, vote: ProcessedVote, tally: PollTallySnapshot) {
        let msg = WsBroadcastMessage::VoteUpdate { poll_id, vote, tally };
        let _ = self.broadcast_tx.send(msg);
    }

    /// Broadcast platform telemetry metrics to connected dashboards.
    pub fn broadcast_telemetry(&self, snapshot: TelemetrySnapshot) {
        let msg = WsBroadcastMessage::Telemetry { snapshot };
        let _ = self.broadcast_tx.send(msg);
    }

    /// Handle a new incoming TCP connection upgraded to WebSocket.
    pub async fn handle_connection(
        &self,
        stream: TcpStream,
        addr: SocketAddr,
        processor: Arc<VoteProcessor>,
    ) {
        let ws_stream = match tokio_tungstenite::accept_async(stream).await {
            Ok(ws) => ws,
            Err(e) => {
                eprintln!("[WS] Handshake failed for {}: {}", addr, e);
                return;
            }
        };

        self.active_connections.fetch_add(1, Ordering::Relaxed);
        let mut rx = self.broadcast_tx.subscribe();
        let (mut ws_writer, mut ws_reader) = ws_stream.split();

        let subscribed_polls: Arc<RwLock<HashSet<String>>> = Arc::new(RwLock::new(HashSet::new()));
        let subs_for_writer = subscribed_polls.clone();

        // Task: Outgoing broadcasts -> client
        let mut send_task = tokio::spawn(async move {
            while let Ok(msg) = rx.recv().await {
                // Check poll subscription filter if applicable
                let should_send = match &msg {
                    WsBroadcastMessage::VoteUpdate { poll_id, .. } => {
                        let subs = subs_for_writer.read();
                        subs.is_empty() || subs.contains(poll_id)
                    }
                    WsBroadcastMessage::Telemetry { .. } | WsBroadcastMessage::Pong { .. } => true,
                };

                if should_send {
                    if let Ok(json_str) = serde_json::to_string(&msg) {
                        if ws_writer.send(Message::Text(json_str)).await.is_err() {
                            break;
                        }
                    }
                }
            }
        });

        // Task: Incoming client messages -> server
        let active_conns = self.active_connections.clone();
        let tx = self.broadcast_tx.clone();
        let mut recv_task = tokio::spawn(async move {
            while let Some(Ok(raw_msg)) = ws_reader.next().await {
                if let Message::Text(text) = raw_msg {
                    if let Ok(cmd) = serde_json::from_str::<ClientCommand>(&text) {
                        match cmd {
                            ClientCommand::Subscribe { poll_id } => {
                                subscribed_polls.write().insert(poll_id);
                            }
                            ClientCommand::Unsubscribe { poll_id } => {
                                subscribed_polls.write().remove(&poll_id);
                            }
                            ClientCommand::Ping => {
                                let now_ms = std::time::SystemTime::now()
                                    .duration_since(std::time::UNIX_EPOCH)
                                    .map(|d| d.as_millis() as u64)
                                    .unwrap_or(0);
                                let _ = tx.send(WsBroadcastMessage::Pong { timestamp_ms: now_ms });
                            }
                            ClientCommand::CastVote { payload } => {
                                let poll_id = payload.poll_id.clone();
                                let processed = processor.ingest_vote(payload);
                                if let Some(tally) = processor.get_tally(&poll_id) {
                                    let _ = tx.send(WsBroadcastMessage::VoteUpdate {
                                        poll_id,
                                        vote: processed,
                                        tally,
                                    });
                                }
                            }
                        }
                    }
                } else if raw_msg.is_close() {
                    break;
                }
            }
            active_conns.fetch_sub(1, Ordering::Relaxed);
        });

        tokio::select! {
            _ = (&mut send_task) => recv_task.abort(),
            _ = (&mut recv_task) => send_task.abort(),
        }
    }

    #[allow(dead_code)]
    pub fn active_connections(&self) -> usize {
        self.active_connections.load(Ordering::Relaxed)
    }
}

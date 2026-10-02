/* =============================================================
   POLLTRACK — Client-Side Cryptographic Verifier
   Browser-only SHA-256 hashing via Web Crypto API.
   Zero data leaves the client device.
   Zero emojis.
   ============================================================= */

const CryptoVerifier = {
  // Convert ArrayBuffer to hex string
  bufferToHex(buffer) {
    const byteArray = new Uint8Array(buffer);
    const hexParts = [];
    for (let i = 0; i < byteArray.length; i++) {
      const hex = byteArray[i].toString(16).padStart(2, '0');
      hexParts.push(hex);
    }
    return '0x' + hexParts.join('');
  },

  // Compute SHA-256 of file in browser
  async hashFile(file) {
    const arrayBuffer = await file.arrayBuffer();
    const digestBuffer = await crypto.subtle.digest('SHA-256', arrayBuffer);
    return this.bufferToHex(digestBuffer);
  },

  // Compute SHA-256 of string or hex
  async hashText(text) {
    const enc = new TextEncoder();
    const data = enc.encode(text);
    const digestBuffer = await crypto.subtle.digest('SHA-256', data);
    return this.bufferToHex(digestBuffer);
  },

  // Recompute Merkle Root from leaf hash and inclusion proof
  async recomputeRoot(leafHash, proof) {
    let currentHash = leafHash;
    for (const step of proof) {
      let combined;
      if (step.position === 'left') {
        combined = step.hash + currentHash.replace('0x', '');
      } else {
        combined = currentHash + step.hash.replace('0x', '');
      }
      currentHash = await this.hashText(combined);
    }
    return currentHash;
  },

  // Look up hash in ledger mock store
  lookupHash(targetHash) {
    const cleanTarget = targetHash.trim().toLowerCase();
    
    // Check known station photos/entry hashes
    const foundEntry = MockData.ledgerEntries.find(entry => 
      entry.imageSha256.toLowerCase() === cleanTarget ||
      entry.entryHash.toLowerCase() === cleanTarget ||
      entry.imageSha256.toLowerCase().includes(cleanTarget.replace('0x', '')) ||
      entry.entryHash.toLowerCase().includes(cleanTarget.replace('0x', ''))
    );

    if (foundEntry) {
      const checkpoint = MockData.checkpoints.find(cp => cp.number === foundEntry.checkpoint) || MockData.checkpoints[0];
      return {
        status: "MATCH",
        entrySeq: foundEntry.seq,
        stationId: foundEntry.stationId,
        stationName: MockData.stations.find(s => s.id === foundEntry.stationId)?.name || foundEntry.stationId,
        checkpointNumber: checkpoint.number,
        publishedRoot: checkpoint.root,
        capturedAt: foundEntry.capturedAt,
        deviceSigStatus: foundEntry.deviceSigStatus,
        inclusionProof: foundEntry.inclusionProof || [
          { level: 1, position: "right", hash: "0x4b7f0129ad8412bc4890cf319a2e8f2a93c7e1b4f09d8213ba4e67120cda59e4" },
          { level: 2, position: "left", hash: "0x12bc4890cf319a2e8f2a93c7e1b4f09d8213ba4e67120cda59e44b7f0129ad84" }
        ],
        anchors: checkpoint.anchors
      };
    }

    // Check for mismatch simulation
    if (cleanTarget.startsWith('0xbad') || cleanTarget.includes('mismatch')) {
      return {
        status: "MISMATCH",
        entrySeq: 14207,
        stationId: "ST-108",
        expectedHash: "0x4c91e87f2a1b9c3e5d710842ba67120cda59e41b7f0129ad8412bc4890cf8821",
        receivedHash: cleanTarget,
        diffReason: "Image perceptual hash altered by 14% (tamper alert) or uncommitted payload"
      };
    }

    return {
      status: "NOT_FOUND",
      hash: targetHash
    };
  }
};

if (typeof module !== 'undefined' && module.exports) {
  module.exports = CryptoVerifier;
}

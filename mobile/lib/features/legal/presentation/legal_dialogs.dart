import 'package:flutter/material.dart';

class LegalDialogs {
  static void showTermsOfService(BuildContext context) {
    showDialog(
      context: context,
      barrierDismissible: true,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF383838),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: const Color(0xFF4A4A4A),
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Icon(Icons.gavel_rounded, color: Color(0xFFE5E5E5), size: 22),
            ),
            const SizedBox(width: 12),
            const Expanded(
              child: Text(
                'Terms of Service',
                style: TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 18,
                ),
              ),
            ),
          ],
        ),
        content: SizedBox(
          width: double.maxFinite,
          child: SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Last Updated: October 2026',
                  style: TextStyle(color: Color(0xFFB8B8B8), fontSize: 11, fontStyle: FontStyle.italic),
                ),
                const SizedBox(height: 12),
                _buildSection(
                  '1. Acceptance of Terms',
                  'By accessing or using the GetitRight mobile application and web platform, you agree to be bound by these Terms of Service. If you do not agree to these terms, do not access or use the services.',
                ),
                _buildSection(
                  '2. Civic Polling & Democratic Participation',
                  'GetitRight provides public and institutional polling services. Users agree to participate in good faith. Automated vote casting, sybil ballot creation, and bot activities are strictly prohibited and actively screened via biometric and device attestation.',
                ),
                _buildSection(
                  '3. Vote Immutability & Permanence',
                  'To safeguard the cryptographic integrity of electoral and civic referendums, once a vote is cast and anchored with a Merkle cryptographic receipt, it cannot be modified or reversed. One ballot per authenticated device or phone account is enforced.',
                ),
                _buildSection(
                  '4. Account & Device Security',
                  'Your phone number and hardware-backed device keys authenticate your participation. You are responsible for maintaining control of your device credentials. We do not sell your account credentials to third parties.',
                ),
                _buildSection(
                  '5. Organizational Surveys',
                  'Organizations publishing surveys on GetitRight must comply with ethical research guidelines and applicable election laws. GetitRight reserves the right to suspend surveys that incite violence, defamation, or fraudulent behavior.',
                ),
                _buildSection(
                  '6. Limitation of Liability',
                  'The service is provided "as is" with cryptographic auditability. In no event shall GetitRight be liable for indirect, incidental, or consequential damages resulting from public polling outcomes.',
                ),
              ],
            ),
          ),
        ),
        actions: [
          ElevatedButton(
            onPressed: () => Navigator.of(ctx).pop(),
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFFE5E5E5),
              foregroundColor: const Color(0xFF2A2A2A),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 10),
            ),
            child: const Text('I Understand', style: TextStyle(fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }

  static void showPrivacyPolicy(BuildContext context) {
    showDialog(
      context: context,
      barrierDismissible: true,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF383838),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: const Color(0xFF4A4A4A),
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Icon(Icons.shield_outlined, color: Color(0xFFE5E5E5), size: 22),
            ),
            const SizedBox(width: 12),
            const Expanded(
              child: Text(
                'Privacy Policy',
                style: TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 18,
                ),
              ),
            ),
          ],
        ),
        content: SizedBox(
          width: double.maxFinite,
          child: SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Compliant with Kenya Data Protection Act 2019 & Global Standards',
                  style: TextStyle(color: Color(0xFFB8B8B8), fontSize: 11, fontStyle: FontStyle.italic),
                ),
                const SizedBox(height: 12),
                _buildSection(
                  '1. What We Collect',
                  '• Account Identity: Phone number and email linked to your account for identity verification and anti-fraud authentication.\n• Ballot Submissions: Pseudonymized votes signed with hardware device attestation.\n• Diagnostic Data: App version, device telemetry, and optional offline sync queues.',
                ),
                _buildSection(
                  '2. Secret Ballot & Zero Knowledge',
                  'Your individual ballot choice is decoupled from your phone number and identity. Public results only expose aggregate counts verified by Merkle tree roots, ensuring no observer can deduce who voted for which option.',
                ),
                _buildSection(
                  '3. Account Phone Linking',
                  'Your phone number is linked once to your user profile to prevent double-voting across polls. We never spam your phone number or sell your contacts to third-party ad networks.',
                ),
                _buildSection(
                  '4. Cryptographic Receipts',
                  'Each vote generates a SHA-256 cryptographic receipt that allows you to mathematically verify your ballot was included in the final tally without revealing your vote choice.',
                ),
                _buildSection(
                  '5. Data Retention & User Rights',
                  'You may request deletion of your account profile at any time. Cryptographically committed aggregate ledger roots remain immutable to protect historical election integrity.',
                ),
                _buildSection(
                  '6. Contact Privacy Officer',
                  'For inquiries regarding your personal data or privacy rights under the Data Protection Act, contact privacy@getitright.io.',
                ),
              ],
            ),
          ),
        ),
        actions: [
          ElevatedButton(
            onPressed: () => Navigator.of(ctx).pop(),
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFFE5E5E5),
              foregroundColor: const Color(0xFF2A2A2A),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 10),
            ),
            child: const Text('Close', style: TextStyle(fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }

  static Widget _buildSection(String title, String content) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: const TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.bold,
              fontSize: 13.5,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            content,
            style: const TextStyle(
              color: Color(0xFFCCCCCC),
              fontSize: 12.5,
              height: 1.45,
            ),
          ),
        ],
      ),
    );
  }
}

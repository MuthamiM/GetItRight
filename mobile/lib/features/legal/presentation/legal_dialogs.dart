import 'package:flutter/material.dart';

class LegalDialogs {
  static Future<void> showTermsOfService(BuildContext context) {
    return Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => const _LegalDocumentPage(
          title: 'Terms of Service',
          icon: Icons.gavel_rounded,
          subtitle: 'Last updated October 2026',
          sections: [
            _LegalSection(
              '1. Acceptance of Terms',
              'By accessing or using the IcapsQ mobile application and web platform, you agree to be bound by these Terms of Service. If you do not agree to these terms, do not access or use the services.',
            ),
            _LegalSection(
              '2. Civic Polling & Democratic Participation',
              'IcapsQ provides public and institutional polling and feedback services. Users agree to participate in good faith. Automated vote casting, sybil ballot creation, and bot activities are strictly prohibited and actively screened via biometric and device attestation.',
            ),
            _LegalSection(
              '3. Vote Immutability & Permanence',
              'To safeguard the cryptographic integrity of electoral and civic referendums, once a vote is cast and anchored with a Merkle cryptographic receipt, it cannot be modified or reversed. One ballot per authenticated device or phone account is enforced.',
            ),
            _LegalSection(
              '4. Account & Device Security',
              'Your phone number and hardware-backed device keys authenticate your participation. You are responsible for maintaining control of your device credentials. We do not sell your account credentials to third parties.',
            ),
            _LegalSection(
              '5. Organizational Surveys',
              'Organizations publishing surveys on IcapsQ must comply with ethical research guidelines and applicable election laws. IcapsQ reserves the right to suspend surveys that incite violence, defamation, or fraudulent behavior.',
            ),
            _LegalSection(
              '6. Limitation of Liability',
              'The service is provided "as is" with cryptographic auditability. In no event shall IcapsQ be liable for indirect, incidental, or consequential damages resulting from public polling outcomes.',
            ),
          ],
        ),
      ),
    );
  }

  static Future<void> showPrivacyPolicy(BuildContext context) {
    return Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => const _LegalDocumentPage(
          title: 'Privacy Policy',
          icon: Icons.shield_outlined,
          subtitle:
              'Compliant with Kenya Data Protection Act 2019 & Global Standards',
          sections: [
            _LegalSection(
              '1. Information We Collect',
              '• Account Identity: Phone number and email linked to your account for identity verification and anti-fraud authentication.\n• Ballot Submissions: Pseudonymized votes signed with hardware device attestation.\n• Diagnostic Data: App version, device telemetry, and optional offline sync queues.',
            ),
            _LegalSection(
              '2. Secret Ballot & Zero Knowledge',
              'Your individual ballot choice is decoupled from your phone number and identity. Public results only expose aggregate counts verified by Merkle tree roots, ensuring no observer can deduce who voted for which option.',
            ),
            _LegalSection(
              '3. Account Phone Linking',
              'Your phone number is linked once to your user profile to prevent double-voting across polls. We never spam your phone number or sell your contacts to third-party ad networks.',
            ),
            _LegalSection(
              '4. Cryptographic Receipts',
              'Each vote generates a SHA-256 cryptographic receipt that allows you to mathematically verify your ballot was included in the final tally without revealing your vote choice.',
            ),
            _LegalSection(
              '5. Data Retention & User Rights',
              'You may request deletion of your account profile at any time. Cryptographically committed aggregate ledger roots remain immutable to protect historical election integrity.',
            ),
            _LegalSection(
              '6. Contact Privacy Officer',
              'For inquiries regarding your personal data or privacy rights under the Data Protection Act, contact privacy@icapsq.com.',
            ),
          ],
        ),
      ),
    );
  }
}

class _LegalSection {
  final String title;
  final String content;

  const _LegalSection(this.title, this.content);
}

class _LegalDocumentPage extends StatelessWidget {
  final String title;
  final IconData icon;
  final String subtitle;
  final List<_LegalSection> sections;

  const _LegalDocumentPage({
    required this.title,
    required this.icon,
    required this.subtitle,
    required this.sections,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF303030),
      appBar: AppBar(
        backgroundColor: const Color(0xFF303030),
        foregroundColor: Colors.white,
        elevation: 0,
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.w700)),
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(18, 10, 18, 28),
          children: [
            Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                color: const Color(0xFF3B3B3B),
                borderRadius: BorderRadius.circular(18),
                border: Border.all(color: const Color(0xFF555555)),
              ),
              child: Row(
                children: [
                  Container(
                    width: 48,
                    height: 48,
                    decoration: const BoxDecoration(
                      color: Color(0xFF505050),
                      shape: BoxShape.circle,
                    ),
                    child: Icon(icon, color: const Color(0xFFE5E5E5)),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Text(
                      subtitle,
                      style: const TextStyle(
                        color: Color(0xFFB8B8B8),
                        fontSize: 13,
                        height: 1.4,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 18),
            ...sections.map(
              (section) => Container(
                margin: const EdgeInsets.only(bottom: 12),
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: const Color(0xFF3B3B3B),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: const Color(0xFF4C4C4C)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      section.title,
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.w700,
                        fontSize: 14,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      section.content,
                      style: const TextStyle(
                        color: Color(0xFFCCCCCC),
                        fontSize: 13,
                        height: 1.5,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

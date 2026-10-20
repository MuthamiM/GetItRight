import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../core/network/api_client.dart';
import '../../legal/presentation/legal_dialogs.dart';

class ProfileSettingsScreen extends StatefulWidget {
  final VoidCallback onSettingsUpdated;

  const ProfileSettingsScreen({super.key, required this.onSettingsUpdated});

  @override
  State<ProfileSettingsScreen> createState() => _ProfileSettingsScreenState();
}

class _ProfileSettingsScreenState extends State<ProfileSettingsScreen> {
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _phoneController = TextEditingController();
  final _orgController = TextEditingController();

  bool _notificationsEnabled = true;

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _nameController.text = prefs.getString('gir_user_name') ?? 'User';
      _emailController.text =
          prefs.getString('gir_user_email') ?? 'user@getitright.io';
      _phoneController.text = prefs.getString('gir_user_phone') ?? '';
      _orgController.text = prefs.getString('gir_user_org') ?? 'Independent';
      _notificationsEnabled =
          prefs.getBool('gir_notifications_enabled') ?? true;
    });
  }

  Future<void> _setNotifications(bool value) async {
    setState(() => _notificationsEnabled = value);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('gir_notifications_enabled', value);
    widget.onSettingsUpdated();
  }

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _phoneController.dispose();
    _orgController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      color: const Color(0xFF303030),
      child: SafeArea(
        top: false,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 28),
          children: [
            Row(children: [
              Container(
                width: 58,
                height: 58,
                decoration: const BoxDecoration(
                  color: Color(0xFF505050),
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.person_outline_rounded,
                    color: Colors.white, size: 32),
              ),
              const SizedBox(width: 14),
              Expanded(
                  child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                      _nameController.text.isEmpty
                          ? 'Your profile'
                          : _nameController.text,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                          color: Colors.white,
                          fontSize: 19,
                          fontWeight: FontWeight.w700)),
                  const SizedBox(height: 3),
                  Text(_emailController.text,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                          color: Color(0xFFB8B8B8), fontSize: 13)),
                ],
              )),
              IconButton(
                tooltip: 'Edit display name',
                onPressed: () => _editAccountField(
                    label: 'Display Name',
                    controller: _nameController,
                    preferenceKey: 'gir_user_name',
                    hint: 'Name'),
                icon: const Icon(Icons.edit_outlined, color: Color(0xFFE5E5E5)),
              ),
            ]),
            const SizedBox(height: 24),
            _buildSectionHeader('ACCOUNT'),
            const SizedBox(height: 8),
            _buildAccountInformationCard(),
            const SizedBox(height: 22),
            _buildSectionHeader('PREFERENCES'),
            const SizedBox(height: 8),
            _settingsPanel([
              _settingsActionRow(
                icon: Icons.notifications_none_rounded,
                title: 'Push notifications',
                subtitle: 'Receive live updates and poll results',
                trailing: Switch(
                  value: _notificationsEnabled,
                  activeColor: const Color(0xFFE5E5E5),
                  activeTrackColor: const Color(0xFF777777),
                  inactiveTrackColor: const Color(0xFF404040),
                  onChanged: _setNotifications,
                ),
              ),
            ]),
            const SizedBox(height: 22),
            _buildSectionHeader('APP'),
            const SizedBox(height: 8),
            _settingsPanel([
              _settingsActionRow(
                icon: Icons.phone_android_rounded,
                title: 'IcapsQ Official App',
                subtitle: 'Version 2.1.18 · Build 23',
                trailing: IconButton(
                  tooltip: 'Check for updates',
                  onPressed: _checkUpdateManually,
                  icon: const Icon(Icons.refresh_rounded,
                      color: Color(0xFFE5E5E5)),
                ),
              ),
              const Divider(height: 1, color: Color(0xFF606060), indent: 54),
              _settingsActionRow(
                icon: Icons.info_outline_rounded,
                title: 'Terms of Service',
                trailing: const Icon(Icons.open_in_new_rounded,
                    color: Color(0xFFB8B8B8), size: 18),
                onTap: () => LegalDialogs.showTermsOfService(context),
              ),
              const Divider(height: 1, color: Color(0xFF606060), indent: 54),
              _settingsActionRow(
                icon: Icons.privacy_tip_outlined,
                title: 'Privacy Policy',
                trailing: const Icon(Icons.open_in_new_rounded,
                    color: Color(0xFFB8B8B8), size: 18),
                onTap: () => LegalDialogs.showPrivacyPolicy(context),
              ),
            ]),
            const SizedBox(height: 18),
            const Text('© 2026 IcapsQ. All rights reserved.',
                textAlign: TextAlign.center,
                style: TextStyle(color: Color(0xFF929292), fontSize: 11)),
          ],
        ),
      ),
    );
  }

  Widget _settingsPanel(List<Widget> children) => Material(
        color: const Color(0xFF3B3B3B),
        borderRadius: BorderRadius.circular(18),
        clipBehavior: Clip.antiAlias,
        child: Column(children: children),
      );

  Widget _settingsActionRow(
          {required IconData icon,
          required String title,
          String? subtitle,
          required Widget trailing,
          VoidCallback? onTap}) =>
      ListTile(
        onTap: onTap,
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 3),
        leading: Icon(icon, color: const Color(0xFFD0D0D0), size: 22),
        title: Text(title,
            style: const TextStyle(
                color: Colors.white,
                fontSize: 14,
                fontWeight: FontWeight.w600)),
        subtitle: subtitle == null
            ? null
            : Text(subtitle,
                style: const TextStyle(color: Color(0xFFB8B8B8), fontSize: 12)),
        trailing: trailing,
      );

  Future<void> _checkUpdateManually() async {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text(
          'Checking for latest updates...',
          style:
              TextStyle(color: Color(0xFF2A2A2A), fontWeight: FontWeight.bold),
        ),
        backgroundColor: Color(0xFFE5E5E5),
        duration: Duration(seconds: 1),
      ),
    );

    try {
      final updateInfo = await ApiClient().checkAppUpdate();
      if (!mounted) return;

      if (updateInfo['update_available'] == true) {
        _showUpdateDialog(
          version: updateInfo['latest_version']?.toString() ?? '2.0.0',
          releaseNotes: updateInfo['release_notes']?.toString(),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text(
              'You are using the latest version of IcapsQ (v2.1.18)',
              style: TextStyle(
                  color: Color(0xFF2A2A2A), fontWeight: FontWeight.bold),
            ),
            backgroundColor: Color(0xFFE5E5E5),
            duration: Duration(seconds: 2),
          ),
        );
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content:
                Text('Could not reach update server. Please try again later.'),
            backgroundColor: Color(0xFF424242),
          ),
        );
      }
    }
  }

  void _showUpdateDialog({required String version, String? releaseNotes}) {
    showDialog(
      context: context,
      barrierDismissible: true,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF424242),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: const Color(0xFF555555),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Icon(Icons.system_update_rounded,
                  color: Color(0xFFE5E5E5), size: 24),
            ),
            const SizedBox(width: 12),
            const Expanded(
              child: Text(
                'Update Available',
                style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 18),
              ),
            ),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
              decoration: BoxDecoration(
                color: const Color(0xFF303030),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: const Color(0xFF606060)),
              ),
              child: Text(
                'Version $version is now available (Current: v2.1.18)',
                style: const TextStyle(
                    color: Color(0xFFE5E5E5),
                    fontSize: 12,
                    fontWeight: FontWeight.w600),
              ),
            ),
            const SizedBox(height: 14),
            const Text(
              'What\'s New in this release:',
              style: TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w600,
                  fontSize: 13),
            ),
            const SizedBox(height: 6),
            Text(
              releaseNotes ??
                  '• Instant scroll-to-top navigation\n'
                      '• Real-time poll vote tallying & animated charts\n'
                      '• Cryptographic survey receipt verification\n'
                      '• Offline vote persistence & auto-sync\n'
                      '• Stability & performance improvements',
              style: const TextStyle(
                  color: Color(0xFFD0D0D0), fontSize: 12.5, height: 1.45),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('Later',
                style: TextStyle(
                    color: Color(0xFFB8B8B8), fontWeight: FontWeight.w600)),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.of(ctx).pop();
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text(
                    'Downloading IcapsQ v$version...',
                    style: const TextStyle(
                        color: Color(0xFF2A2A2A), fontWeight: FontWeight.bold),
                  ),
                  backgroundColor: const Color(0xFFE5E5E5),
                  duration: const Duration(seconds: 3),
                ),
              );
              try {
                final uri = Uri.parse(
                    'https://icapsq.mftechnologies.org/app-release.apk');
                if (await canLaunchUrl(uri)) {
                  await launchUrl(uri, mode: LaunchMode.externalApplication);
                }
              } catch (_) {}
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFFE5E5E5),
              foregroundColor: const Color(0xFF2A2A2A),
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16)),
            ),
            child: const Text('Update Now',
                style: TextStyle(fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionHeader(String title) {
    return Text(
      title,
      style: const TextStyle(
          color: Color(0xFFB8B8B8),
          fontSize: 12,
          fontWeight: FontWeight.bold,
          letterSpacing: 1.0),
    );
  }

  Widget _buildAccountInformationCard() {
    return Material(
      color: const Color(0xFF505050),
      borderRadius: BorderRadius.circular(16),
      clipBehavior: Clip.antiAlias,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(14, 14, 14, 4),
            child: _buildSectionHeader('ACCOUNT INFORMATION'),
          ),
          _buildAccountRow(
            label: 'Display Name',
            controller: _nameController,
            preferenceKey: 'gir_user_name',
            hint: 'Name',
          ),
          _buildAccountDivider(),
          _buildAccountRow(
            label: 'Email Address',
            controller: _emailController,
            hint: 'Email',
            keyboardType: TextInputType.emailAddress,
          ),
          _buildAccountDivider(),
          _buildAccountRow(
            label: 'Linked Phone Number',
            controller: _phoneController,
            preferenceKey: 'gir_user_phone',
            hint: '+254 700 000 000',
            keyboardType: TextInputType.phone,
          ),
          _buildAccountDivider(),
          _buildAccountRow(
            label: 'Organization Name',
            controller: _orgController,
            preferenceKey: 'gir_user_org',
            hint: 'Organization',
          ),
          const SizedBox(height: 5),
        ],
      ),
    );
  }

  Widget _buildAccountDivider() => const Padding(
        padding: EdgeInsets.symmetric(horizontal: 14),
        child: Divider(height: 1, color: Color(0xFF666666)),
      );

  Widget _buildAccountRow({
    required String label,
    required TextEditingController controller,
    required String hint,
    String? preferenceKey,
    TextInputType? keyboardType,
  }) {
    final editable = preferenceKey != null;
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: editable
            ? () => _editAccountField(
                  label: label,
                  controller: controller,
                  preferenceKey: preferenceKey,
                  hint: hint,
                  keyboardType: keyboardType,
                )
            : null,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      label,
                      style: const TextStyle(
                        color: Color(0xFFD0D0D0),
                        fontSize: 11,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      controller.text.isEmpty ? hint : controller.text,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        color: controller.text.isEmpty
                            ? const Color(0xFFB8B8B8)
                            : Colors.white,
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 12),
              Icon(
                editable ? Icons.edit_outlined : Icons.mail_outline_rounded,
                size: 18,
                color: const Color(0xFFE5E5E5),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _editAccountField({
    required String label,
    required TextEditingController controller,
    required String? preferenceKey,
    required String hint,
    TextInputType? keyboardType,
  }) async {
    if (preferenceKey == null) return;

    final draftController = TextEditingController(text: controller.text);
    final updatedValue = await showDialog<String>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        backgroundColor: const Color(0xFF424242),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
        title: Text('Edit $label',
            style: const TextStyle(color: Colors.white, fontSize: 18)),
        content: TextField(
          controller: draftController,
          autofocus: true,
          keyboardType: keyboardType,
          style: const TextStyle(color: Colors.white),
          cursorColor: Colors.white,
          decoration: InputDecoration(
            hintText: hint,
            hintStyle: const TextStyle(color: Color(0xFFB8B8B8)),
            enabledBorder: const UnderlineInputBorder(
                borderSide: BorderSide(color: Color(0xFF888888))),
            focusedBorder: const UnderlineInputBorder(
                borderSide: BorderSide(color: Color(0xFFE5E5E5))),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(),
            child: const Text('Cancel',
                style: TextStyle(color: Color(0xFFB8B8B8))),
          ),
          TextButton(
            onPressed: () =>
                Navigator.of(dialogContext).pop(draftController.text.trim()),
            child:
                const Text('Save', style: TextStyle(color: Color(0xFFE5E5E5))),
          ),
        ],
      ),
    );
    draftController.dispose();
    if (updatedValue == null || !mounted) return;

    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(preferenceKey, updatedValue);
    if (!mounted) return;
    setState(() => controller.text = updatedValue);
    widget.onSettingsUpdated();
  }
}

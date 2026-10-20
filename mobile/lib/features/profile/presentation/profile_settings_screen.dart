import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
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
            _buildAccountInformationCard(),
            const SizedBox(height: 18),
            const Text('© 2026 IcapsQ. All rights reserved.',
                textAlign: TextAlign.center,
                style: TextStyle(color: Color(0xFF929292), fontSize: 11)),
          ],
        ),
      ),
    );
  }

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
          _buildAccountDivider(),
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
          _buildAccountDivider(),
          _settingsActionRow(
            icon: Icons.phone_android_rounded,
            title: 'IcapsQ Official App',
            subtitle: 'Version 2.1.19 · Build 24',
            trailing: const SizedBox(width: 4),
          ),
          _buildAccountDivider(),
          _settingsActionRow(
            icon: Icons.info_outline_rounded,
            title: 'Terms of Service',
            trailing: const Icon(Icons.chevron_right_rounded,
                color: Color(0xFFB8B8B8), size: 22),
            onTap: () => LegalDialogs.showTermsOfService(context),
          ),
          _buildAccountDivider(),
          _settingsActionRow(
            icon: Icons.privacy_tip_outlined,
            title: 'Privacy Policy',
            trailing: const Icon(Icons.chevron_right_rounded,
                color: Color(0xFFB8B8B8), size: 22),
            onTap: () => LegalDialogs.showPrivacyPolicy(context),
          ),
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

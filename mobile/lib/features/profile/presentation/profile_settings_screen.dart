import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../../core/theme/app_theme.dart';
import '../../legal/presentation/legal_dialogs.dart';
import '../../../core/network/api_client.dart';

class ProfileSettingsScreen extends StatefulWidget {
  final VoidCallback onSettingsUpdated;

  const ProfileSettingsScreen({super.key, required this.onSettingsUpdated});

  @override
  ProfileSettingsScreenState createState() => ProfileSettingsScreenState();
}

class ProfileSettingsScreenState extends State<ProfileSettingsScreen> {
  static const _background = AppColors.graphite900;
  static const _surface = AppColors.graphite700;
  static const _surfaceBorder = Color(0xFF565960);
  static const _primaryText = AppColors.graphite50;
  static const _secondaryText = AppColors.graphite300;
  static const _accent = AppColors.graphite50;

  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _phoneController = TextEditingController();
  final _orgController = TextEditingController();

  bool _notificationsEnabled = true;
  bool _isPlanLoading = true;
  bool _planUnavailable = false;
  String _userPlan = '';

  @override
  void initState() {
    super.initState();
    refreshProfile();
  }

  Future<void> refreshProfile() async {
    final prefs = await SharedPreferences.getInstance();
    if (!mounted) return;

    setState(() {
      _nameController.text = prefs.getString('gir_user_name') ?? 'User';
      _emailController.text =
          prefs.getString('gir_user_email') ?? 'user@getitright.io';
      _phoneController.text = prefs.getString('gir_user_phone') ?? '';
      _orgController.text = prefs.getString('gir_user_org') ?? 'Independent';
      _notificationsEnabled =
          prefs.getBool('gir_notifications_enabled') ?? true;
      _userPlan = '';
      _isPlanLoading = true;
      _planUnavailable = false;
    });

    final userId = prefs.getString('gir_user_id');
    final remoteUser =
        userId == null ? null : await ApiClient().fetchUserProfile(userId);
    if (!mounted) return;

    if (remoteUser != null) {
      final remotePlan = remoteUser['plan']?.toString().trim();
      if (remotePlan != null && remotePlan.isNotEmpty) {
        _userPlan = remotePlan;
        _planUnavailable = false;
        await prefs.setString('gir_user_plan', remotePlan);
        await prefs.setBool('gir_plan_chosen', true);
      } else if (remoteUser['isAdmin'] == true ||
          (remoteUser['role']?.toString().toLowerCase().contains('admin') ??
              false)) {
        _userPlan = 'admin';
      } else {
        _planUnavailable = true;
      }

      final remoteName = remoteUser['fullName']?.toString().trim();
      if (remoteName != null && remoteName.isNotEmpty) {
        _nameController.text = remoteName;
        await prefs.setString('gir_user_name', remoteName);
      }
      final remoteEmail = remoteUser['email']?.toString().trim();
      if (remoteEmail != null && remoteEmail.isNotEmpty) {
        _emailController.text = remoteEmail;
        await prefs.setString('gir_user_email', remoteEmail);
      }
      final remotePhone =
          (remoteUser['phone'] ?? remoteUser['phoneNumber'])?.toString().trim();
      if (remotePhone != null && remotePhone.isNotEmpty) {
        _phoneController.text = remotePhone;
        await prefs.setString('gir_user_phone', remotePhone);
      }
      final remoteOrganization = remoteUser['organization']?.toString().trim();
      if (remoteOrganization != null && remoteOrganization.isNotEmpty) {
        _orgController.text = remoteOrganization;
        await prefs.setString('gir_user_org', remoteOrganization);
      }
    } else {
      _planUnavailable = true;
    }

    setState(() => _isPlanLoading = false);
    widget.onSettingsUpdated();
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
      color: _background,
      child: SafeArea(
        top: false,
        child: RefreshIndicator(
          onRefresh: refreshProfile,
          color: _accent,
          backgroundColor: _surface,
          child: ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.fromLTRB(16, 18, 16, 30),
            children: [
              _buildProfileHeader(),
              const SizedBox(height: 18),
              _buildAccountAndSettingsCard(),
              const SizedBox(height: 18),
              const Text(
                '© 2026 IcapsQ. All rights reserved.',
                textAlign: TextAlign.center,
                style: TextStyle(color: AppColors.graphite500, fontSize: 11),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildProfileHeader() {
    final name = _nameController.text.trim();
    final initial = name.isEmpty ? 'U' : name.characters.first.toUpperCase();
    final planColor = _planColor(_userPlan);

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [AppColors.graphite700, AppColors.graphite900],
        ),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: _surfaceBorder),
      ),
      child: Row(
        children: [
          Container(
            width: 62,
            height: 62,
            decoration: BoxDecoration(
              color: AppColors.graphite50,
              shape: BoxShape.circle,
              border: Border.all(color: Colors.white, width: 1.2),
            ),
            alignment: Alignment.center,
            child: Text(
              initial,
              style: const TextStyle(
                color: AppColors.graphite900,
                fontSize: 25,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
          const SizedBox(width: 15),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  name.isEmpty ? 'Your profile' : name,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    color: _primaryText,
                    fontSize: 18,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 8),
                if (_isPlanLoading)
                  Row(
                    children: const [
                      SizedBox(
                        width: 12,
                        height: 12,
                        child: CircularProgressIndicator(
                          strokeWidth: 1.7,
                          color: _accent,
                        ),
                      ),
                      SizedBox(width: 8),
                      Text(
                        'Checking current plan',
                        style: TextStyle(color: _secondaryText, fontSize: 12),
                      ),
                    ],
                  )
                else
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                    decoration: BoxDecoration(
                      color: planColor.withValues(alpha: 0.14),
                      borderRadius: BorderRadius.circular(30),
                      border:
                          Border.all(color: planColor.withValues(alpha: 0.4)),
                    ),
                    child: Text(
                      _planUnavailable
                          ? 'PLAN UNAVAILABLE'
                          : _planDisplayName(_userPlan),
                      style: TextStyle(
                        color: planColor,
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 0.3,
                      ),
                    ),
                  ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          const Icon(Icons.verified_user_outlined,
              color: AppColors.graphite50, size: 21),
        ],
      ),
    );
  }

  Widget _buildAccountAndSettingsCard() {
    return Container(
      decoration: BoxDecoration(
        color: _surface,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: _surfaceBorder),
        boxShadow: const [
          BoxShadow(
              color: Color(0x26000000), blurRadius: 18, offset: Offset(0, 8)),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildSectionHeader('ACCOUNT DETAILS'),
            _buildAccountRow(
              icon: Icons.person_outline_rounded,
              label: 'Username',
              controller: _nameController,
              hint: 'Name',
            ),
            _buildDivider(),
            _buildAccountRow(
              icon: Icons.alternate_email_rounded,
              label: 'Email address',
              controller: _emailController,
              hint: 'Email',
              keyboardType: TextInputType.emailAddress,
            ),
            _buildDivider(),
            _buildAccountRow(
              icon: Icons.phone_outlined,
              label: 'Linked phone number',
              controller: _phoneController,
              preferenceKey: 'gir_user_phone',
              hint: '+254 700 000 000',
              keyboardType: TextInputType.phone,
            ),
            _buildDivider(),
            _buildAccountRow(
              icon: Icons.apartment_rounded,
              label: 'Organization',
              controller: _orgController,
              preferenceKey: 'gir_user_org',
              hint: 'Independent',
            ),
            _buildSectionHeader('PREFERENCES & ABOUT'),
            _buildSettingsRow(
              icon: Icons.notifications_active_outlined,
              title: 'Push notifications',
              subtitle: 'Poll updates and results',
              trailing: Switch(
                value: _notificationsEnabled,
                activeColor: Colors.white,
                activeTrackColor: _accent,
                inactiveThumbColor: AppColors.graphite300,
                inactiveTrackColor: const Color(0xFF4B4D53),
                onChanged: _setNotifications,
              ),
            ),
            _buildDivider(),
            _buildSettingsRow(
              icon: Icons.phone_android_rounded,
              title: 'IcapsQ app',
              subtitle: 'Version 2.1.22  ·  Build 27',
              trailing: const SizedBox(width: 8),
            ),
            _buildDivider(),
            _buildSettingsRow(
              icon: Icons.description_outlined,
              title: 'Terms of Service',
              trailing: const Icon(Icons.chevron_right_rounded,
                  color: _secondaryText, size: 23),
              onTap: () => LegalDialogs.showTermsOfService(context),
            ),
            _buildDivider(),
            _buildSettingsRow(
              icon: Icons.shield_outlined,
              title: 'Privacy Policy',
              trailing: const Icon(Icons.chevron_right_rounded,
                  color: _secondaryText, size: 23),
              onTap: () => LegalDialogs.showPrivacyPolicy(context),
            ),
            const SizedBox(height: 8),
          ],
        ),
      ),
    );
  }

  Widget _buildSectionHeader(String title) => Padding(
        padding: const EdgeInsets.fromLTRB(17, 18, 16, 8),
        child: Text(
          title,
          style: const TextStyle(
            color: AppColors.graphite300,
            fontSize: 10,
            fontWeight: FontWeight.w700,
            letterSpacing: 1.15,
          ),
        ),
      );

  Widget _buildAccountRow({
    required IconData icon,
    required String label,
    required TextEditingController controller,
    required String hint,
    String? preferenceKey,
    TextInputType? keyboardType,
  }) {
    final editable = preferenceKey != null;
    return InkWell(
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
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 11),
        child: Row(
          children: [
            _iconTile(icon),
            const SizedBox(width: 13),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(label,
                      style: const TextStyle(
                          color: _secondaryText,
                          fontSize: 11,
                          fontWeight: FontWeight.w500)),
                  const SizedBox(height: 4),
                  Text(
                    controller.text.isEmpty ? hint : controller.text,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      color: controller.text.isEmpty
                          ? AppColors.graphite300
                          : _primaryText,
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 10),
            Icon(
              editable ? Icons.edit_outlined : Icons.lock_outline_rounded,
              size: 17,
              color: AppColors.graphite300,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSettingsRow({
    required IconData icon,
    required String title,
    String? subtitle,
    required Widget trailing,
    VoidCallback? onTap,
  }) =>
      ListTile(
        onTap: onTap,
        minLeadingWidth: 36,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 1),
        leading: _iconTile(icon),
        title: Text(title,
            style: const TextStyle(
                color: _primaryText,
                fontSize: 14,
                fontWeight: FontWeight.w600)),
        subtitle: subtitle == null
            ? null
            : Text(subtitle,
                style: const TextStyle(color: _secondaryText, fontSize: 11)),
        trailing: trailing,
      );

  Widget _iconTile(IconData icon) => Container(
        width: 36,
        height: 36,
        decoration: BoxDecoration(
          color: const Color(0xFF414349),
          borderRadius: BorderRadius.circular(12),
        ),
        alignment: Alignment.center,
        child: Icon(icon, color: _accent, size: 19),
      );

  Widget _buildDivider() => const Padding(
        padding: EdgeInsets.only(left: 65, right: 16),
        child: Divider(height: 1, color: Color(0xFF55575D)),
      );

  String _planDisplayName(String plan) {
    switch (plan.trim().toLowerCase()) {
      case 'pro':
        return 'PRO';
      case 'org':
      case 'organization':
        return 'ORGANIZATION';
      case 'election':
        return 'ELECTION';
      case 'free':
      case '':
        return 'FREE';
      default:
        return plan.toUpperCase();
    }
  }

  Color _planColor(String plan) {
    return _accent;
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
        backgroundColor: AppColors.graphite900,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: Text('Edit $label',
            style: const TextStyle(color: _primaryText, fontSize: 18)),
        content: TextField(
          controller: draftController,
          autofocus: true,
          keyboardType: keyboardType,
          style: const TextStyle(color: _primaryText),
          cursorColor: _accent,
          decoration: InputDecoration(
            hintText: hint,
            hintStyle: const TextStyle(color: _secondaryText),
            enabledBorder: const UnderlineInputBorder(
                borderSide: BorderSide(color: _surfaceBorder)),
            focusedBorder: const UnderlineInputBorder(
                borderSide: BorderSide(color: _accent)),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(),
            child:
                const Text('Cancel', style: TextStyle(color: _secondaryText)),
          ),
          TextButton(
            onPressed: () =>
                Navigator.of(dialogContext).pop(draftController.text.trim()),
            child: const Text('Save', style: TextStyle(color: _accent)),
          ),
        ],
      ),
    );
    draftController.dispose();
    if (updatedValue == null || !mounted) return;

    final response = await ApiClient().updateUserProfile(
      phoneNumber: preferenceKey == 'gir_user_phone' ? updatedValue : null,
      organization: preferenceKey == 'gir_user_org'
          ? (updatedValue.isEmpty ? 'Independent' : updatedValue)
          : null,
    );
    if (!mounted) return;
    if (response['success'] != true) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(response['error']?.toString() ??
              'Could not save your profile changes. Try again.'),
          backgroundColor: const Color(0xFFE5E5E5),
          duration: const Duration(seconds: 4),
        ),
      );
      return;
    }

    final savedValue = preferenceKey == 'gir_user_org' && updatedValue.isEmpty
        ? 'Independent'
        : updatedValue;

    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(preferenceKey, savedValue);
    setState(() => controller.text = savedValue);
    widget.onSettingsUpdated();
  }
}

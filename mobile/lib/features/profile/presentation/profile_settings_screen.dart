import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../auth/presentation/plan_selection_screen.dart';
import '../../../core/network/api_client.dart';

class ProfileSettingsScreen extends StatefulWidget {
  final VoidCallback onSettingsUpdated;

  const ProfileSettingsScreen({super.key, required this.onSettingsUpdated});

  @override
  State<ProfileSettingsScreen> createState() => _ProfileSettingsScreenState();
}

class _ProfileSettingsScreenState extends State<ProfileSettingsScreen> {
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _orgController = TextEditingController();

  String _currentPlan = 'free';
  bool _notificationsEnabled = true;
  bool _isSaving = false;

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _nameController.text = prefs.getString('gir_user_name') ?? 'User';
      _emailController.text = prefs.getString('gir_user_email') ?? 'user@getitright.io';
      _orgController.text = prefs.getString('gir_user_org') ?? 'Independent';
      _currentPlan = prefs.getString('gir_user_plan') ?? 'free';
      _notificationsEnabled = prefs.getBool('gir_notifications_enabled') ?? true;
    });
  }

  Future<void> _saveSettings() async {
    setState(() => _isSaving = true);
    final prefs = await SharedPreferences.getInstance();

    await prefs.setString('gir_user_name', _nameController.text.trim());
    await prefs.setString('gir_user_email', _emailController.text.trim());
    await prefs.setString('gir_user_org', _orgController.text.trim());
    await prefs.setBool('gir_notifications_enabled', _notificationsEnabled);

    if (mounted) {
      setState(() => _isSaving = false);
      widget.onSettingsUpdated();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Settings saved successfully',
            style: TextStyle(color: Color(0xFF2A2A2A), fontWeight: FontWeight.bold),
          ),
          backgroundColor: Color(0xFFE5E5E5),
          duration: Duration(seconds: 2),
        ),
      );
    }
  }

  void _openPlanSelection() async {
    final prefs = await SharedPreferences.getInstance();
    final userId = prefs.getString('gir_user_id') ?? 'USR-001';

    if (!mounted) return;
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (context) => PlanSelectionScreen(
          userData: {
            'id': userId,
            'fullName': _nameController.text,
            'plan': _currentPlan,
          },
          onProceed: () async {
            Navigator.of(context).pop();
            final updatedPlan = (await SharedPreferences.getInstance()).getString('gir_user_plan') ?? _currentPlan;
            setState(() => _currentPlan = updatedPlan);
            widget.onSettingsUpdated();
          },
        ),
      ),
    );
  }

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _orgController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF303030),
      appBar: AppBar(
        backgroundColor: const Color(0xFF303030),
        elevation: 0,
        title: const Text(
          'Settings & Profile',
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 18),
        ),
        centerTitle: true,
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // User Avatar
              Center(
                child: Container(
                  width: 90,
                  height: 90,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: const Color(0xFF505050),
                    border: Border.all(color: const Color(0xFF666666), width: 2),
                  ),
                  child: const Icon(Icons.person, size: 48, color: Color(0xFFD0D0D0)),
                ),
              ),

              const SizedBox(height: 24),

              // Section 1: Account Settings
              _buildSectionHeader('ACCOUNT INFORMATION'),
              const SizedBox(height: 10),

              _buildFieldLabel('Display Name'),
              const SizedBox(height: 6),
              _buildPillInput(controller: _nameController, hint: 'Name'),

              const SizedBox(height: 14),

              _buildFieldLabel('Email Address'),
              const SizedBox(height: 6),
              _buildPillInput(controller: _emailController, hint: 'Email', keyboardType: TextInputType.emailAddress),

              const SizedBox(height: 14),

              _buildFieldLabel('Organization Name'),
              const SizedBox(height: 6),
              _buildPillInput(controller: _orgController, hint: 'Organization'),

              const SizedBox(height: 24),

              // Section 2: Subscription Plan
              _buildSectionHeader('SUBSCRIPTION PLAN'),
              const SizedBox(height: 10),

              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: const Color(0xFF505050),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.star, color: Colors.white, size: 22),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Current Plan: ${_currentPlan.toUpperCase()}',
                            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14),
                          ),
                          const SizedBox(height: 2),
                          const Text(
                            'Upgrade or change your plan tier',
                            style: TextStyle(color: Color(0xFFB8B8B8), fontSize: 12),
                          ),
                        ],
                      ),
                    ),
                    ElevatedButton(
                      onPressed: _openPlanSelection,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFFE5E5E5),
                        foregroundColor: const Color(0xFF2A2A2A),
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                      ),
                      child: const Text('Change', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 24),

              // Section 3: Notification Preferences
              _buildSectionHeader('PREFERENCES'),
              const SizedBox(height: 10),

              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                decoration: BoxDecoration(
                  color: const Color(0xFF505050),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Push Notifications', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 14)),
                        SizedBox(height: 2),
                        Text('Receive live updates and poll results', style: TextStyle(color: Color(0xFFB8B8B8), fontSize: 12)),
                      ],
                    ),
                    Switch(
                      value: _notificationsEnabled,
                      activeColor: const Color(0xFFE5E5E5),
                      activeTrackColor: const Color(0xFF606060),
                      inactiveTrackColor: const Color(0xFF404040),
                      onChanged: (val) => setState(() => _notificationsEnabled = val),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 24),

              // Section 4: App Version & Updates
              _buildSectionHeader('APP VERSION & UPDATES'),
              const SizedBox(height: 10),

              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: const Color(0xFF505050),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Getitright Official App',
                              style: TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.bold,
                                fontSize: 14,
                              ),
                            ),
                            SizedBox(height: 3),
                            Text(
                              'Version 1.0.0 (Build 1)',
                              style: TextStyle(
                                color: Color(0xFFB8B8B8),
                                fontSize: 12,
                              ),
                            ),
                          ],
                        ),
                        ElevatedButton.icon(
                          onPressed: _checkUpdateManually,
                          icon: const Icon(Icons.sync, size: 16),
                          label: const Text(
                            'Check',
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFFE5E5E5),
                            foregroundColor: const Color(0xFF2A2A2A),
                            elevation: 0,
                            padding: const EdgeInsets.symmetric(
                              horizontal: 14,
                              vertical: 8,
                            ),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(20),
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    const Text(
                      'Getitright updates ensure you have the latest cryptographic verification rules, live voting feeds, and performance optimizations.',
                      style: TextStyle(
                        color: Color(0xFFD0D0D0),
                        fontSize: 11.5,
                        height: 1.35,
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 32),

              // Save Button
              SizedBox(
                width: double.infinity,
                height: 50,
                child: ElevatedButton(
                  onPressed: _isSaving ? null : _saveSettings,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFFE5E5E5),
                    foregroundColor: const Color(0xFF2A2A2A),
                    elevation: 0,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(25)),
                  ),
                  child: _isSaving
                      ? const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(color: Colors.black, strokeWidth: 2.5))
                      : const Text('Save Settings', style: TextStyle(color: Color(0xFF2A2A2A), fontSize: 15, fontWeight: FontWeight.bold)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _checkUpdateManually() async {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text(
          'Checking for latest updates...',
          style: TextStyle(color: Color(0xFF2A2A2A), fontWeight: FontWeight.bold),
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
              'You are using the latest version of Getitright (v1.0.0)',
              style: TextStyle(color: Color(0xFF2A2A2A), fontWeight: FontWeight.bold),
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
            content: Text('Could not reach update server. Please try again later.'),
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
              child: const Icon(Icons.system_update_rounded, color: Color(0xFFE5E5E5), size: 24),
            ),
            const SizedBox(width: 12),
            const Expanded(
              child: Text(
                'Update Available',
                style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 18),
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
                'Version $version is now available (Current: v1.0.0)',
                style: const TextStyle(color: Color(0xFFE5E5E5), fontSize: 12, fontWeight: FontWeight.w600),
              ),
            ),
            const SizedBox(height: 14),
            const Text(
              'What\'s New in this release:',
              style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 13),
            ),
            const SizedBox(height: 6),
            Text(
              releaseNotes ??
                  '• Instant scroll-to-top navigation\n'
                  '• Real-time poll vote tallying & animated charts\n'
                  '• Cryptographic survey receipt verification\n'
                  '• Offline vote persistence & auto-sync\n'
                  '• Stability & performance improvements',
              style: const TextStyle(color: Color(0xFFD0D0D0), fontSize: 12.5, height: 1.45),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('Later', style: TextStyle(color: Color(0xFFB8B8B8), fontWeight: FontWeight.w600)),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.of(ctx).pop();
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text(
                    'Downloading Getitright v$version...',
                    style: const TextStyle(color: Color(0xFF2A2A2A), fontWeight: FontWeight.bold),
                  ),
                  backgroundColor: const Color(0xFFE5E5E5),
                  duration: const Duration(seconds: 3),
                ),
              );
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFFE5E5E5),
              foregroundColor: const Color(0xFF2A2A2A),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            ),
            child: const Text('Update Now', style: TextStyle(fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionHeader(String title) {
    return Text(
      title,
      style: const TextStyle(color: Color(0xFFB8B8B8), fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 1.0),
    );
  }

  Widget _buildFieldLabel(String label) {
    return Text(
      label,
      style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.w500),
    );
  }

  Widget _buildPillInput({
    required TextEditingController controller,
    required String hint,
    TextInputType? keyboardType,
  }) {
    return Container(
      height: 48,
      decoration: BoxDecoration(
        color: const Color(0xFF505050),
        borderRadius: BorderRadius.circular(24),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 20),
      alignment: Alignment.centerLeft,
      child: TextField(
        controller: controller,
        keyboardType: keyboardType,
        style: const TextStyle(color: Colors.white, fontSize: 14),
        cursorColor: Colors.white,
        decoration: InputDecoration(
          hintText: hint,
          hintStyle: const TextStyle(color: Color(0xFFB8B8B8), fontSize: 14),
          border: InputBorder.none,
          enabledBorder: InputBorder.none,
          focusedBorder: InputBorder.none,
          contentPadding: EdgeInsets.zero,
          isDense: true,
        ),
      ),
    );
  }
}

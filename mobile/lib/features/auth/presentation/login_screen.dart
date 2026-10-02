import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';

class LoginScreen extends StatefulWidget {
  final Function(String role) onLoginSuccess;

  const LoginScreen({super.key, required this.onLoginSuccess});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  String _selectedRole = 'org'; // 'org' or 'user'
  final _emailController = TextEditingController(text: 'admin@acme.org');
  final _passwordController = TextEditingController(text: '********');
  final _orgNameController = TextEditingController(text: 'Acme Systems');

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _orgNameController.dispose();
    super.dispose();
  }

  void _submit() {
    widget.onLoginSuccess(_selectedRole);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Brand Header
                Center(
                  child: Container(
                    width: 56,
                    height: 56,
                    decoration: BoxDecoration(
                      color: AppColors.accent,
                      borderRadius: BorderRadius.circular(16),
                      boxShadow: [
                        BoxShadow(
                          color: AppColors.accent.withOpacity(0.35),
                          blurRadius: 20,
                          offset: const Offset(0, 4),
                        ),
                      ],
                    ),
                    child: const Icon(Icons.bar_chart, color: Colors.black, size: 32),
                  ),
                ),
                const SizedBox(height: 16),
                Center(
                  child: RichText(
                    text: const TextSpan(
                      style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
                      children: [
                        TextSpan(text: 'getitright', style: TextStyle(color: AppColors.textPrimary)),
                        TextSpan(text: '.', style: TextStyle(color: AppColors.accent)),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 6),
                const Center(
                  child: Text(
                    'Multi-platform Surveys & Polling Engine',
                    style: TextStyle(color: AppColors.textSecondary, fontSize: 13),
                  ),
                ),
                const SizedBox(height: 36),

                // Role Selector Switch
                Container(
                  padding: const EdgeInsets.all(4),
                  decoration: BoxDecoration(
                    color: AppColors.bgElevated,
                    borderRadius: BorderRadius.circular(AppRadius.button),
                    border: Border.all(color: AppColors.border),
                  ),
                  child: Row(
                    children: [
                      Expanded(
                        child: InkWell(
                          onTap: () => setState(() => _selectedRole = 'org'),
                          borderRadius: BorderRadius.circular(AppRadius.button - 2),
                          child: Container(
                            padding: const EdgeInsets.symmetric(vertical: 10),
                            decoration: BoxDecoration(
                              color: _selectedRole == 'org' ? AppColors.accent : Colors.transparent,
                              borderRadius: BorderRadius.circular(AppRadius.button - 2),
                            ),
                            child: Center(
                              child: Text(
                                'Organization',
                                style: TextStyle(
                                  color: _selectedRole == 'org' ? Colors.black : AppColors.textSecondary,
                                  fontWeight: FontWeight.w600,
                                  fontSize: 13,
                                ),
                              ),
                            ),
                          ),
                        ),
                      ),
                      Expanded(
                        child: InkWell(
                          onTap: () => setState(() => _selectedRole = 'user'),
                          borderRadius: BorderRadius.circular(AppRadius.button - 2),
                          child: Container(
                            padding: const EdgeInsets.symmetric(vertical: 10),
                            decoration: BoxDecoration(
                              color: _selectedRole == 'user' ? AppColors.accent : Colors.transparent,
                              borderRadius: BorderRadius.circular(AppRadius.button - 2),
                            ),
                            child: Center(
                              child: Text(
                                'Voter / Participant',
                                style: TextStyle(
                                  color: _selectedRole == 'user' ? Colors.black : AppColors.textSecondary,
                                  fontWeight: FontWeight.w600,
                                  fontSize: 13,
                                ),
                              ),
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 24),

                if (_selectedRole == 'org') ...[
                  const Text('Organization / Institution Name',
                      style: TextStyle(color: AppColors.textSecondary, fontSize: 12)),
                  const SizedBox(height: 6),
                  TextField(
                    controller: _orgNameController,
                    decoration: const InputDecoration(
                      hintText: 'e.g. Acme University or TechCorp',
                      prefixIcon: Icon(Icons.business, color: AppColors.textSecondary),
                    ),
                  ),
                  const SizedBox(height: 16),
                ],

                const Text('Email Address', style: TextStyle(color: AppColors.textSecondary, fontSize: 12)),
                const SizedBox(height: 6),
                TextField(
                  controller: _emailController,
                  decoration: const InputDecoration(
                    hintText: 'name@institution.com',
                    prefixIcon: Icon(Icons.email_outlined, color: AppColors.textSecondary),
                  ),
                ),
                const SizedBox(height: 16),

                const Text('Password', style: TextStyle(color: AppColors.textSecondary, fontSize: 12)),
                const SizedBox(height: 6),
                TextField(
                  controller: _passwordController,
                  obscureText: true,
                  decoration: const InputDecoration(
                    hintText: 'Enter password',
                    prefixIcon: Icon(Icons.lock_outline, color: AppColors.textSecondary),
                  ),
                ),
                const SizedBox(height: 28),

                // Submit Button
                ElevatedButton(
                  onPressed: _submit,
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(_selectedRole == 'org' ? 'Launch Organization Console' : 'Enter Live Polling'),
                      const SizedBox(width: 8),
                      const Icon(Icons.arrow_forward, size: 18),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../../core/network/api_client.dart';
import 'plan_selection_screen.dart';
import 'password_recovery_screen.dart';
import '../../legal/presentation/legal_dialogs.dart';

class LoginScreen extends StatefulWidget {
  final Function(String role) onLoginSuccess;

  const LoginScreen({super.key, required this.onLoginSuccess});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final ApiClient _apiClient = ApiClient();
  bool _isSignUp = false;
  bool _isLoading = false;
  bool _showPassword = false;
  String? _errorMessage;

  final _fullNameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _dobController = TextEditingController();
  final _nationalIdController = TextEditingController();
  final _countyController = TextEditingController();
  final _orgController = TextEditingController();
  final _roleController = TextEditingController();

  static const List<String> _kenyanCounties = [
    'Baringo',
    'Bomet',
    'Bungoma',
    'Busia',
    'Elgeyo-Marakwet',
    'Embu',
    'Garissa',
    'Homa Bay',
    'Isiolo',
    'Kajiado',
    'Kakamega',
    'Kericho',
    'Kiambu',
    'Kilifi',
    'Kirinyaga',
    'Kisii',
    'Kisumu',
    'Kitui',
    'Kwale',
    'Laikipia',
    'Lamu',
    'Machakos',
    'Makueni',
    'Mandera',
    'Marsabit',
    'Meru',
    'Migori',
    'Mombasa',
    'Murang\'a',
    'Nairobi',
    'Nakuru',
    'Nandi',
    'Narok',
    'Nyamira',
    'Nyandarua',
    'Nyeri',
    'Samburu',
    'Siaya',
    'Taita-Taveta',
    'Tana River',
    'Tharaka-Nithi',
    'Trans Nzoia',
    'Turkana',
    'Uasin Gishu',
    'Vihiga',
    'Wajir',
    'West Pokot',
  ];

  @override
  void dispose() {
    _fullNameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _dobController.dispose();
    _nationalIdController.dispose();
    _countyController.dispose();
    _orgController.dispose();
    _roleController.dispose();
    super.dispose();
  }

  Future<void> _pickDob() async {
    final now = DateTime.now();
    DateTime initial = DateTime(now.year - 20, now.month, now.day);
    if (_dobController.text.trim().isNotEmpty) {
      try {
        final parsed = DateTime.parse(_dobController.text.trim());
        if (parsed.isBefore(now) && parsed.isAfter(DateTime(1920))) {
          initial = parsed;
        }
      } catch (_) {}
    }
    final picked = await showDatePicker(
      context: context,
      initialDate: initial,
      firstDate: DateTime(1920),
      lastDate: now,
      initialDatePickerMode: DatePickerMode.year,
      helpText: 'SELECT DATE OF BIRTH',
      builder: (context, child) {
        return Theme(
          data: Theme.of(context).copyWith(
            colorScheme: const ColorScheme.dark(
              primary: Color(0xFFF2F2F3),
              onPrimary: Color(0xFF1F2023),
              surface: Color(0xFF2E3035),
              onSurface: Colors.white,
            ),
            dialogBackgroundColor: const Color(0xFF1F2023),
          ),
          child: child!,
        );
      },
    );

    if (picked != null) {
      final formatted =
          "${picked.year.toString().padLeft(4, '0')}-${picked.month.toString().padLeft(2, '0')}-${picked.day.toString().padLeft(2, '0')}";
      setState(() {
        _dobController.text = formatted;
        _errorMessage = null;
      });
    }
  }

  Future<void> _pickCounty() async {
    final selected = await showModalBottomSheet<String>(
      context: context,
      backgroundColor: const Color(0xFF1F2023),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      isScrollControlled: true,
      builder: (context) {
        String filter = '';
        return StatefulBuilder(
          builder: (context, setModalState) {
            final filtered = _kenyanCounties
                .where((c) => c.toLowerCase().contains(filter.toLowerCase()))
                .toList();
            return Container(
              height: 480,
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
              child: Column(
                children: [
                  Container(
                    width: 40,
                    height: 4,
                    decoration: BoxDecoration(
                      color: const Color(0xFF6B6E76),
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                  const SizedBox(height: 12),
                  const Text(
                    'Select County',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    onChanged: (val) => setModalState(() => filter = val),
                    style: const TextStyle(color: Colors.white, fontSize: 14),
                    cursorColor: Colors.white,
                    decoration: InputDecoration(
                      hintText: 'Search county...',
                      hintStyle: const TextStyle(color: Color(0xFF8E929B)),
                      prefixIcon:
                          const Icon(Icons.search, color: Color(0xFF8E929B)),
                      filled: true,
                      fillColor: const Color(0xFF2E3035),
                      contentPadding: const EdgeInsets.symmetric(
                          horizontal: 16, vertical: 12),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(15),
                        borderSide: BorderSide.none,
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Expanded(
                    child: ListView.separated(
                      itemCount: filtered.length,
                      separatorBuilder: (_, __) =>
                          const Divider(color: Color(0x22FFFFFF), height: 1),
                      itemBuilder: (context, index) {
                        final county = filtered[index];
                        final isSelected = _countyController.text == county;
                        return ListTile(
                          title: Text(
                            county,
                            style: TextStyle(
                              color: isSelected
                                  ? Colors.white
                                  : const Color(0xFFD0D0D0),
                              fontWeight: isSelected
                                  ? FontWeight.bold
                                  : FontWeight.normal,
                            ),
                          ),
                          trailing: isSelected
                              ? const Icon(Icons.check,
                                  color: Colors.white, size: 20)
                              : null,
                          onTap: () => Navigator.of(context).pop(county),
                        );
                      },
                    ),
                  ),
                ],
              ),
            );
          },
        );
      },
    );

    if (selected != null) {
      setState(() {
        _countyController.text = selected;
        _errorMessage = null;
      });
    }
  }

  Future<void> _handleSubmit() async {
    final email = _emailController.text.trim();
    final password = _passwordController.text;

    if (email.isEmpty || password.isEmpty) {
      setState(() => _errorMessage = 'Email and password required');
      return;
    }

    if (!email.contains('@') || !email.contains('.')) {
      setState(() => _errorMessage = 'Please enter a valid email address');
      return;
    }

    if (_isSignUp) {
      if (_fullNameController.text.trim().isEmpty) {
        setState(() => _errorMessage = 'Full name required');
        return;
      }
      final dob = _dobController.text.trim();
      if (dob.isEmpty) {
        setState(() => _errorMessage = 'Date of birth required');
        return;
      }
      if (!RegExp(r'^\d{4}-\d{2}-\d{2}$').hasMatch(dob)) {
        setState(() => _errorMessage = 'Date of birth must be YYYY-MM-DD');
        return;
      }
      if (_nationalIdController.text.trim().isEmpty) {
        setState(() => _errorMessage =
            'Please provide correct details: National ID is required.');
        return;
      }
      if (!RegExp(r'^\d{5,12}$').hasMatch(_nationalIdController.text.trim())) {
        setState(() => _errorMessage =
            'Please provide correct details: National ID must contain 5–12 numbers only.');
        return;
      }
      if (_countyController.text.trim().isEmpty) {
        setState(() => _errorMessage = 'County required');
        return;
      }
      // Enforce 12-char password with uppercase, lowercase, and number
      if (password.length < 12) {
        setState(() => _errorMessage = 'Password must be at least 12 characters.');
        return;
      }
      if (!RegExp(r'[A-Z]').hasMatch(password) ||
          !RegExp(r'[a-z]').hasMatch(password) ||
          !RegExp(r'[0-9]').hasMatch(password)) {
        setState(() => _errorMessage = 'Password must include uppercase, lowercase, and a number.');
        return;
      }
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      Map<String, dynamic>? userData;
      String? sessionToken;

      final orgName = _orgController.text.trim();
      final position = _roleController.text.trim();
      final hasOrgAndPosition = orgName.isNotEmpty && position.isNotEmpty;

      if (_isSignUp) {
        final regRes = await _apiClient.register(
          fullName: _fullNameController.text.trim(),
          email: email,
          password: password,
          dob: _dobController.text.trim(),
          nationalId: _nationalIdController.text.trim(),
          county: _countyController.text.trim(),
          organization: orgName.isNotEmpty ? orgName : 'Independent',
          organizationContactRole: position.isNotEmpty ? position : null,
        );

        if (regRes != null && regRes['user'] != null) {
          userData = regRes['user'] as Map<String, dynamic>;
          sessionToken = regRes['token']?.toString();
        } else {
          throw Exception('Your account was not created. Please try again.');
        }
      } else {
        final loginRes = await _apiClient.login(email, password);
        if (loginRes != null && loginRes['user'] != null) {
          userData = loginRes['user'] as Map<String, dynamic>;
          sessionToken = loginRes['token']?.toString();
        } else {
          throw Exception(
              'Sign-in did not return an authenticated account. Please try again.');
        }
      }

      if (sessionToken == null || sessionToken.isEmpty) {
        throw Exception(
            'Sign-in failed to create a secure session. Please try again.');
      }

      final role = (userData['role'] ?? 'Customer').toString().toLowerCase();
      final prefs = await SharedPreferences.getInstance();
      if (sessionToken != null && sessionToken.isNotEmpty) {
        await prefs.setString('gir_token', sessionToken);
      } else {
        await prefs.remove('gir_token');
      }
      await prefs.setString(
          'gir_user_id', userData['id']?.toString() ?? 'USR-101');
      await prefs.setString('gir_user_role', role);
      await prefs.setString(
          'gir_user_email', userData['email']?.toString() ?? email);
      await prefs.setString(
          'gir_user_name', userData['fullName']?.toString() ?? 'User');

      final phone = userData['phone']?.toString() ??
          userData['phoneNumber']?.toString() ??
          '';
      if (phone.isNotEmpty) {
        await prefs.setString('gir_user_phone', phone);
      }
      if (_isSignUp) {
        await prefs.setString('gir_user_dob', _dobController.text.trim());
        await prefs.setString(
            'gir_user_national_id', _nationalIdController.text.trim());
        await prefs.setString('gir_user_county', _countyController.text.trim());
      }

      final planChosen = prefs.getBool('gir_plan_chosen') ?? false;
      final serverPlan = userData['plan']?.toString().trim();
      final cachedPlan = prefs.getString('gir_user_plan');
      final savedPlan =
          serverPlan != null && serverPlan.isNotEmpty ? serverPlan : cachedPlan;

      if (mounted) {
        // Only ask for plan if during creating account they gave org name and position.
        // Otherwise (regular voter/user without org and position, or sign-in, or plan chosen), proceed straight to app.
        if (!_isSignUp ||
            !hasOrgAndPosition ||
            planChosen ||
            (savedPlan != null &&
                savedPlan.isNotEmpty &&
                savedPlan.toLowerCase() != 'free')) {
          if (savedPlan != null && savedPlan.isNotEmpty) {
            await prefs.setString('gir_user_plan', savedPlan);
            await prefs.setBool('gir_plan_chosen', true);
          } else {
            await prefs.setString('gir_user_plan', 'free');
            await prefs.setBool('gir_plan_chosen', true);
          }
          widget.onLoginSuccess(
              role == 'admin' || role == 'org' ? 'org' : 'user');
        } else {
          if (!mounted) return;
          final navigator = Navigator.of(context);
          navigator.push(
            MaterialPageRoute(
              builder: (subContext) => PlanSelectionScreen(
                userData: userData!,
                onProceed: () async {
                  final p = await SharedPreferences.getInstance();
                  await p.setBool('gir_plan_chosen', true);
                  navigator.pop();
                  widget.onLoginSuccess(
                      role == 'admin' || role == 'org' ? 'org' : 'user');
                },
              ),
            ),
          );
        }
      }

    } catch (e) {
      if (!mounted) return;
      var message = e.toString().replaceFirst('Exception: ', '').trim();
      final lower = message.toLowerCase();
      if (lower.contains('socketexception') ||
          lower.contains('failed host lookup') ||
          lower.contains('timed out')) {
        message =
            'Could not connect to IcapsQ. Check your internet connection and try again.';
      } else if (lower.contains('format_exception') ||
          lower.contains('type \'') ||
          lower.contains('null')) {
        message =
            'The server returned an unexpected response. Please try again shortly.';
      }
      setState(() => _errorMessage = message.isEmpty
          ? 'Could not complete your request. Check your details and try again.'
          : message);
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _openForgotPasswordScreen() {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => PasswordRecoveryScreen(
          initialEmail: _emailController.text.trim(),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF1F2023),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 36, vertical: 24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // Brand Logo with curved corners container
                Container(
                  width: 82,
                  height: 82,
                  decoration: BoxDecoration(
                    color: const Color(0xFF2E3035),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: const Color(0xFF3F4249), width: 1.5),
                  ),
                  alignment: Alignment.center,
                  child: SvgPicture.asset(
                    'assets/images/icapsq-mark-white.svg',
                    width: 48,
                    height: 54,
                    fit: BoxFit.contain,
                  ),
                ),

                const SizedBox(height: 36),

                // Error message
                if (_errorMessage != null) ...[
                  Text(
                    _errorMessage!,
                    style: const TextStyle(
                      color: Color(0xFFFF6B6B),
                      fontSize: 13,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 14),
                ],

                // Sign Up Fields
                if (_isSignUp) ...[
                  _buildPillInput(
                    controller: _fullNameController,
                    hint: 'Full Name',
                    prefixIcon: const Icon(Icons.person_outline,
                        color: Color(0xFFB8BAC0), size: 20),
                  ),
                  const SizedBox(height: 14),
                ],

                // Email Input
                _buildPillInput(
                  controller: _emailController,
                  hint: 'Email address',
                  keyboardType: TextInputType.emailAddress,
                  prefixIcon: const Icon(Icons.mail_outline,
                      color: Color(0xFFB8BAC0), size: 20),
                ),

                const SizedBox(height: 14),

                // Password Input
                _buildPillInput(
                  controller: _passwordController,
                  hint: 'Password',
                  obscureText: !_showPassword,
                  prefixIcon: const Icon(Icons.lock_outline,
                      color: Color(0xFFB8BAC0), size: 20),
                  suffixIcon: IconButton(
                    onPressed: () =>
                        setState(() => _showPassword = !_showPassword),
                    icon: Icon(
                      _showPassword
                          ? Icons.visibility_off_outlined
                          : Icons.visibility_outlined,
                      color: const Color(0xFFB8BAC0),
                      size: 20,
                    ),
                    tooltip: _showPassword ? 'Hide password' : 'Show password',
                    padding: EdgeInsets.zero,
                    constraints:
                        const BoxConstraints(minWidth: 32, minHeight: 40),
                  ),
                ),

                if (_isSignUp) ...[
                  const SizedBox(height: 14),
                  // Date of Birth Field with forced format & calendar picker
                  _buildPillInput(
                    controller: _dobController,
                    hint: '',
                    readOnly: true,
                    onTap: _pickDob,
                    prefixIcon: const Icon(Icons.calendar_today_outlined,
                        color: Color(0xFFB8BAC0), size: 20),
                    suffixIcon: const Icon(Icons.calendar_month,
                        color: Color(0xFFF2F2F3), size: 24),
                  ),
                  const SizedBox(height: 14),
                  // National ID Field
                  _buildPillInput(
                    controller: _nationalIdController,
                    hint: 'National ID · 5–12 digits',
                    keyboardType: TextInputType.number,
                    inputFormatters: [
                      FilteringTextInputFormatter.digitsOnly,
                      LengthLimitingTextInputFormatter(12),
                    ],
                    prefixIcon: const Icon(Icons.badge_outlined,
                        color: Color(0xFFB8BAC0), size: 20),
                  ),
                  const SizedBox(height: 14),
                  // County Field with Searchable Bottom Sheet
                  _buildPillInput(
                    controller: _countyController,
                    hint: 'Select County',
                    readOnly: true,
                    onTap: _pickCounty,
                    prefixIcon: const Icon(Icons.location_on_outlined,
                        color: Color(0xFFB8BAC0), size: 20),
                    suffixIcon: const Icon(Icons.arrow_drop_down,
                        color: Color(0xFFF2F2F3), size: 26),
                  ),
                  const SizedBox(height: 14),
                  _buildPillInput(
                    controller: _orgController,
                    hint: 'Organization Name (Optional)',
                    prefixIcon: const Icon(Icons.business_outlined,
                        color: Color(0xFFB8BAC0), size: 20),
                  ),
                  const SizedBox(height: 14),
                  _buildPillInput(
                    controller: _roleController,
                    hint: 'Sector / Role (Optional)',
                    prefixIcon: const Icon(Icons.work_outline,
                        color: Color(0xFFB8BAC0), size: 20),
                  ),
                ],

                const SizedBox(height: 20),

                // Forgot Password text link (Only on login)
                if (!_isSignUp) ...[
                  GestureDetector(
                    onTap: _openForgotPasswordScreen,
                    child: const Text(
                      'Forgot password?',
                      style: TextStyle(
                        color: Color(0xFFB8BAC0),
                        fontSize: 14,
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),
                ],

                // Action Button (Sign in / Sign up)
                SizedBox(
                  width: double.infinity,
                  height: 50,
                  child: ElevatedButton(
                    onPressed: _isLoading ? null : _handleSubmit,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFFF2F2F3),
                      foregroundColor: const Color(0xFF1F2023),
                      elevation: 0,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(25),
                      ),
                    ),
                    child: _isLoading
                        ? const SizedBox(
                            width: 22,
                            height: 22,
                            child: CircularProgressIndicator(
                              color: Color(0xFF1F2023),
                              strokeWidth: 2.5,
                            ),
                          )
                        : Text(
                            _isSignUp ? 'Sign up' : 'Sign in',
                            style: const TextStyle(
                              color: Color(0xFF1F2023),
                              fontSize: 16,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                  ),
                ),

                const SizedBox(height: 18),

                // Toggle Link
                GestureDetector(
                  onTap: () => setState(() {
                    _isSignUp = !_isSignUp;
                    _errorMessage = null;
                  }),
                  child: Text(
                    _isSignUp
                        ? 'Already have an account? Sign in'
                        : "Don't have an account? Sign up",
                    style: const TextStyle(
                      color: Color(0xFFB8BAC0),
                      fontSize: 14,
                    ),
                  ),
                ),

                const SizedBox(height: 24),

                // Terms and Policy Links
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    GestureDetector(
                      onTap: () => LegalDialogs.showTermsOfService(context),
                      child: const Text(
                        'Terms of Service',
                        style: TextStyle(
                          color: Color(0xFFB8B8B8),
                          fontSize: 12,
                          decoration: TextDecoration.underline,
                        ),
                      ),
                    ),
                    const Text(' • ',
                        style:
                            TextStyle(color: Color(0xFF888888), fontSize: 12)),
                    GestureDetector(
                      onTap: () => LegalDialogs.showPrivacyPolicy(context),
                      child: const Text(
                        'Privacy Policy',
                        style: TextStyle(
                          color: Color(0xFFB8B8B8),
                          fontSize: 12,
                          decoration: TextDecoration.underline,
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildPillInput({
    required TextEditingController controller,
    required String hint,
    bool obscureText = false,
    TextInputType? keyboardType,
    bool readOnly = false,
    VoidCallback? onTap,
    List<TextInputFormatter>? inputFormatters,
    Widget? prefixIcon,
    Widget? suffixIcon,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(25),
      child: Container(
        height: 50,
        decoration: BoxDecoration(
          color: const Color(0xFF2E3035),
          borderRadius: BorderRadius.circular(25),
          border: Border.all(
            color: const Color(0xFF6B6E76).withOpacity(0.35),
            width: 1.2,
          ),
        ),
        alignment: Alignment.center,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        child: Row(
          children: [
            if (prefixIcon != null) ...[
              prefixIcon,
              const SizedBox(width: 8),
            ] else
              const SizedBox(width: 20),
            Expanded(
              child: IgnorePointer(
                ignoring: readOnly,
                child: TextField(
                  controller: controller,
                  obscureText: obscureText,
                  keyboardType: keyboardType,
                  inputFormatters: inputFormatters,
                  readOnly: readOnly,
                  onTap: onTap,
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 15,
                    fontWeight: FontWeight.w500,
                  ),
                  cursorColor: Colors.white,
                  decoration: InputDecoration(
                    filled: false,
                    fillColor: Colors.transparent,
                    hintText: hint,
                    hintStyle: const TextStyle(
                      color: Color(0xFFB8BAC0),
                      fontSize: 14,
                      fontWeight: FontWeight.w400,
                    ),
                    border: InputBorder.none,
                    enabledBorder: InputBorder.none,
                    focusedBorder: InputBorder.none,
                    errorBorder: InputBorder.none,
                    disabledBorder: InputBorder.none,
                    focusedErrorBorder: InputBorder.none,
                    contentPadding: EdgeInsets.zero,
                    isDense: true,
                  ),
                ),
              ),
            ),
            if (suffixIcon != null) ...[
              const SizedBox(width: 8),
              suffixIcon,
            ] else
              const SizedBox(width: 20),
          ],
        ),
      ),
    );
  }
}

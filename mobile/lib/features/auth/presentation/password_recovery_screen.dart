import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_svg/flutter_svg.dart';
import '../../../core/network/api_client.dart';

/// Screen 1 of 4: Enter email to request a 6-digit recovery code (Full Screen)
class PasswordRecoveryScreen extends StatefulWidget {
  final String? initialEmail;

  const PasswordRecoveryScreen({super.key, this.initialEmail});

  @override
  State<PasswordRecoveryScreen> createState() => _PasswordRecoveryScreenState();
}

class _PasswordRecoveryScreenState extends State<PasswordRecoveryScreen> {
  final ApiClient _apiClient = ApiClient();
  late final TextEditingController _emailController;
  bool _isLoading = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _emailController = TextEditingController(text: widget.initialEmail ?? '');
  }

  @override
  void dispose() {
    _emailController.dispose();
    super.dispose();
  }

  Future<void> _handleSendCode() async {
    final email = _emailController.text.trim();
    if (email.isEmpty || !email.contains('@')) {
      setState(() => _errorMessage = 'Please enter a valid email address.');
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final res = await _apiClient.sendOTP(email);
      if (!mounted) return;

      if (res['success'] == true) {
        // Navigate to dedicated "Code Sent to Email" screen
        Navigator.of(context).push(
          MaterialPageRoute(
            builder: (_) => CodeSentToEmailScreen(email: email),
          ),
        );
      } else {
        setState(() {
          _errorMessage = res['error']?.toString() ??
              'Could not send recovery code. Please try again.';
        });
      }
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _errorMessage = 'Connection error. Check your internet connection and try again.';
      });
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF1F2023),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, color: Colors.white, size: 20),
          onPressed: () => Navigator.of(context).pop(),
          tooltip: 'Back to Sign In',
        ),
      ),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 20),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                SvgPicture.asset(
                  'assets/images/icapsq-mark-white.svg',
                  width: 64,
                  height: 72,
                  fit: BoxFit.contain,
                ),
                const SizedBox(height: 28),
                const Text(
                  'Password Recovery',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 24,
                    fontWeight: FontWeight.w800,
                    letterSpacing: -0.5,
                  ),
                ),
                const SizedBox(height: 10),
                const Text(
                  'Enter the email associated with your IcapsQ account to receive a 6-digit recovery code.',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: Color(0xFFB8BAC0),
                    fontSize: 14,
                    height: 1.45,
                  ),
                ),
                const SizedBox(height: 32),
                if (_errorMessage != null) ...[
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    decoration: BoxDecoration(
                      color: const Color(0x22FF6B6B),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: const Color(0x66FF6B6B)),
                    ),
                    child: Text(
                      _errorMessage!,
                      style: const TextStyle(
                        color: Color(0xFFFF8585),
                        fontSize: 13,
                        fontWeight: FontWeight.w500,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ),
                  const SizedBox(height: 20),
                ],
                _buildRecoveryInput(
                  controller: _emailController,
                  hint: 'Email address',
                  keyboardType: TextInputType.emailAddress,
                  prefixIcon: const Icon(Icons.mail_outline, color: Color(0xFFB8BAC0), size: 20),
                ),
                const SizedBox(height: 24),
                SizedBox(
                  width: double.infinity,
                  height: 50,
                  child: ElevatedButton(
                    onPressed: _isLoading ? null : _handleSendCode,
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
                        : const Text(
                            'Send Recovery Code',
                            style: TextStyle(
                              color: Color(0xFF1F2023),
                              fontSize: 16,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                  ),
                ),
                const SizedBox(height: 28),
                GestureDetector(
                  onTap: () => Navigator.of(context).pop(),
                  child: const Text(
                    'Remember your password? Sign in',
                    style: TextStyle(
                      color: Color(0xFFB8BAC0),
                      fontSize: 14,
                    ),
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

/// Screen 2 of 4: Dedicated "Code Sent to Email" screen (Full Screen)
class CodeSentToEmailScreen extends StatefulWidget {
  final String email;

  const CodeSentToEmailScreen({super.key, required this.email});

  @override
  State<CodeSentToEmailScreen> createState() => _CodeSentToEmailScreenState();
}

class _CodeSentToEmailScreenState extends State<CodeSentToEmailScreen> {
  final ApiClient _apiClient = ApiClient();
  bool _isResending = false;
  String? _statusNotice;
  String? _errorMessage;
  int _cooldown = 60;
  Timer? _cooldownTimer;

  @override
  void initState() {
    super.initState();
    _startCooldown();
  }

  void _startCooldown() {
    setState(() => _cooldown = 60);
    _cooldownTimer?.cancel();
    _cooldownTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_cooldown <= 1) {
        timer.cancel();
        if (mounted) setState(() => _cooldown = 0);
      } else {
        if (mounted) setState(() => _cooldown--);
      }
    });
  }

  @override
  void dispose() {
    _cooldownTimer?.cancel();
    super.dispose();
  }

  Future<void> _handleResend() async {
    if (_cooldown > 0 || _isResending) return;
    setState(() {
      _isResending = true;
      _errorMessage = null;
      _statusNotice = null;
    });

    try {
      final res = await _apiClient.sendOTP(widget.email);
      if (!mounted) return;
      if (res['success'] == true) {
        _startCooldown();
        setState(() {
          _statusNotice = 'A new 6-digit recovery code has been sent to your email.';
        });
      } else {
        setState(() {
          _errorMessage = res['error']?.toString() ?? 'Could not resend code. Please try again.';
        });
      }
    } catch (_) {
      if (!mounted) return;
      setState(() => _errorMessage = 'Could not resend code. Check your connection.');
    } finally {
      if (mounted) setState(() => _isResending = false);
    }
  }

  void _navigateToCodeInput() {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => RecoveryCodeInputScreen(email: widget.email),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF1F2023),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, color: Colors.white, size: 20),
          onPressed: () => Navigator.of(context).pop(),
          tooltip: 'Back to Email Input',
        ),
      ),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 20),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // Animated glowing mail container
                Container(
                  width: 88,
                  height: 88,
                  decoration: BoxDecoration(
                    color: const Color(0xFF2E3035),
                    shape: BoxShape.circle,
                    border: Border.all(
                      color: const Color(0xFF6B6E76).withOpacity(0.4),
                      width: 1.5,
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.white.withOpacity(0.08),
                        blurRadius: 24,
                        spreadRadius: 2,
                      ),
                    ],
                  ),
                  child: const Icon(
                    Icons.mark_email_read_outlined,
                    color: Colors.white,
                    size: 42,
                  ),
                ),
                const SizedBox(height: 24),
                // Status badge
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                  decoration: BoxDecoration(
                    color: const Color(0x224CAF50),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: const Color(0x664CAF50)),
                  ),
                  child: const Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.check_circle, color: Color(0xFF81C784), size: 14),
                      SizedBox(width: 6),
                      Text(
                        'Code Sent Successfully',
                        style: TextStyle(
                          color: Color(0xFF81C784),
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 20),
                const Text(
                  'Check Your Email',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 24,
                    fontWeight: FontWeight.w800,
                    letterSpacing: -0.5,
                  ),
                ),
                const SizedBox(height: 12),
                RichText(
                  textAlign: TextAlign.center,
                  text: TextSpan(
                    style: const TextStyle(
                      color: Color(0xFFB8BAC0),
                      fontSize: 14,
                      height: 1.5,
                    ),
                    children: [
                      const TextSpan(text: 'We have dispatched a 6-digit recovery code to\n'),
                      TextSpan(
                        text: widget.email,
                        style: const TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const TextSpan(
                        text: '\n\nPlease check your inbox and spam folder. The code expires in 10 minutes.',
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 32),
                if (_errorMessage != null) ...[
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    decoration: BoxDecoration(
                      color: const Color(0x22FF6B6B),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: const Color(0x66FF6B6B)),
                    ),
                    child: Text(
                      _errorMessage!,
                      style: const TextStyle(
                        color: Color(0xFFFF8585),
                        fontSize: 13,
                        fontWeight: FontWeight.w500,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ),
                  const SizedBox(height: 20),
                ],
                if (_statusNotice != null) ...[
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    decoration: BoxDecoration(
                      color: const Color(0x224CAF50),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: const Color(0x664CAF50)),
                    ),
                    child: Text(
                      _statusNotice!,
                      style: const TextStyle(
                        color: Color(0xFF81C784),
                        fontSize: 13,
                        fontWeight: FontWeight.w500,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ),
                  const SizedBox(height: 20),
                ],
                // Primary Action Button: Enter 6-Digit Code
                SizedBox(
                  width: double.infinity,
                  height: 50,
                  child: ElevatedButton(
                    onPressed: _navigateToCodeInput,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFFF2F2F3),
                      foregroundColor: const Color(0xFF1F2023),
                      elevation: 0,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(25),
                      ),
                    ),
                    child: const Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(
                          'Enter 6-Digit Code',
                          style: TextStyle(
                            color: Color(0xFF1F2023),
                            fontSize: 16,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        SizedBox(width: 8),
                        Icon(Icons.arrow_forward, color: Color(0xFF1F2023), size: 18),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 20),
                // Resend action
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      _cooldown > 0
                          ? 'Resend code in ${_cooldown}s'
                          : 'Did not receive the email?',
                      style: const TextStyle(
                        color: Color(0xFFB8BAC0),
                        fontSize: 13.5,
                      ),
                    ),
                    if (_cooldown == 0) ...[
                      const SizedBox(width: 6),
                      GestureDetector(
                        onTap: _isResending ? null : _handleResend,
                        child: Text(
                          _isResending ? 'Sending...' : 'Resend Code',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 13.5,
                            fontWeight: FontWeight.w700,
                            decoration: TextDecoration.underline,
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
                const SizedBox(height: 20),
                GestureDetector(
                  onTap: () => Navigator.of(context).pop(),
                  child: const Text(
                    'Wrong email address? Change email',
                    style: TextStyle(
                      color: Color(0xFF8E929B),
                      fontSize: 13,
                    ),
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

/// Screen 3 of 4: Enter the 6-digit code received via email (Full Screen)
class RecoveryCodeInputScreen extends StatefulWidget {
  final String email;

  const RecoveryCodeInputScreen({super.key, required this.email});

  @override
  State<RecoveryCodeInputScreen> createState() => _RecoveryCodeInputScreenState();
}

class _RecoveryCodeInputScreenState extends State<RecoveryCodeInputScreen> {
  final ApiClient _apiClient = ApiClient();
  final TextEditingController _codeController = TextEditingController();
  bool _isResending = false;
  String? _errorMessage;
  String? _statusNotice;
  int _resendCooldown = 60;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _startCooldown();
  }

  void _startCooldown() {
    setState(() => _resendCooldown = 60);
    _timer?.cancel();
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_resendCooldown <= 1) {
        timer.cancel();
        if (mounted) setState(() => _resendCooldown = 0);
      } else {
        if (mounted) setState(() => _resendCooldown--);
      }
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    _codeController.dispose();
    super.dispose();
  }

  Future<void> _handleResendCode() async {
    if (_resendCooldown > 0 || _isResending) return;
    setState(() {
      _isResending = true;
      _errorMessage = null;
      _statusNotice = null;
    });

    try {
      final res = await _apiClient.sendOTP(widget.email);
      if (!mounted) return;
      if (res['success'] == true) {
        _startCooldown();
        setState(() {
          _statusNotice = 'A new 6-digit recovery code has been sent to ${widget.email}.';
        });
      } else {
        setState(() {
          _errorMessage = res['error']?.toString() ?? 'Could not resend code. Please try again.';
        });
      }
    } catch (_) {
      if (!mounted) return;
      setState(() => _errorMessage = 'Could not resend code. Check your connection.');
    } finally {
      if (mounted) setState(() => _isResending = false);
    }
  }

  void _handleContinue() {
    final code = _codeController.text.trim();
    if (code.length != 6) {
      setState(() => _errorMessage = 'Please enter the complete 6-digit recovery code.');
      return;
    }

    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => SetNewPasswordScreen(
          email: widget.email,
          otp: code,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF1F2023),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, color: Colors.white, size: 20),
          onPressed: () => Navigator.of(context).pop(),
          tooltip: 'Back',
        ),
      ),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 20),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  width: 72,
                  height: 72,
                  decoration: BoxDecoration(
                    color: const Color(0xFF2E3035),
                    shape: BoxShape.circle,
                    border: Border.all(color: const Color(0xFF6B6E76).withOpacity(0.4)),
                  ),
                  child: const Icon(
                    Icons.pin_outlined,
                    color: Colors.white,
                    size: 36,
                  ),
                ),
                const SizedBox(height: 24),
                const Text(
                  'Enter 6-Digit Code',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 24,
                    fontWeight: FontWeight.w800,
                    letterSpacing: -0.5,
                  ),
                ),
                const SizedBox(height: 10),
                RichText(
                  textAlign: TextAlign.center,
                  text: TextSpan(
                    style: const TextStyle(
                      color: Color(0xFFB8BAC0),
                      fontSize: 14,
                      height: 1.45,
                    ),
                    children: [
                      const TextSpan(text: 'Type the 6-digit code sent to\n'),
                      TextSpan(
                        text: widget.email,
                        style: const TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 32),
                if (_errorMessage != null) ...[
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    decoration: BoxDecoration(
                      color: const Color(0x22FF6B6B),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: const Color(0x66FF6B6B)),
                    ),
                    child: Text(
                      _errorMessage!,
                      style: const TextStyle(
                        color: Color(0xFFFF8585),
                        fontSize: 13,
                        fontWeight: FontWeight.w500,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ),
                  const SizedBox(height: 20),
                ],
                if (_statusNotice != null) ...[
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    decoration: BoxDecoration(
                      color: const Color(0x224CAF50),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: const Color(0x664CAF50)),
                    ),
                    child: Text(
                      _statusNotice!,
                      style: const TextStyle(
                        color: Color(0xFF81C784),
                        fontSize: 13,
                        fontWeight: FontWeight.w500,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ),
                  const SizedBox(height: 20),
                ],
                // 6-digit numeric input with large styled font
                Container(
                  height: 56,
                  decoration: BoxDecoration(
                    color: const Color(0xFF2E3035),
                    borderRadius: BorderRadius.circular(28),
                    border: Border.all(
                      color: const Color(0xFF6B6E76).withOpacity(0.35),
                      width: 1.2,
                    ),
                  ),
                  padding: const EdgeInsets.symmetric(horizontal: 24),
                  alignment: Alignment.center,
                  child: TextField(
                    controller: _codeController,
                    keyboardType: TextInputType.number,
                    textAlign: TextAlign.center,
                    maxLength: 6,
                    inputFormatters: [
                      FilteringTextInputFormatter.digitsOnly,
                      LengthLimitingTextInputFormatter(6),
                    ],
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 24,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 10,
                    ),
                    cursorColor: Colors.white,
                    decoration: const InputDecoration(
                      hintText: '••••••',
                      counterText: '',
                      hintStyle: TextStyle(
                        color: Color(0xFF8E929B),
                        fontSize: 24,
                        letterSpacing: 8,
                      ),
                      border: InputBorder.none,
                      contentPadding: EdgeInsets.zero,
                      isDense: true,
                    ),
                    onChanged: (val) {
                      if (_errorMessage != null) {
                        setState(() => _errorMessage = null);
                      }
                      if (val.trim().length == 6) {
                        _handleContinue();
                      }
                    },
                  ),
                ),
                const SizedBox(height: 24),
                SizedBox(
                  width: double.infinity,
                  height: 50,
                  child: ElevatedButton(
                    onPressed: _handleContinue,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFFF2F2F3),
                      foregroundColor: const Color(0xFF1F2023),
                      elevation: 0,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(25),
                      ),
                    ),
                    child: const Text(
                      'Verify Code & Continue',
                      style: TextStyle(
                        color: Color(0xFF1F2023),
                        fontSize: 16,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 24),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      _resendCooldown > 0
                          ? 'Resend code in ${_resendCooldown}s'
                          : 'Did not receive code?',
                      style: const TextStyle(
                        color: Color(0xFFB8BAC0),
                        fontSize: 13.5,
                      ),
                    ),
                    if (_resendCooldown == 0) ...[
                      const SizedBox(width: 6),
                      GestureDetector(
                        onTap: _isResending ? null : _handleResendCode,
                        child: Text(
                          _isResending ? 'Sending...' : 'Resend Code',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 13.5,
                            fontWeight: FontWeight.w700,
                            decoration: TextDecoration.underline,
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
                const SizedBox(height: 16),
                GestureDetector(
                  onTap: () => Navigator.of(context).pop(),
                  child: const Text(
                    'Wrong email address? Change email',
                    style: TextStyle(
                      color: Color(0xFF8E929B),
                      fontSize: 13,
                    ),
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

/// Screen 4 of 4: Enter and confirm the new password (Full Screen)
class SetNewPasswordScreen extends StatefulWidget {
  final String email;
  final String otp;

  const SetNewPasswordScreen({
    super.key,
    required this.email,
    required this.otp,
  });

  @override
  State<SetNewPasswordScreen> createState() => _SetNewPasswordScreenState();
}

class _SetNewPasswordScreenState extends State<SetNewPasswordScreen> {
  final ApiClient _apiClient = ApiClient();
  final TextEditingController _newPasswordController = TextEditingController();
  final TextEditingController _confirmPasswordController = TextEditingController();
  bool _showNewPassword = false;
  bool _showConfirmPassword = false;
  bool _isLoading = false;
  String? _errorMessage;

  @override
  void dispose() {
    _newPasswordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  Future<void> _handleResetPassword() async {
    final newPass = _newPasswordController.text;
    final confirmPass = _confirmPasswordController.text;

    if (newPass.isEmpty) {
      setState(() => _errorMessage = 'Please enter a new password.');
      return;
    }
    if (newPass.length < 8) {
      setState(() => _errorMessage = 'Password must be at least 8 characters long.');
      return;
    }
    if (newPass != confirmPass) {
      setState(() => _errorMessage = 'Passwords do not match. Please re-enter.');
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final res = await _apiClient.verifyOTPAndResetPassword(
        email: widget.email,
        otp: widget.otp,
        newPassword: newPass,
      );

      if (!mounted) return;

      if (res['success'] == true) {
        // Pop all recovery screens and return to login screen with success feedback
        Navigator.of(context).popUntil((route) => route.isFirst);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              res['message']?.toString() ??
                  'Password reset successfully! Sign in with your new password.',
              style: const TextStyle(
                color: Color(0xFF1F2023),
                fontWeight: FontWeight.w700,
              ),
            ),
            backgroundColor: const Color(0xFFF2F2F3),
            duration: const Duration(seconds: 5),
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          ),
        );
      } else {
        setState(() {
          _errorMessage = res['error']?.toString() ??
              'Invalid or expired recovery code. Please request a new code.';
        });
      }
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _errorMessage = 'Could not update password. Check your connection.';
      });
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF1F2023),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, color: Colors.white, size: 20),
          onPressed: () => Navigator.of(context).pop(),
          tooltip: 'Back',
        ),
      ),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 20),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  width: 72,
                  height: 72,
                  decoration: BoxDecoration(
                    color: const Color(0xFF2E3035),
                    shape: BoxShape.circle,
                    border: Border.all(color: const Color(0xFF6B6E76).withOpacity(0.4)),
                  ),
                  child: const Icon(
                    Icons.lock_reset_outlined,
                    color: Colors.white,
                    size: 36,
                  ),
                ),
                const SizedBox(height: 24),
                const Text(
                  'Set New Password',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 24,
                    fontWeight: FontWeight.w800,
                    letterSpacing: -0.5,
                  ),
                ),
                const SizedBox(height: 10),
                RichText(
                  textAlign: TextAlign.center,
                  text: TextSpan(
                    style: const TextStyle(
                      color: Color(0xFFB8BAC0),
                      fontSize: 14,
                      height: 1.45,
                    ),
                    children: [
                      const TextSpan(text: 'Choose a strong new password for\n'),
                      TextSpan(
                        text: widget.email,
                        style: const TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 32),
                if (_errorMessage != null) ...[
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    decoration: BoxDecoration(
                      color: const Color(0x22FF6B6B),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: const Color(0x66FF6B6B)),
                    ),
                    child: Text(
                      _errorMessage!,
                      style: const TextStyle(
                        color: Color(0xFFFF8585),
                        fontSize: 13,
                        fontWeight: FontWeight.w500,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ),
                  const SizedBox(height: 20),
                ],
                _buildRecoveryInput(
                  controller: _newPasswordController,
                  hint: 'New password (min. 8 characters)',
                  obscureText: !_showNewPassword,
                  prefixIcon: const Icon(Icons.lock_outline, color: Color(0xFFB8BAC0), size: 20),
                  suffixIcon: IconButton(
                    icon: Icon(
                      _showNewPassword ? Icons.visibility_off_outlined : Icons.visibility_outlined,
                      color: const Color(0xFFB8BAC0),
                      size: 20,
                    ),
                    onPressed: () => setState(() => _showNewPassword = !_showNewPassword),
                    tooltip: _showNewPassword ? 'Hide password' : 'Show password',
                  ),
                ),
                const SizedBox(height: 16),
                _buildRecoveryInput(
                  controller: _confirmPasswordController,
                  hint: 'Confirm new password',
                  obscureText: !_showConfirmPassword,
                  prefixIcon: const Icon(Icons.lock_reset, color: Color(0xFFB8BAC0), size: 20),
                  suffixIcon: IconButton(
                    icon: Icon(
                      _showConfirmPassword ? Icons.visibility_off_outlined : Icons.visibility_outlined,
                      color: const Color(0xFFB8BAC0),
                      size: 20,
                    ),
                    onPressed: () => setState(() => _showConfirmPassword = !_showConfirmPassword),
                    tooltip: _showConfirmPassword ? 'Hide password' : 'Show password',
                  ),
                ),
                const SizedBox(height: 24),
                SizedBox(
                  width: double.infinity,
                  height: 50,
                  child: ElevatedButton(
                    onPressed: _isLoading ? null : _handleResetPassword,
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
                        : const Text(
                            'Update Password',
                            style: TextStyle(
                              color: Color(0xFF1F2023),
                              fontSize: 16,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                  ),
                ),
                const SizedBox(height: 24),
                GestureDetector(
                  onTap: () => Navigator.of(context).popUntil((route) => route.isFirst),
                  child: const Text(
                    'Cancel and back to sign in',
                    style: TextStyle(
                      color: Color(0xFF8E929B),
                      fontSize: 13,
                    ),
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

/// Helper method to build pill inputs consistent with IcapsQ mobile styling
Widget _buildRecoveryInput({
  required TextEditingController controller,
  required String hint,
  bool obscureText = false,
  TextInputType? keyboardType,
  Widget? prefixIcon,
  Widget? suffixIcon,
}) {
  return Container(
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
          child: TextField(
            controller: controller,
            obscureText: obscureText,
            keyboardType: keyboardType,
            textAlign: TextAlign.center,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 15,
              fontWeight: FontWeight.w500,
            ),
            cursorColor: Colors.white,
            decoration: InputDecoration(
              filled: false,
              hintText: hint,
              hintStyle: const TextStyle(
                color: Color(0xFFB8BAC0),
                fontSize: 14,
                fontWeight: FontWeight.w400,
              ),
              border: InputBorder.none,
              contentPadding: EdgeInsets.zero,
              isDense: true,
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
  );
}

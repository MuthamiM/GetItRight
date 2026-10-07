import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../../core/network/api_client.dart';

class PlanSelectionScreen extends StatefulWidget {
  final Map<String, dynamic> userData;
  final VoidCallback onProceed;

  const PlanSelectionScreen({
    super.key,
    required this.userData,
    required this.onProceed,
  });

  @override
  State<PlanSelectionScreen> createState() => _PlanSelectionScreenState();
}

class _PlanSelectionScreenState extends State<PlanSelectionScreen> {
  final ApiClient _apiClient = ApiClient();
  final PageController _pageController = PageController(viewportFraction: 0.86);
  late String _selectedPlan;
  int _currentPage = 0;
  bool _isSaving = false;

  static const _plans = <Map<String, dynamic>>[
    {
      'id': 'free',
      'name': 'Starter',
      'tier': 'FREE TIER',
      'price': 'Free',
      'period': 'No card required',
      'icon': Icons.bolt,
      'features': [
        'Up to 5 active polls',
        '1,000 responses per poll',
        'Basic results dashboard',
        'Share via public link',
      ],
    },
    {
      'id': 'pro',
      'name': 'Pro',
      'tier': 'PROFESSIONAL',
      'price': '499 KES',
      'period': 'per month',
      'icon': Icons.verified,
      'features': [
        'Up to 50 active polls',
        '25,000 responses per poll',
        'Real-time analytics & exports',
        'Custom branding & CSV export',
      ],
    },
    {
      'id': 'org',
      'name': 'Organization',
      'tier': 'ENTERPRISE',
      'price': '899 KES',
      'period': 'per month',
      'icon': Icons.business,
      'features': [
        'Up to 200 active polls',
        '100,000 responses per poll',
        'Multi-admin team access',
        'Audit trail & compliance',
      ],
    },
    {
      'id': 'election',
      'name': 'Election',
      'tier': 'GOVERNANCE',
      'price': '1,399 KES',
      'period': 'per month',
      'icon': Icons.security,
      'features': [
        'Unlimited polls & surveys',
        '10M+ voter capacity',
        'Voter verification & ID checks',
        'Full audit & observer access',
      ],
    },
  ];

  final TextEditingController _phoneController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _selectedPlan =
        (widget.userData['plan'] as String? ?? 'free').toLowerCase();
    _phoneController.text =
        widget.userData['phone']?.toString() ?? '';
    final initialIndex = _plans.indexWhere((p) => p['id'] == _selectedPlan);
    if (initialIndex != -1) {
      _currentPage = initialIndex;
    } else {
      _selectedPlan = 'free';
      _currentPage = 0;
    }
  }

  @override
  void dispose() {
    _pageController.dispose();
    _phoneController.dispose();
    super.dispose();
  }

  Future<void> _handleConfirm() async {
    setState(() => _isSaving = true);
    final userId = widget.userData['id']?.toString() ?? 'USR-001';
    final phone = _phoneController.text.trim();

    await _apiClient.updatePlan(userId, _selectedPlan);

    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('gir_user_plan', _selectedPlan);
    await prefs.setString('gir_user_id', userId);
    await prefs.setString('gir_user_phone', phone);
    await prefs.setString('gir_user_name',
        widget.userData['fullName']?.toString() ?? 'User');

    if (mounted) {
      setState(() => _isSaving = false);
      widget.onProceed();
    }
  }

  void _scrollToNextPlan() {
    if (_currentPage < _plans.length - 1) {
      _pageController.animateToPage(
        _currentPage + 1,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
    } else {
      _pageController.animateToPage(
        0,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final userName = widget.userData['fullName'] ?? 'there';

    return Scaffold(
      backgroundColor: const Color(0xFF303030),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: const Text(
          'Choose Plan',
          style: TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.w700,
            fontSize: 18,
          ),
        ),
        centerTitle: true,
      ),
      body: SafeArea(
        child: Column(
          children: [
            // Header
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
              child: Column(
                children: [
                  Text(
                    'Welcome, $userName',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 18,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Swipe horizontally to browse plans. Enter phone number to link your account.',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: Colors.white.withAlpha(140),
                      fontSize: 13,
                    ),
                  ),
                  const SizedBox(height: 12),
                  // Phone Number Input Section
                  Container(
                    decoration: BoxDecoration(
                      color: const Color(0xFF404040),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: const Color(0xFF606060)),
                    ),
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 2),
                    child: TextField(
                      controller: _phoneController,
                      keyboardType: TextInputType.phone,
                      style: const TextStyle(color: Colors.white, fontSize: 14),
                      decoration: const InputDecoration(
                        icon: Icon(Icons.phone_android, color: Colors.white70, size: 20),
                        hintText: 'Enter Phone Number (+254...)',
                        hintStyle: TextStyle(color: Colors.white38, fontSize: 13),
                        border: InputBorder.none,
                      ),
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 16),

            // Horizontal Scrolling PageView for Plan Cards
            Expanded(
              child: PageView.builder(
                controller: _pageController,
                itemCount: _plans.length,
                onPageChanged: (index) {
                  setState(() {
                    _currentPage = index;
                    _selectedPlan = _plans[index]['id'] as String;
                  });
                },
                itemBuilder: (context, index) {
                  final plan = _plans[index];
                  final isSelected = plan['id'] == _selectedPlan;

                  return AnimatedContainer(
                    duration: const Duration(milliseconds: 200),
                    margin: const EdgeInsets.symmetric(
                        horizontal: 8, vertical: 12),
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      color: isSelected
                          ? const Color(0xFF505050)
                          : const Color(0xFF404040),
                      borderRadius: BorderRadius.circular(24),
                      border: Border.all(
                        color: isSelected ? Colors.white : const Color(0xFF606060),
                        width: isSelected ? 2.0 : 1.0,
                      ),
                      boxShadow: isSelected
                          ? [
                              BoxShadow(
                                color: Colors.black.withAlpha(50),
                                blurRadius: 16,
                                offset: const Offset(0, 6),
                              )
                            ]
                          : [],
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Card Header Row
                        Row(
                          children: [
                            Container(
                              width: 42,
                              height: 42,
                              decoration: BoxDecoration(
                                color: Colors.white.withAlpha(30),
                                shape: BoxShape.circle,
                              ),
                              child: Icon(plan['icon'] as IconData,
                                  color: Colors.white, size: 22),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    plan['name'] as String,
                                    style: const TextStyle(
                                      color: Colors.white,
                                      fontSize: 18,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                  Text(
                                    plan['tier'] as String,
                                    style: const TextStyle(
                                      color: Color(0xFFD0D0D0),
                                      fontSize: 11,
                                      fontWeight: FontWeight.w700,
                                      letterSpacing: 1.0,
                                    ),
                                  ),
                                ],
                              ),
                            ),

                            // Selection Radio
                            GestureDetector(
                              onTap: () {
                                setState(
                                    () => _selectedPlan = plan['id'] as String);
                              },
                              child: Container(
                                width: 24,
                                height: 24,
                                decoration: BoxDecoration(
                                  shape: BoxShape.circle,
                                  border: Border.all(
                                    color: isSelected
                                        ? Colors.white
                                        : const Color(0xFF888888),
                                    width: 2,
                                  ),
                                  color: isSelected
                                      ? Colors.white
                                      : Colors.transparent,
                                ),
                                child: isSelected
                                    ? const Icon(Icons.check,
                                        size: 16, color: Color(0xFF303030))
                                    : null,
                              ),
                            ),
                          ],
                        ),

                        const SizedBox(height: 18),

                        // Price Row
                        Row(
                          crossAxisAlignment: CrossAxisAlignment.baseline,
                          textBaseline: TextBaseline.alphabetic,
                          children: [
                            Text(
                              plan['price'] as String,
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 24,
                                fontWeight: FontWeight.w900,
                              ),
                            ),
                            const SizedBox(width: 8),
                            Text(
                              plan['period'] as String,
                              style: const TextStyle(
                                color: Color(0xFFB0B0B0),
                                fontSize: 13,
                              ),
                            ),
                          ],
                        ),

                        const Divider(
                          color: Color(0xFF606060),
                          height: 28,
                        ),

                        // Features List
                        Expanded(
                          child: ListView(
                            physics: const NeverScrollableScrollPhysics(),
                            children: (plan['features'] as List<String>)
                                .map((feat) => Padding(
                                      padding:
                                          const EdgeInsets.only(bottom: 10),
                                      child: Row(
                                        children: [
                                          const Icon(Icons.check,
                                              size: 16, color: Colors.white),
                                          const SizedBox(width: 10),
                                          Expanded(
                                            child: Text(
                                              feat,
                                              style: const TextStyle(
                                                color: Color(0xFFE0E0E0),
                                                fontSize: 13,
                                              ),
                                            ),
                                          ),
                                        ],
                                      ),
                                    ))
                                .toList(),
                          ),
                        ),
                      ],
                    ),
                  );
                },
              ),
            ),

            const SizedBox(height: 8),

            // Indicator Dots & "View More Plans" Button
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: List.generate(_plans.length, (index) {
                final isCurrent = index == _currentPage;
                return AnimatedContainer(
                  duration: const Duration(milliseconds: 200),
                  margin: const EdgeInsets.symmetric(horizontal: 4),
                  width: isCurrent ? 20 : 8,
                  height: 8,
                  decoration: BoxDecoration(
                    color: isCurrent ? Colors.white : const Color(0xFF606060),
                    borderRadius: BorderRadius.circular(4),
                  ),
                );
              }),
            ),

            const SizedBox(height: 10),

            // View More Plans Toggle Button
            TextButton.icon(
              onPressed: _scrollToNextPlan,
              icon: const Icon(Icons.swipe_right,
                  color: Color(0xFFD0D0D0), size: 18),
              label: const Text(
                'View More Plans',
                style: TextStyle(
                  color: Color(0xFFD0D0D0),
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),

            const SizedBox(height: 8),

            // Action Button
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 4, 24, 20),
              child: SizedBox(
                width: double.infinity,
                height: 52,
                child: ElevatedButton(
                  onPressed: _isSaving ? null : _handleConfirm,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFFE5E5E5),
                    foregroundColor: const Color(0xFF2A2A2A),
                    elevation: 0,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(26),
                    ),
                  ),
                  child: _isSaving
                      ? const SizedBox(
                          width: 22,
                          height: 22,
                          child: CircularProgressIndicator(
                            color: Color(0xFF2A2A2A),
                            strokeWidth: 2.5,
                          ),
                        )
                      : Text(
                          'Proceed with ${_plans[_currentPage]['name']}',
                          style: const TextStyle(
                            color: Color(0xFF2A2A2A),
                            fontSize: 16,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

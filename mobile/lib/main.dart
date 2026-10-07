import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'core/theme/app_theme.dart';
import 'features/auth/presentation/login_screen.dart';
import 'features/auth/presentation/plan_selection_screen.dart';
import 'features/polls/presentation/polls_feed_screen.dart';
import 'features/surveys/presentation/surveys_feed_screen.dart';
import 'features/dashboard/presentation/org_dashboard_screen.dart';
import 'features/profile/presentation/profile_settings_screen.dart';
import 'features/splash/presentation/splash_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const GetitrightApp());
}

class GetitrightApp extends StatelessWidget {
  const GetitrightApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Getitright',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.darkTheme,
      home: const SplashScreen(),
    );
  }
}

class RootNavigationCoordinator extends StatefulWidget {
  const RootNavigationCoordinator({super.key});

  @override
  State<RootNavigationCoordinator> createState() =>
      _RootNavigationCoordinatorState();
}

class _RootNavigationCoordinatorState
    extends State<RootNavigationCoordinator> {
  bool _isLoggedIn = false;
  String _userRole = 'user';
  int _currentIndex = 0;
  String _userName = 'User';
  String _currentPlan = 'free';

  @override
  void initState() {
    super.initState();
    _checkSavedSession();
  }

  Future<void> _checkSavedSession() async {
    final prefs = await SharedPreferences.getInstance();
    final userId = prefs.getString('gir_user_id');
    final role = prefs.getString('gir_user_role') ?? 'user';
    final plan = prefs.getString('gir_user_plan') ?? 'free';
    final name = prefs.getString('gir_user_name') ?? 'User';

    if (userId != null && userId.isNotEmpty) {
      if (mounted) {
        setState(() {
          _isLoggedIn = true;
          _userRole = role;
          _currentPlan = plan;
          _userName = name;
          _currentIndex = (role == 'admin' || role == 'org') ? 2 : 0;
        });
        _requestNotificationPermissionIfNeeded();
      }
    }
  }

  Future<void> _requestNotificationPermissionIfNeeded() async {
    final prefs = await SharedPreferences.getInstance();
    final alreadyAsked = prefs.getBool('gir_notification_asked') ?? false;

    if (!alreadyAsked && mounted) {
      await prefs.setBool('gir_notification_asked', true);
      showDialog(
        context: context,
        builder: (context) => AlertDialog(
          backgroundColor: const Color(0xFF424242),
          shape:
              RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
          title: const Text(
            'Allow Notifications?',
            style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
          ),
          content: const Text(
            'Getitright would like to send you notifications for live poll results and survey updates.',
            style: TextStyle(color: Color(0xFFD0D0D0), fontSize: 13),
          ),
          actions: [
            TextButton(
              onPressed: () {
                prefs.setBool('gir_notifications_enabled', false);
                Navigator.of(context).pop();
              },
              child: const Text('Don\'t Allow',
                  style: TextStyle(color: Color(0xFFB8B8B8))),
            ),
            ElevatedButton(
              onPressed: () {
                prefs.setBool('gir_notifications_enabled', true);
                Navigator.of(context).pop();
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFFE5E5E5),
                foregroundColor: const Color(0xFF2A2A2A),
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16)),
              ),
              child: const Text('Allow',
                  style: TextStyle(fontWeight: FontWeight.bold)),
            ),
          ],
        ),
      );
    }
  }

  void _onLogin(String role) async {
    final prefs = await SharedPreferences.getInstance();
    final plan = prefs.getString('gir_user_plan') ?? 'free';
    final name = prefs.getString('gir_user_name') ?? 'User';

    setState(() {
      _isLoggedIn = true;
      _userRole = role;
      _currentPlan = plan;
      _userName = name;
      _currentIndex = (role == 'admin' || role == 'org') ? 2 : 0;
    });

    _requestNotificationPermissionIfNeeded();
  }

  void _refreshState() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _userName = prefs.getString('gir_user_name') ?? 'User';
      _currentPlan = prefs.getString('gir_user_plan') ?? 'free';
    });
  }

  void _logout() async {
    final prefs = await SharedPreferences.getInstance();
    // Do NOT wipe SharedPreferences (which clears completed surveys and plan selection).
    // Just clear active user session state.
    await prefs.remove('gir_user_id');
    if (mounted) {
      setState(() {
        _isLoggedIn = false;
        _currentIndex = 0;
      });
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
            'fullName': _userName,
            'plan': _currentPlan,
          },
          onProceed: () async {
            Navigator.of(context).pop();
            _refreshState();
          },
        ),
      ),
    );
  }

  String _getGreeting() {
    final hour = DateTime.now().hour;
    if (hour < 12) return 'Good Morning';
    if (hour < 17) return 'Good Afternoon';
    return 'Good Evening';
  }

  @override
  Widget build(BuildContext context) {
    if (!_isLoggedIn) {
      return LoginScreen(onLoginSuccess: _onLogin);
    }

    final bool isOrgAdmin = (_userRole == 'admin' || _userRole == 'org');

    final List<Widget> screens = isOrgAdmin
        ? [
            const PollsFeedScreen(),
            const SurveysFeedScreen(),
            const OrgDashboardScreen(),
            ProfileSettingsScreen(onSettingsUpdated: _refreshState),
          ]
        : [
            const PollsFeedScreen(),
            const SurveysFeedScreen(),
            ProfileSettingsScreen(onSettingsUpdated: _refreshState),
          ];

    final int safeIndex = _currentIndex < screens.length ? _currentIndex : 0;

    return Scaffold(
      appBar: AppBar(
        backgroundColor: const Color(0xFF303030),
        centerTitle: false,
        titleSpacing: 16,
        elevation: 0,
        title: safeIndex == 0
            ? Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '${_getGreeting()}, $_userName!',
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 0.3,
                      color: Colors.white,
                    ),
                  ),
                  const Text(
                    'Welcome back',
                    style: TextStyle(
                      fontSize: 11,
                      color: Color(0xFFB8B8B8),
                    ),
                  ),
                ],
              )
            : Text(
                safeIndex == 1
                    ? 'Surveys'
                    : (isOrgAdmin && safeIndex == 2
                        ? 'Organization Console'
                        : 'Profile & Settings'),
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
        actions: [
          PopupMenuButton<String>(
            icon: const Icon(Icons.more_vert, color: Colors.white70),
            color: const Color(0xFF424242),
            onSelected: (val) {
              if (val == 'settings') {
                setState(() => _currentIndex = isOrgAdmin ? 3 : 2);
              }
              if (val == 'plan') _openPlanSelection();
              if (val == 'logout') _logout();
            },
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: 'settings',
                child: Row(
                  children: [
                    Icon(Icons.settings, color: Colors.white, size: 18),
                    SizedBox(width: 10),
                    Text('Settings & Profile',
                        style: TextStyle(fontSize: 13, color: Colors.white)),
                  ],
                ),
              ),
              const PopupMenuItem(
                value: 'plan',
                child: Row(
                  children: [
                    Icon(Icons.workspace_premium,
                        color: Colors.white, size: 18),
                    SizedBox(width: 10),
                    Text('Change Plan',
                        style: TextStyle(fontSize: 13, color: Colors.white)),
                  ],
                ),
              ),
              const PopupMenuItem(
                value: 'logout',
                child: Row(
                  children: [
                    Icon(Icons.logout, color: Color(0xFFFF6B6B), size: 18),
                    SizedBox(width: 10),
                    Text('Sign Out',
                        style:
                            TextStyle(color: Color(0xFFFF6B6B), fontSize: 13)),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
      body: IndexedStack(
        index: safeIndex,
        children: screens,
      ),
      bottomNavigationBar: Container(
        decoration: const BoxDecoration(
          color: Color(0xFF303030),
          border: Border(top: BorderSide(color: Color(0xFF555555), width: 1)),
        ),
        child: BottomNavigationBar(
          currentIndex: safeIndex,
          backgroundColor: const Color(0xFF303030),
          selectedItemColor: Colors.white,
          unselectedItemColor: const Color(0xFF888888),
          selectedLabelStyle:
              const TextStyle(fontWeight: FontWeight.bold, fontSize: 11),
          unselectedLabelStyle: const TextStyle(fontSize: 11),
          type: BottomNavigationBarType.fixed,
          onTap: (index) => setState(() => _currentIndex = index),
          items: isOrgAdmin
              ? const [
                  BottomNavigationBarItem(
                    icon: Icon(Icons.bar_chart_outlined),
                    activeIcon: Icon(Icons.bar_chart, color: Colors.white),
                    label: 'Polls',
                  ),
                  BottomNavigationBarItem(
                    icon: Icon(Icons.assignment_outlined),
                    activeIcon: Icon(Icons.assignment, color: Colors.white),
                    label: 'Surveys',
                  ),
                  BottomNavigationBarItem(
                    icon: Icon(Icons.dashboard_outlined),
                    activeIcon: Icon(Icons.dashboard, color: Colors.white),
                    label: 'Console',
                  ),
                  BottomNavigationBarItem(
                    icon: Icon(Icons.settings_outlined),
                    activeIcon: Icon(Icons.settings, color: Colors.white),
                    label: 'Settings',
                  ),
                ]
              : const [
                  BottomNavigationBarItem(
                    icon: Icon(Icons.bar_chart_outlined),
                    activeIcon: Icon(Icons.bar_chart, color: Colors.white),
                    label: 'Polls',
                  ),
                  BottomNavigationBarItem(
                    icon: Icon(Icons.assignment_outlined),
                    activeIcon: Icon(Icons.assignment, color: Colors.white),
                    label: 'Surveys',
                  ),
                  BottomNavigationBarItem(
                    icon: Icon(Icons.settings_outlined),
                    activeIcon: Icon(Icons.settings, color: Colors.white),
                    label: 'Settings',
                  ),
                ],
        ),
      ),
    );
  }
}

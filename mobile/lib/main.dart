import 'package:flutter/material.dart';
import 'core/theme/app_theme.dart';
import 'features/auth/presentation/login_screen.dart';
import 'features/polls/presentation/polls_feed_screen.dart';
import 'features/dashboard/presentation/org_dashboard_screen.dart';

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
      home: const RootNavigationCoordinator(),
    );
  }
}

class RootNavigationCoordinator extends StatefulWidget {
  const RootNavigationCoordinator({super.key});

  @override
  State<RootNavigationCoordinator> createState() => _RootNavigationCoordinatorState();
}

class _RootNavigationCoordinatorState extends State<RootNavigationCoordinator> {
  bool _isLoggedIn = true;
  String _userRole = 'user'; // 'org' or 'user'
  int _currentIndex = 0;

  void _onLogin(String role) {
    setState(() {
      _isLoggedIn = true;
      _userRole = role;
      _currentIndex = role == 'org' ? 1 : 0;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (!_isLoggedIn) {
      return LoginScreen(onLoginSuccess: _onLogin);
    }

    final List<Widget> screens = [
      const PollsFeedScreen(),
      const OrgDashboardScreen(),
    ];

    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: screens,
      ),
      bottomNavigationBar: Container(
        decoration: const BoxDecoration(
          color: AppColors.bgCard,
          border: Border(top: BorderSide(color: AppColors.border, width: 1)),
        ),
        child: BottomNavigationBar(
          currentIndex: _currentIndex,
          backgroundColor: AppColors.bgCard,
          selectedItemColor: AppColors.accent,
          unselectedItemColor: AppColors.textSecondary,
          selectedLabelStyle: const TextStyle(fontWeight: FontWeight.w600, fontSize: 12),
          unselectedLabelStyle: const TextStyle(fontSize: 12),
          type: BottomNavigationBarType.fixed,
          onTap: (index) => setState(() => _currentIndex = index),
          items: const [
            BottomNavigationBarItem(
              icon: Icon(Icons.bar_chart),
              activeIcon: Icon(Icons.bar_chart, color: AppColors.accent),
              label: 'Live Polls',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.dashboard_outlined),
              activeIcon: Icon(Icons.dashboard, color: AppColors.accent),
              label: 'Org Console',
            ),
          ],
        ),
      ),
    );
  }
}

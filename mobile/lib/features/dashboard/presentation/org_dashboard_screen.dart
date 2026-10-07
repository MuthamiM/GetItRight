import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../../core/models/poll_model.dart';
import '../../../core/models/survey_model.dart';
import '../../../core/network/api_client.dart';

class OrgDashboardScreen extends StatefulWidget {
  const OrgDashboardScreen({super.key});

  @override
  State<OrgDashboardScreen> createState() => _OrgDashboardScreenState();
}

class _OrgDashboardScreenState extends State<OrgDashboardScreen> {
  final ApiClient _apiClient = ApiClient();
  String _userName = 'Admin';
  String _userPlan = 'pro';
  String _orgName = 'Organization';
  List<Poll> _polls = [];
  List<Survey> _surveys = [];
  bool _isLoading = true;

  String _shareTargetType = 'poll';
  String _selectedItemId = '';

  @override
  void initState() {
    super.initState();
    _loadOrgData();
  }

  Future<void> _loadOrgData() async {
    final prefs = await SharedPreferences.getInstance();
    _userName = prefs.getString('gir_user_name') ?? 'Admin';
    _userPlan = prefs.getString('gir_user_plan') ?? 'pro';
    _orgName = prefs.getString('gir_user_org') ?? 'Organization';

    final allPolls = await _apiClient.fetchPolls();
    final allSurveys = await _apiClient.fetchSurveys();

    // Filter polls to only those that are actually visible in the feeds
    // (same logic as polls_feed_screen: hide polls whose 24h countdown + 5h grace expired)
    final now = DateTime.now();
    final activePolls = <Poll>[];
    for (var p in allPolls) {
      final deadline = p.createdAt.add(const Duration(hours: 24));
      if (now.isAfter(deadline.add(const Duration(hours: 5)))) {
        continue; // This poll is expired and no longer visible to voters
      }
      activePolls.add(p);
    }

    // Filter surveys to only those not already completed by this admin
    final activeSurveys = allSurveys.where((s) {
      final completedTimeStr = prefs.getString('gir_survey_completed_time_${s.id}');
      return completedTimeStr == null;
    }).toList();

    if (mounted) {
      setState(() {
        _polls = activePolls;
        _surveys = activeSurveys;
        if (_polls.isNotEmpty) _selectedItemId = _polls.first.id;
        _isLoading = false;
      });
    }
  }

  void _generateAndCopyUniqueLink() {
    if (_selectedItemId.isEmpty) return;

    final link = _apiClient.generateShareLink(
      type: _shareTargetType,
      id: _selectedItemId,
      userId: 'public',
    );

    Clipboard.setData(ClipboardData(text: link));

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text(
          'Share link copied to clipboard',
          style: TextStyle(color: Color(0xFF2A2A2A), fontWeight: FontWeight.bold),
        ),
        backgroundColor: Color(0xFFE5E5E5),
        duration: Duration(seconds: 2),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final totalVotes = _polls.fold<int>(0, (sum, p) => sum + p.totalVotes);

    return Scaffold(
      backgroundColor: const Color(0xFF303030),
      body: SafeArea(
        child: _isLoading
            ? const Center(child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
            : SingleChildScrollView(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Header Banner Card
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(20),
                      decoration: BoxDecoration(
                        color: const Color(0xFF424242),
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: const Color(0xFF555555)),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            _orgName,
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            'Administrator: $_userName • Plan: ${_userPlan.toUpperCase()}',
                            style: const TextStyle(
                              color: Color(0xFFB8B8B8),
                              fontSize: 12,
                            ),
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 20),

                    // Metrics Row
                    Row(
                      children: [
                        _buildMetricCard('Total Polls', '${_polls.length}', Icons.bar_chart),
                        const SizedBox(width: 12),
                        _buildMetricCard('Surveys', '${_surveys.length}', Icons.assignment),
                        const SizedBox(width: 12),
                        _buildMetricCard('Votes', '$totalVotes', Icons.how_to_vote),
                      ],
                    ),

                    const SizedBox(height: 24),

                    // Share Link Generator
                    const Text(
                      'SHARE PUBLIC LINK',
                      style: TextStyle(
                        color: Color(0xFFB8B8B8),
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 1.0,
                      ),
                    ),
                    const SizedBox(height: 10),

                    Container(
                      padding: const EdgeInsets.all(18),
                      decoration: BoxDecoration(
                        color: const Color(0xFF424242),
                        borderRadius: BorderRadius.circular(18),
                        border: Border.all(color: const Color(0xFF555555)),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          // Type Selector Toggle
                          Row(
                            children: [
                              Expanded(
                                child: GestureDetector(
                                  onTap: () => setState(() {
                                    _shareTargetType = 'poll';
                                    if (_polls.isNotEmpty) _selectedItemId = _polls.first.id;
                                  }),
                                  child: Container(
                                    padding: const EdgeInsets.symmetric(vertical: 10),
                                    decoration: BoxDecoration(
                                      color: _shareTargetType == 'poll' ? const Color(0xFFE5E5E5) : const Color(0xFF505050),
                                      borderRadius: BorderRadius.circular(12),
                                    ),
                                    child: Center(
                                      child: Text(
                                        'Poll',
                                        style: TextStyle(
                                          color: _shareTargetType == 'poll' ? const Color(0xFF2A2A2A) : Colors.white,
                                          fontWeight: FontWeight.bold,
                                          fontSize: 13,
                                        ),
                                      ),
                                    ),
                                  ),
                                ),
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: GestureDetector(
                                  onTap: () => setState(() {
                                    _shareTargetType = 'survey';
                                    if (_surveys.isNotEmpty) _selectedItemId = _surveys.first.id;
                                  }),
                                  child: Container(
                                    padding: const EdgeInsets.symmetric(vertical: 10),
                                    decoration: BoxDecoration(
                                      color: _shareTargetType == 'survey' ? const Color(0xFFE5E5E5) : const Color(0xFF505050),
                                      borderRadius: BorderRadius.circular(12),
                                    ),
                                    child: Center(
                                      child: Text(
                                        'Survey',
                                        style: TextStyle(
                                          color: _shareTargetType == 'survey' ? const Color(0xFF2A2A2A) : Colors.white,
                                          fontWeight: FontWeight.bold,
                                          fontSize: 13,
                                        ),
                                      ),
                                    ),
                                  ),
                                ),
                              ),
                            ],
                          ),

                          const SizedBox(height: 16),

                          // Dropdown Item Selection
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 16),
                            decoration: BoxDecoration(
                              color: const Color(0xFF505050),
                              borderRadius: BorderRadius.circular(14),
                            ),
                            child: DropdownButtonHideUnderline(
                              child: DropdownButton<String>(
                                value: _selectedItemId.isNotEmpty ? _selectedItemId : null,
                                dropdownColor: const Color(0xFF505050),
                                isExpanded: true,
                                icon: const Icon(Icons.arrow_drop_down, color: Colors.white),
                                items: _shareTargetType == 'poll'
                                    ? _polls.map((p) {
                                        return DropdownMenuItem(
                                          value: p.id,
                                          child: Text(p.title, style: const TextStyle(color: Colors.white, fontSize: 13)),
                                        );
                                      }).toList()
                                    : _surveys.map((s) {
                                        return DropdownMenuItem(
                                          value: s.id,
                                          child: Text(s.title, style: const TextStyle(color: Colors.white, fontSize: 13)),
                                        );
                                      }).toList(),
                                onChanged: (val) {
                                  if (val != null) setState(() => _selectedItemId = val);
                                },
                              ),
                            ),
                          ),

                          const SizedBox(height: 16),

                          SizedBox(
                            width: double.infinity,
                            height: 48,
                            child: ElevatedButton(
                              onPressed: _generateAndCopyUniqueLink,
                              style: ElevatedButton.styleFrom(
                                backgroundColor: const Color(0xFFE5E5E5),
                                foregroundColor: const Color(0xFF2A2A2A),
                                elevation: 0,
                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
                              ),
                              child: const Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Icon(Icons.copy, size: 18),
                                  SizedBox(width: 8),
                                  Text('Copy Unique Share Link', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                                ],
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
      ),
    );
  }

  Widget _buildMetricCard(String label, String value, IconData icon) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: const Color(0xFF424242),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: const Color(0xFF555555)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, color: Colors.white, size: 20),
            const SizedBox(height: 10),
            Text(
              value,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              label,
              style: const TextStyle(
                color: Color(0xFFB8B8B8),
                fontSize: 11,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

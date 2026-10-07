import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../../core/models/survey_model.dart';
import '../../../core/network/api_client.dart';
import 'survey_detail_screen.dart';

class SurveysFeedScreen extends StatefulWidget {
  const SurveysFeedScreen({super.key});

  @override
  State<SurveysFeedScreen> createState() => SurveysFeedScreenState();
}

class SurveysFeedScreenState extends State<SurveysFeedScreen> {
  final ApiClient _apiClient = ApiClient();
  final ScrollController scrollController = ScrollController();
  List<Survey> _surveys = [];
  bool _isLoading = true;
  bool _showBackToTop = false;
  String _selectedFilter = 'ALL';
  final List<String> _surveyFilters = [
    'ALL',
    'MOST POPULAR',
    'ENDING SOON',
  ];
  String _userId = 'USR-001';
  String _userRole = 'user';

  @override
  void initState() {
    super.initState();
    scrollController.addListener(() {
      final show = scrollController.hasClients && scrollController.offset > 150;
      if (show != _showBackToTop && mounted) {
        setState(() => _showBackToTop = show);
      }
    });
    _loadUserAndSurveys();
  }

  @override
  void dispose() {
    scrollController.dispose();
    super.dispose();
  }

  void scrollToTop() {
    if (scrollController.hasClients) {
      if (scrollController.offset > 10) {
        scrollController.animateTo(
          0,
          duration: const Duration(milliseconds: 350),
          curve: Curves.easeOutCubic,
        );
      } else {
        ScaffoldMessenger.of(context).hideCurrentSnackBar();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text(
              'Already at top',
              style: TextStyle(
                color: Color(0xFF2A2A2A),
                fontWeight: FontWeight.bold,
              ),
            ),
            backgroundColor: Color(0xFFE5E5E5),
            duration: Duration(seconds: 1),
          ),
        );
      }
    }
  }

  Future<void> scrollToTopAndRefresh() async {
    scrollToTop();
    await _loadSurveys();
  }

  Future<void> _loadUserAndSurveys() async {
    final prefs = await SharedPreferences.getInstance();
    _userId = prefs.getString('gir_user_id') ?? 'USR-001';
    _userRole = prefs.getString('gir_user_role') ?? 'user';
    await _loadSurveys();
  }

  Future<void> _loadSurveys() async {
    setState(() => _isLoading = true);
    final surveys = await _apiClient.fetchSurveys();
    final prefs = await SharedPreferences.getInstance();

    final activeSurveys = surveys.where((s) {
      final completedTimeStr = prefs.getString('gir_survey_completed_time_${s.id}');
      // Disappear immediately once survey is completed
      if (completedTimeStr != null) {
        return false;
      }
      return true;
    }).toList();

    if (mounted) {
      setState(() {
        _surveys = activeSurveys.isNotEmpty ? activeSurveys : surveys;
        _isLoading = false;
      });
    }
  }

  void _shareSurvey(Survey survey) {
    final shareUrl = _apiClient.generateShareLink(type: 'survey', id: survey.id, userId: _userId);
    Clipboard.setData(ClipboardData(text: shareUrl));
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text(
          'Survey link copied to clipboard',
          style: TextStyle(color: Color(0xFF2A2A2A), fontWeight: FontWeight.bold),
        ),
        backgroundColor: Color(0xFFE5E5E5),
        duration: Duration(seconds: 2),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final List<Survey> filteredSurveys = List.from(_surveys);
    if (_selectedFilter == 'RECENTLY ADDED') {
      filteredSurveys.sort((a, b) => b.createdAt.compareTo(a.createdAt));
    } else if (_selectedFilter == 'MOST POPULAR') {
      filteredSurveys.sort((a, b) => b.totalResponses.compareTo(a.totalResponses));
    } else if (_selectedFilter == 'ENDING SOON') {
      filteredSurveys.sort((a, b) => a.totalResponses.compareTo(b.totalResponses));
    }

    return Scaffold(
      backgroundColor: const Color(0xFF303030),
      body: SafeArea(
        child: Column(
          children: [
            // Status & Order Dropdown Filter
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Row(
                children: [
                  const Icon(Icons.filter_list, color: Color(0xFFB8B8B8), size: 18),
                  const SizedBox(width: 8),
                  const Text(
                    'Filter Status:',
                    style: TextStyle(
                      color: Color(0xFFB8B8B8),
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Container(
                    height: 38,
                    padding: const EdgeInsets.symmetric(horizontal: 14),
                    decoration: BoxDecoration(
                      color: const Color(0xFF505050),
                      borderRadius: BorderRadius.circular(19),
                      border: Border.all(color: const Color(0xFF666666)),
                    ),
                    child: DropdownButtonHideUnderline(
                      child: DropdownButton<String>(
                        value: _selectedFilter,
                        dropdownColor: const Color(0xFF424242),
                        icon: const Icon(Icons.arrow_drop_down, color: Colors.white),
                        style: const TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                          fontSize: 13,
                        ),
                        items: _surveyFilters.map((filter) {
                          return DropdownMenuItem<String>(
                            value: filter,
                            child: Text(
                              filter,
                              style: const TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.bold,
                                fontSize: 13,
                              ),
                            ),
                          );
                        }).toList(),
                        onChanged: (newVal) {
                          if (newVal != null) {
                            setState(() => _selectedFilter = newVal);
                          }
                        },
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 8),

            // Survey List
            Expanded(
              child: _isLoading
                  ? const Center(
                      child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                    )
                  : RefreshIndicator(
                      color: const Color(0xFF303030),
                      backgroundColor: const Color(0xFFE5E5E5),
                      onRefresh: _loadSurveys,
                      child: filteredSurveys.isEmpty
                          ? ListView(
                              physics: const AlwaysScrollableScrollPhysics(),
                              children: const [
                                SizedBox(height: 120),
                                Center(
                                  child: Text('No surveys available', style: TextStyle(color: Color(0xFFB8B8B8))),
                                ),
                              ],
                            )
                          : ListView.builder(
                              controller: scrollController,
                              physics: const AlwaysScrollableScrollPhysics(),
                              padding: const EdgeInsets.all(16),
                              itemCount: filteredSurveys.length,
                              itemBuilder: (context, index) {
                            final survey = filteredSurveys[index];

                            return Container(
                              margin: const EdgeInsets.only(bottom: 16),
                              padding: const EdgeInsets.all(18),
                              decoration: BoxDecoration(
                                color: const Color(0xFF424242),
                                borderRadius: BorderRadius.circular(18),
                                border: Border.all(color: const Color(0xFF555555)),
                              ),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    children: [
                                      Container(
                                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                        decoration: BoxDecoration(
                                          color: const Color(0xFF505050),
                                          borderRadius: BorderRadius.circular(12),
                                        ),
                                        child: Text(
                                          survey.track.toUpperCase(),
                                          style: const TextStyle(
                                            color: Color(0xFFD0D0D0),
                                            fontSize: 10,
                                            fontWeight: FontWeight.bold,
                                          ),
                                        ),
                                      ),
                                      if (_userRole == 'admin' || _userRole == 'org')
                                        IconButton(
                                          icon: const Icon(Icons.share_outlined, color: Colors.white70, size: 20),
                                          onPressed: () => _shareSurvey(survey),
                                        ),
                                    ],
                                  ),
                                  const SizedBox(height: 8),

                                  Text(
                                    survey.title,
                                    style: const TextStyle(
                                      color: Colors.white,
                                      fontSize: 16,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                  const SizedBox(height: 6),

                                  Text(
                                    survey.description,
                                    style: const TextStyle(
                                      color: Color(0xFFB8B8B8),
                                      fontSize: 13,
                                    ),
                                    maxLines: 2,
                                    overflow: TextOverflow.ellipsis,
                                  ),

                                  const SizedBox(height: 16),

                                  SizedBox(
                                    width: double.infinity,
                                    height: 44,
                                    child: ElevatedButton(
                                      onPressed: () async {
                                        await Navigator.of(context).push(
                                          MaterialPageRoute(
                                            builder: (context) => SurveyDetailScreen(
                                              survey: survey,
                                              userId: _userId,
                                            ),
                                          ),
                                        );
                                        _loadSurveys();
                                      },
                                      style: ElevatedButton.styleFrom(
                                        backgroundColor: const Color(0xFFE5E5E5),
                                        foregroundColor: const Color(0xFF2A2A2A),
                                        elevation: 0,
                                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(22)),
                                      ),
                                      child: const Text(
                                        'Take Survey',
                                        style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            );
                          },
                        ),
                    ),
            ),
          ],
        ),
      ),
      floatingActionButton: _showBackToTop
          ? FloatingActionButton.small(
              onPressed: scrollToTop,
              backgroundColor: const Color(0xFFE5E5E5),
              foregroundColor: const Color(0xFF2A2A2A),
              tooltip: 'Back to top',
              child: const Icon(Icons.arrow_upward),
            )
          : null,
    );
  }
}

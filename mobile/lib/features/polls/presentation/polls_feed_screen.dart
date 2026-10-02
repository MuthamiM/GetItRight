import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/models/poll_model.dart';
import '../../../core/network/api_client.dart';
import '../../../core/network/websocket_client.dart';

class PollsFeedScreen extends StatefulWidget {
  const PollsFeedScreen({super.key});

  @override
  State<PollsFeedScreen> createState() => _PollsFeedScreenState();
}

class _PollsFeedScreenState extends State<PollsFeedScreen> {
  final ApiClient _apiClient = ApiClient();
  final WebSocketVoteClient _wsClient = WebSocketVoteClient();
  List<Poll> _polls = [];
  bool _isLoading = true;
  String _selectedCategory = 'All';

  final List<String> _categories = [
    'All',
    'Engineering',
    'Architecture',
    'Governance',
    'Community'
  ];

  @override
  void initState() {
    super.initState();
    _loadPolls();
    _wsClient.connect();
    _wsClient.voteUpdates.listen((update) {
      if (mounted) {
        setState(() {
          // Update real-time tally if matching poll
        });
      }
    });
  }

  Future<void> _loadPolls() async {
    final polls = await _apiClient.fetchPolls();
    if (mounted) {
      setState(() {
        _polls = polls;
        _isLoading = false;
      });
    }
  }

  void _handleVote(Poll poll, String optionId) {
    setState(() {
      poll.selectedOptionId = optionId;
      poll.totalVotes += 1;
      for (var opt in poll.options) {
        if (opt.id == optionId) {
          opt.votes += 1;
        }
        opt.percentage = (opt.votes / poll.totalVotes) * 100.0;
      }
    });

    _wsClient.sendVote(pollId: poll.id, optionId: optionId);
    _apiClient.castVote(poll.id, optionId);

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Vote recorded successfully'),
        backgroundColor: AppColors.accent,
        behavior: SnackBarBehavior.floating,
        duration: Duration(seconds: 2),
      ),
    );
  }

  @override
  void dispose() {
    _wsClient.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Container(
              width: 30,
              height: 30,
              decoration: BoxDecoration(
                color: AppColors.accent,
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(Icons.bar_chart, color: Colors.black, size: 20),
            ),
            const SizedBox(width: 10),
            RichText(
              text: const TextSpan(
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                children: [
                  TextSpan(text: 'getitright', style: TextStyle(color: AppColors.textPrimary)),
                  TextSpan(text: '.', style: TextStyle(color: AppColors.accent)),
                ],
              ),
            ),
          ],
        ),
        actions: [
          Container(
            margin: const EdgeInsets.only(right: 16),
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: AppColors.accent.withOpacity(0.12),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppColors.accent.withOpacity(0.3)),
            ),
            child: const Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.bolt, color: AppColors.accent, size: 14),
                SizedBox(width: 4),
                Text(
                  'Live Sync',
                  style: TextStyle(color: AppColors.accent, fontSize: 12, fontWeight: FontWeight.w600),
                ),
              ],
            ),
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: AppColors.accent))
          : RefreshIndicator(
              color: AppColors.accent,
              backgroundColor: AppColors.bgCard,
              onRefresh: _loadPolls,
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  // Search Bar
                  TextField(
                    decoration: const InputDecoration(
                      hintText: 'Search active polls or topics...',
                      prefixIcon: Icon(Icons.search, color: AppColors.textSecondary),
                    ),
                  ),
                  const SizedBox(height: 16),

                  // Categories Horizontal Bar
                  SizedBox(
                    height: 38,
                    child: ListView.separated(
                      scrollDirection: Axis.horizontal,
                      itemCount: _categories.length,
                      separatorBuilder: (_, __) => const SizedBox(width: 8),
                      itemBuilder: (context, index) {
                        final cat = _categories[index];
                        final isSelected = cat == _selectedCategory;
                        return InkWell(
                          onTap: () => setState(() => _selectedCategory = cat),
                          borderRadius: BorderRadius.circular(AppRadius.pill),
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                            decoration: BoxDecoration(
                              color: isSelected ? AppColors.accent : AppColors.bgCard,
                              borderRadius: BorderRadius.circular(AppRadius.pill),
                              border: Border.all(
                                color: isSelected ? AppColors.accent : AppColors.border,
                              ),
                            ),
                            child: Text(
                              cat,
                              style: TextStyle(
                                color: isSelected ? Colors.black : AppColors.textPrimary,
                                fontSize: 13,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                        );
                      },
                    ),
                  ),
                  const SizedBox(height: 20),

                  // Polls List
                  ..._polls.map((poll) => _buildPollCard(poll)),
                ],
              ),
            ),
    );
  }

  Widget _buildPollCard(Poll poll) {
    return Card(
      margin: const EdgeInsets.only(bottom: 20),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Poll Header
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    CircleAvatar(
                      radius: 14,
                      backgroundColor: AppColors.bgElevated,
                      child: Text(
                        poll.authorName.isNotEmpty ? poll.authorName[0] : 'U',
                        style: const TextStyle(color: AppColors.accent, fontSize: 12, fontWeight: FontWeight.bold),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          poll.authorName,
                          style: const TextStyle(color: AppColors.textPrimary, fontSize: 13, fontWeight: FontWeight.w600),
                        ),
                        Text(
                          'Track: ${poll.trackName}',
                          style: const TextStyle(color: AppColors.textSecondary, fontSize: 11),
                        ),
                      ],
                    ),
                  ],
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: AppColors.accent.withOpacity(0.12),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: const Text(
                    'Active',
                    style: TextStyle(color: AppColors.accent, fontSize: 11, fontWeight: FontWeight.bold),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 14),

            // Title & Description
            Text(
              poll.title,
              style: const TextStyle(
                color: AppColors.textPrimary,
                fontSize: 16,
                fontWeight: FontWeight.w600,
                height: 1.35,
              ),
            ),
            if (poll.description.isNotEmpty) ...[
              const SizedBox(height: 6),
              Text(
                poll.description,
                style: const TextStyle(color: AppColors.textSecondary, fontSize: 13, height: 1.4),
              ),
            ],
            const SizedBox(height: 18),

            // Options List
            Column(
              children: poll.options.map((opt) {
                final isSelected = poll.selectedOptionId == opt.id;
                return InkWell(
                  onTap: () => _handleVote(poll, opt.id),
                  borderRadius: BorderRadius.circular(AppRadius.button),
                  child: Container(
                    margin: const EdgeInsets.only(bottom: 10),
                    height: 52,
                    clipBehavior: Clip.antiAlias,
                    decoration: BoxDecoration(
                      color: AppColors.bgElevated,
                      borderRadius: BorderRadius.circular(AppRadius.button),
                      border: Border.all(
                        color: isSelected ? AppColors.accent : AppColors.border,
                        width: isSelected ? 1.5 : 1.0,
                      ),
                    ),
                    child: Stack(
                      children: [
                        // Animated progress fill
                        FractionallySizedBox(
                          widthFactor: (opt.percentage / 100.0).clamp(0.0, 1.0),
                          child: Container(
                            decoration: BoxDecoration(
                              color: isSelected
                                  ? AppColors.accent.withOpacity(0.25)
                                  : AppColors.accent.withOpacity(0.12),
                              borderRadius: BorderRadius.circular(AppRadius.button),
                            ),
                          ),
                        ),
                        // Label and percent
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 16),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Expanded(
                                child: Row(
                                  children: [
                                    if (isSelected) ...[
                                      const Icon(Icons.check_circle, color: AppColors.accent, size: 18),
                                      const SizedBox(width: 8),
                                    ],
                                    Flexible(
                                      child: Text(
                                        opt.text,
                                        style: TextStyle(
                                          color: isSelected ? AppColors.textPrimary : AppColors.textPrimary.withOpacity(0.9),
                                          fontSize: 14,
                                          fontWeight: isSelected ? FontWeight.w600 : FontWeight.w500,
                                        ),
                                        overflow: TextOverflow.ellipsis,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              Text(
                                '${opt.percentage.toStringAsFixed(0)}%',
                                style: const TextStyle(
                                  color: AppColors.accent,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 14,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              }).toList(),
            ),

            const SizedBox(height: 8),
            // Footer Info
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  '${poll.totalVotes} total votes',
                  style: const TextStyle(color: AppColors.textSecondary, fontSize: 12),
                ),
                IconButton(
                  icon: const Icon(Icons.share_outlined, color: AppColors.textSecondary, size: 18),
                  onPressed: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Poll link copied')),
                    );
                  },
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

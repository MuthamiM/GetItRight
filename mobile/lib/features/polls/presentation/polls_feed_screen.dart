import 'dart:async';
import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:share_plus/share_plus.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../../core/models/poll_model.dart';
import '../../../core/network/api_client.dart';

class PollsFeedScreen extends StatefulWidget {
  const PollsFeedScreen({super.key});

  @override
  State<PollsFeedScreen> createState() => _PollsFeedScreenState();
}

class _PollsFeedScreenState extends State<PollsFeedScreen>
    with SingleTickerProviderStateMixin {
  final ApiClient _apiClient = ApiClient();
  List<Poll> _polls = [];
  bool _isLoading = true;
  String _selectedFilter = 'ALL';
  final List<String> _statusFilters = ['ALL', 'CLOSING', 'ENDED'];
  bool _showingSsup = false;
  late AnimationController _ssupController;
  late Animation<Offset> _ssupSlide;
  late Animation<double> _ssupOpacity;

  @override
  void initState() {
    super.initState();
    _ssupController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 400),
    );
    _ssupSlide = Tween<Offset>(
      begin: const Offset(0, -1),
      end: Offset.zero,
    ).animate(CurvedAnimation(parent: _ssupController, curve: Curves.easeOut));
    _ssupOpacity = Tween<double>(begin: 0.0, end: 1.0).animate(
        CurvedAnimation(parent: _ssupController, curve: Curves.easeOut));
    _loadPolls();
  }

  @override
  void dispose() {
    _ssupController.dispose();
    super.dispose();
  }

  Future<void> _loadPolls() async {
    final polls = await _apiClient.fetchPolls();
    final prefs = await SharedPreferences.getInstance();
    final now = DateTime.now();

    final activePolls = <Poll>[];
    for (var p in polls) {
      // 1. Check if user voted on this poll over 5 hours ago
      final votedTimeStr = prefs.getString('gir_voted_time_${p.id}');
      if (votedTimeStr != null) {
        final votedTime = DateTime.tryParse(votedTimeStr);
        if (votedTime != null && now.difference(votedTime).inHours >= 5) {
          continue; // Hide 5 hours after vote
        }
      }

      // Restore saved vote selection so refreshing home DOES NOT reset votes
      final savedOptionId = prefs.getString('gir_voted_option_${p.id}');
      if (savedOptionId != null) {
        p.selectedOptionId = savedOptionId;
      }

      // 2. Only expire closed/ended polls where countdown expired over 5 hours ago
      if (p.status == 'closed' || p.status == 'ended') {
        final deadline = p.createdAt.add(const Duration(hours: 24));
        if (now.isAfter(deadline.add(const Duration(hours: 5)))) {
          continue; // Hide 5 hours after countdown / results final
        }
      }

      activePolls.add(p);
    }

    if (mounted) {
      setState(() {
        _polls = activePolls.isNotEmpty ? activePolls : polls;
        _isLoading = false;
      });
    }
  }

  Future<void> _sharePoll(Poll poll) async {
    final shareUrl = _apiClient.generateShareLink(type: 'poll', id: poll.id);
    final shareMessage =
        '🗳️ Cast your vote on GetitRight!\n\n${poll.title}\n\n👉 Vote now: $shareUrl';

    // Copy to clipboard as quick fallback
    Clipboard.setData(ClipboardData(text: shareUrl));

    try {
      await Share.share(
        shareMessage,
        subject: poll.title,
      );
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Row(
              children: [
                const Icon(Icons.share, color: Color(0xFF2A2A2A), size: 18),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Poll link copied for sharing:\n$shareUrl',
                    style: const TextStyle(
                      color: Color(0xFF2A2A2A),
                      fontWeight: FontWeight.bold,
                      fontSize: 12,
                    ),
                  ),
                ),
              ],
            ),
            backgroundColor: const Color(0xFFE5E5E5),
            duration: const Duration(seconds: 3),
          ),
        );
      }
    }
  }

  void _handleVote(Poll poll, String optionId, {int? optionIndex}) async {
    if (poll.selectedOptionId != null) return;

    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(
        'gir_voted_time_${poll.id}', DateTime.now().toIso8601String());
    await prefs.setString('gir_voted_option_${poll.id}', optionId);

    setState(() {
      poll.selectedOptionId = optionId;
      poll.totalVotes += 1;
      for (var opt in poll.options) {
        if (opt.id == optionId) {
          opt.votes += 1;
        }
        opt.percentage =
            poll.totalVotes > 0 ? (opt.votes / poll.totalVotes) * 100.0 : 0.0;
      }
    });

    _apiClient.castVote(poll.id, optionId, optionIndex: optionIndex);

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Row(
            children: [
              Icon(Icons.check_circle, color: Color(0xFF2A2A2A), size: 18),
              SizedBox(width: 8),
              Text(
                'VOTED',
                style: TextStyle(
                  color: Color(0xFF2A2A2A),
                  fontWeight: FontWeight.bold,
                  fontSize: 14,
                ),
              ),
            ],
          ),
          backgroundColor: Color(0xFFE5E5E5),
          duration: Duration(seconds: 2),
        ),
      );
    }
  }

  Future<void> _handleRefresh() async {
    if (mounted) {
      setState(() => _showingSsup = true);
      _ssupController.forward(from: 0);
    }
    await _loadPolls();
    await Future.delayed(const Duration(milliseconds: 1200));
    if (mounted) {
      await _ssupController.reverse();
      setState(() => _showingSsup = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final filteredPolls = _polls.where((p) {
      if (_selectedFilter == 'CLOSING') {
        return p.status != 'closed' && p.status != 'ended';
      } else if (_selectedFilter == 'ENDED') {
        return p.status == 'closed' || p.status == 'ended';
      }
      return true;
    }).toList();

    return Scaffold(
      backgroundColor: const Color(0xFF303030),
      body: SafeArea(
        child: Stack(
          children: [
            Column(
              children: [
                // Status Dropdown Filter (ALL, CLOSING, ENDED)
                Padding(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  child: Row(
                    children: [
                      const Icon(Icons.filter_list,
                          color: Color(0xFFB8B8B8), size: 18),
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
                            icon: const Icon(Icons.arrow_drop_down,
                                color: Colors.white),
                            style: const TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                              fontSize: 13,
                            ),
                            items: _statusFilters.map((filter) {
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

                // Poll List with Pull-to-Refresh
                Expanded(
                  child: _isLoading
                      ? const Center(
                          child: CircularProgressIndicator(
                              color: Colors.white, strokeWidth: 2),
                        )
                      : RefreshIndicator(
                          color: const Color(0xFF303030),
                          backgroundColor: const Color(0xFFE5E5E5),
                          onRefresh: _handleRefresh,
                          child: filteredPolls.isEmpty
                              ? ListView(
                                  physics:
                                      const AlwaysScrollableScrollPhysics(),
                                  children: const [
                                    SizedBox(height: 120),
                                    Center(
                                      child: Text(
                                        'No polls available',
                                        style:
                                            TextStyle(color: Color(0xFFB8B8B8)),
                                      ),
                                    ),
                                  ],
                                )
                              : ListView.builder(
                                  physics:
                                      const AlwaysScrollableScrollPhysics(),
                                  padding: const EdgeInsets.all(16),
                                  itemCount: filteredPolls.length,
                                  itemBuilder: (context, index) {
                                    final poll = filteredPolls[index];
                                    final hasVoted =
                                        poll.selectedOptionId != null;

                                    return Container(
                                      margin: const EdgeInsets.only(bottom: 16),
                                      padding: const EdgeInsets.all(18),
                                      decoration: BoxDecoration(
                                        color: const Color(0xFF424242),
                                        borderRadius: BorderRadius.circular(18),
                                        border: Border.all(
                                            color: const Color(0xFF555555)),
                                      ),
                                      child: Column(
                                        crossAxisAlignment:
                                            CrossAxisAlignment.start,
                                        children: [
                                          // Header Tag & Status
                                          Row(
                                            mainAxisAlignment:
                                                MainAxisAlignment.spaceBetween,
                                            children: [
                                              Container(
                                                padding:
                                                    const EdgeInsets.symmetric(
                                                        horizontal: 10,
                                                        vertical: 4),
                                                decoration: BoxDecoration(
                                                  color:
                                                      const Color(0xFF505050),
                                                  borderRadius:
                                                      BorderRadius.circular(12),
                                                ),
                                                child: Text(
                                                  poll.trackName.toUpperCase(),
                                                  style: const TextStyle(
                                                    color: Color(0xFFD0D0D0),
                                                    fontSize: 10,
                                                    fontWeight: FontWeight.bold,
                                                  ),
                                                ),
                                              ),
                                              Row(
                                                children: [
                                                  const Row(
                                                    children: [
                                                      Icon(Icons.pie_chart,
                                                          size: 14,
                                                          color: Colors.white70),
                                                      SizedBox(width: 4),
                                                      Text(
                                                        'LIVE TALLY',
                                                        style: TextStyle(
                                                          color: Colors.white70,
                                                          fontSize: 10,
                                                          fontWeight:
                                                              FontWeight.bold,
                                                        ),
                                                      ),
                                                    ],
                                                  ),
                                                  const SizedBox(width: 10),
                                                  InkWell(
                                                    onTap: () => _sharePoll(poll),
                                                    borderRadius: BorderRadius.circular(10),
                                                    child: Container(
                                                      padding: const EdgeInsets.symmetric(
                                                          horizontal: 8, vertical: 3),
                                                      decoration: BoxDecoration(
                                                        color: const Color(0xFF5A5A5A),
                                                        borderRadius: BorderRadius.circular(10),
                                                        border: Border.all(
                                                            color: const Color(0xFF707070)),
                                                      ),
                                                      child: const Row(
                                                        mainAxisSize: MainAxisSize.min,
                                                        children: [
                                                          Icon(Icons.share,
                                                              size: 11,
                                                              color: Colors.white),
                                                          SizedBox(width: 4),
                                                          Text(
                                                            'SHARE',
                                                            style: TextStyle(
                                                              color: Colors.white,
                                                              fontSize: 9,
                                                              fontWeight:
                                                                  FontWeight.bold,
                                                              letterSpacing: 0.5,
                                                            ),
                                                          ),
                                                        ],
                                                      ),
                                                    ),
                                                  ),
                                                ],
                                              ),
                                            ],
                                          ),
                                          const SizedBox(height: 10),

                                          // Question Title
                                          Text(
                                            poll.title,
                                            style: const TextStyle(
                                              color: Colors.white,
                                              fontSize: 16,
                                              fontWeight: FontWeight.bold,
                                            ),
                                          ),

                                          // Description
                                          if (poll.description.isNotEmpty) ...[
                                            const SizedBox(height: 6),
                                            Text(
                                              poll.description,
                                              style: const TextStyle(
                                                color: Color(0xFFB8B8B8),
                                                fontSize: 12,
                                              ),
                                              maxLines: 2,
                                              overflow: TextOverflow.ellipsis,
                                            ),
                                          ],

                                          const SizedBox(height: 16),

                                          // Live Pie Chart Widget (Interactive)
                                          InteractivePieChartWidget(poll: poll),

                                          const SizedBox(height: 16),

                                          // Vote Buttons (Candidate List)
                                          ...poll.options
                                              .asMap()
                                              .entries
                                              .map((entry) {
                                            final i = entry.key;
                                            final opt = entry.value;
                                            final isSelectedOption =
                                                poll.selectedOptionId == opt.id;
                                            final sliceColor =
                                                InteractivePieChartWidget
                                                        .sliceColors[
                                                    i %
                                                        InteractivePieChartWidget
                                                            .sliceColors
                                                            .length];

                                            return GestureDetector(
                                              onTap: hasVoted
                                                  ? null
                                                  : () =>
                                                      _handleVote(poll, opt.id, optionIndex: i),
                                              child: Container(
                                                margin: const EdgeInsets.only(
                                                    bottom: 10),
                                                padding:
                                                    const EdgeInsets.symmetric(
                                                        horizontal: 14,
                                                        vertical: 12),
                                                decoration: BoxDecoration(
                                                  color: isSelectedOption
                                                      ? const Color(0xFF606060)
                                                      : const Color(0xFF505050),
                                                  borderRadius:
                                                      BorderRadius.circular(14),
                                                  border: Border.all(
                                                    color: isSelectedOption
                                                        ? sliceColor
                                                        : Colors.transparent,
                                                    width: isSelectedOption
                                                        ? 2
                                                        : 0,
                                                  ),
                                                ),
                                                child: Row(
                                                  children: [
                                                    // Color dot matching pie
                                                    Container(
                                                      width: 12,
                                                      height: 12,
                                                      decoration: BoxDecoration(
                                                        color: sliceColor,
                                                        shape: BoxShape.circle,
                                                      ),
                                                    ),
                                                    const SizedBox(width: 10),

                                                    Expanded(
                                                      child: Text(
                                                        opt.text,
                                                        style: const TextStyle(
                                                          color: Colors.white,
                                                          fontSize: 14,
                                                          fontWeight:
                                                              FontWeight.w500,
                                                        ),
                                                      ),
                                                    ),

                                                    Text(
                                                      '${opt.votes} votes (${opt.percentage.toStringAsFixed(1)}%)',
                                                      style: TextStyle(
                                                        color: sliceColor,
                                                        fontSize: 12,
                                                        fontWeight:
                                                            FontWeight.bold,
                                                      ),
                                                    ),
                                                    const SizedBox(width: 8),

                                                    if (isSelectedOption)
                                                      Container(
                                                        padding:
                                                            const EdgeInsets
                                                                .symmetric(
                                                                horizontal: 8,
                                                                vertical: 3),
                                                        decoration:
                                                            BoxDecoration(
                                                          color: sliceColor,
                                                          borderRadius:
                                                              BorderRadius
                                                                  .circular(10),
                                                        ),
                                                        child: const Text(
                                                          'VOTED',
                                                          style: TextStyle(
                                                            color: Color(
                                                                0xFF2A2A2A),
                                                            fontSize: 10,
                                                            fontWeight:
                                                                FontWeight.w900,
                                                          ),
                                                        ),
                                                      )
                                                    else if (!hasVoted)
                                                      const Text(
                                                        'Vote',
                                                        style: TextStyle(
                                                          color:
                                                              Color(0xFFB8B8B8),
                                                          fontSize: 12,
                                                          fontWeight:
                                                              FontWeight.w600,
                                                        ),
                                                      ),
                                                  ],
                                                ),
                                              ),
                                            );
                                          }),

                                          const SizedBox(height: 10),

                                          // Total Votes & Prominent Share Poll Button (WhatsApp, TikTok, IG, FB)
                                          Row(
                                            mainAxisAlignment:
                                                MainAxisAlignment.spaceBetween,
                                            children: [
                                              Text(
                                                '${poll.totalVotes} total votes • Live updating',
                                                style: const TextStyle(
                                                  color: Color(0xFFB8B8B8),
                                                  fontSize: 12,
                                                ),
                                              ),
                                              ElevatedButton.icon(
                                                onPressed: () =>
                                                    _sharePoll(poll),
                                                icon: const Icon(
                                                    Icons.share_rounded,
                                                    size: 14,
                                                    color: Color(0xFF2A2A2A)),
                                                label: const Text(
                                                  'Share Poll',
                                                  style: TextStyle(
                                                    color: Color(0xFF2A2A2A),
                                                    fontWeight: FontWeight.bold,
                                                    fontSize: 12,
                                                  ),
                                                ),
                                                style: ElevatedButton.styleFrom(
                                                  backgroundColor:
                                                      const Color(0xFFE5E5E5),
                                                  foregroundColor:
                                                      const Color(0xFF2A2A2A),
                                                  padding:
                                                      const EdgeInsets.symmetric(
                                                          horizontal: 14,
                                                          vertical: 8),
                                                  minimumSize: Size.zero,
                                                  tapTargetSize:
                                                      MaterialTapTargetSize
                                                          .shrinkWrap,
                                                  shape: RoundedRectangleBorder(
                                                    borderRadius:
                                                        BorderRadius.circular(
                                                            16),
                                                  ),
                                                  elevation: 0,
                                                ),
                                              ),
                                            ],
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

            // "ssup!" top overlay — slides down from top on pull-to-refresh
            if (_showingSsup)
              Positioned(
                top: 0,
                left: 0,
                right: 0,
                child: SlideTransition(
                  position: _ssupSlide,
                  child: FadeTransition(
                    opacity: _ssupOpacity,
                    child: Container(
                      alignment: Alignment.center,
                      padding: const EdgeInsets.symmetric(vertical: 10),
                      decoration: BoxDecoration(
                        color: const Color(0xFFE5E5E5),
                        borderRadius: const BorderRadius.only(
                          bottomLeft: Radius.circular(16),
                          bottomRight: Radius.circular(16),
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withOpacity(0.3),
                            blurRadius: 8,
                            offset: const Offset(0, 2),
                          ),
                        ],
                      ),
                      child: const Text(
                        'ssup!',
                        style: TextStyle(
                          color: Color(0xFF2A2A2A),
                          fontWeight: FontWeight.w900,
                          fontSize: 16,
                          letterSpacing: 1.2,
                        ),
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

// ──────────────────────────────────────────────
// Pie Chart Widget with Dynamic Moving Countdown Timer
// ──────────────────────────────────────────────
class InteractivePieChartWidget extends StatefulWidget {
  final Poll poll;

  static const List<Color> sliceColors = [
    Color(0xFF29B6F6), // Light Blue
    Color(0xFFFF9800), // Orange
    Color(0xFF66BB6A), // Green
    Color(0xFFAB47BC), // Purple
    Color(0xFFFFCA28), // Amber
    Color(0xFFEF5350), // Red
    Color(0xFF26C6DA), // Cyan
    Color(0xFF8D6E63), // Brown
  ];

  const InteractivePieChartWidget({super.key, required this.poll});

  @override
  State<InteractivePieChartWidget> createState() =>
      _InteractivePieChartWidgetState();
}

class _InteractivePieChartWidgetState extends State<InteractivePieChartWidget> {
  Timer? _countdownTimer;
  int? _selectedIndex;

  @override
  void initState() {
    super.initState();
    _countdownTimer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (mounted) setState(() {});
    });
  }

  @override
  void dispose() {
    _countdownTimer?.cancel();
    super.dispose();
  }

  String _formatMovingCountdown() {
    final deadline = widget.poll.createdAt.add(const Duration(hours: 24));
    final diff = deadline.difference(DateTime.now());
    if (diff.isNegative) {
      return 'Voting Closed • Final Results';
    }
    final hours = diff.inHours.toString().padLeft(2, '0');
    final minutes = (diff.inMinutes % 60).toString().padLeft(2, '0');
    final seconds = (diff.inSeconds % 60).toString().padLeft(2, '0');
    return 'Voting Closes in $hours:$minutes:$seconds • Live Results';
  }

  @override
  Widget build(BuildContext context) {
    if (widget.poll.totalVotes == 0 || widget.poll.options.isEmpty) {
      return Container(
        height: 100,
        alignment: Alignment.center,
        child: const Text(
          'Waiting for votes...',
          style: TextStyle(color: Color(0xFFB8B8B8), fontSize: 13),
        ),
      );
    }

    final selectedOpt =
        (_selectedIndex != null && _selectedIndex! < widget.poll.options.length)
            ? widget.poll.options[_selectedIndex!]
            : null;
    final selectedColor = (_selectedIndex != null)
        ? InteractivePieChartWidget.sliceColors[
            _selectedIndex! % InteractivePieChartWidget.sliceColors.length]
        : null;

    return Column(
      children: [
        // Moving Countdown Banner (Ticks every second)
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          margin: const EdgeInsets.only(bottom: 14),
          decoration: BoxDecoration(
            color: const Color(0xFF505050),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.timer_outlined, size: 14, color: Colors.white),
              const SizedBox(width: 6),
              Text(
                _formatMovingCountdown(),
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ),

        // Interactive Pie Chart (Tappable slices showing specific vote count)
        GestureDetector(
          behavior: HitTestBehavior.opaque,
          onTapUp: (details) {
            const size = Size(160, 160);
            final center = Offset(size.width / 2, size.height / 2);
            final dx = details.localPosition.dx - center.dx;
            final dy = details.localPosition.dy - center.dy;

            // Center donut tap clears selection
            if (math.sqrt(dx * dx + dy * dy) < 32) {
              setState(() => _selectedIndex = null);
              return;
            }

            double angle = math.atan2(dy, dx);
            if (angle < -math.pi / 2) {
              angle += 2 * math.pi;
            }

            double start = -math.pi / 2;
            for (int i = 0; i < widget.poll.options.length; i++) {
              final opt = widget.poll.options[i];
              final sweep = widget.poll.totalVotes > 0
                  ? (opt.votes / widget.poll.totalVotes) * 2 * math.pi
                  : 0.0;
              if (angle >= start && angle < start + sweep) {
                setState(() {
                  _selectedIndex = (_selectedIndex == i) ? null : i;
                });
                return;
              }
              start += sweep;
            }
          },
          child: SizedBox(
            height: 160,
            width: 160,
            child: Stack(
              alignment: Alignment.center,
              children: [
                CustomPaint(
                  size: const Size(160, 160),
                  painter: ColorfulPieChartPainter(
                    options: widget.poll.options,
                    totalVotes: widget.poll.totalVotes,
                    colors: InteractivePieChartWidget.sliceColors,
                    selectedIndex: _selectedIndex,
                  ),
                ),

                // Center donut label displaying specific vote count when slice/aspirant is clicked
                Container(
                  width: 66,
                  height: 66,
                  padding: const EdgeInsets.all(4),
                  decoration: BoxDecoration(
                    color: const Color(0xFF424242).withAlpha(245),
                    shape: BoxShape.circle,
                    border: Border.all(
                      color: selectedColor ?? const Color(0xFF666666),
                      width: selectedOpt != null ? 2 : 1,
                    ),
                  ),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      if (selectedOpt != null) ...[
                        Text(
                          selectedOpt.text,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 9,
                            fontWeight: FontWeight.bold,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          textAlign: TextAlign.center,
                        ),
                        Text(
                          '${selectedOpt.votes} votes',
                          style: TextStyle(
                            color: selectedColor,
                            fontSize: 11,
                            fontWeight: FontWeight.w900,
                          ),
                        ),
                        Text(
                          '(${selectedOpt.percentage.toStringAsFixed(1)}%)',
                          style: const TextStyle(
                            color: Color(0xFFD0D0D0),
                            fontSize: 9,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ] else ...[
                        Text(
                          '${widget.poll.totalVotes}',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 13,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const Text(
                          'Total Votes',
                          style:
                              TextStyle(color: Color(0xFFB8B8B8), fontSize: 9),
                        ),
                        const Text(
                          'Tap slice',
                          style: TextStyle(color: Colors.white38, fontSize: 8),
                        ),
                      ],
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),

        const SizedBox(height: 14),

        // Color-coded Candidate Legend — Tappable Aspirants
        _buildCandidateLegend(),

        const SizedBox(height: 12),
      ],
    );
  }

  Widget _buildCandidateLegend() {
    final opts = widget.poll.options;
    const colors = InteractivePieChartWidget.sliceColors;

    final List<Widget> rows = [];
    for (int i = 0; i < opts.length; i += 2) {
      rows.add(
        Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: Row(
            children: [
              Expanded(
                  child:
                      _buildLegendItem(opts[i], colors[i % colors.length], i)),
              if (i + 1 < opts.length)
                Expanded(
                    child: _buildLegendItem(
                        opts[i + 1], colors[(i + 1) % colors.length], i + 1))
              else
                const Expanded(child: SizedBox()),
            ],
          ),
        ),
      );
    }

    return Column(children: rows);
  }

  Widget _buildLegendItem(PollOption opt, Color color, int index) {
    final isSelected = _selectedIndex == index;

    return GestureDetector(
      onTap: () {
        setState(() {
          _selectedIndex = (isSelected) ? null : index;
        });
      },
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
        margin: const EdgeInsets.symmetric(horizontal: 2),
        decoration: BoxDecoration(
          color: isSelected ? color.withOpacity(0.25) : Colors.transparent,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: isSelected ? color : Colors.transparent,
            width: 1,
          ),
        ),
        child: Row(
          children: [
            Container(
              width: 10,
              height: 10,
              decoration: BoxDecoration(
                color: color,
                shape: BoxShape.circle,
              ),
            ),
            const SizedBox(width: 6),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    opt.text,
                    style: TextStyle(
                      color:
                          isSelected ? Colors.white : const Color(0xFFD0D0D0),
                      fontSize: 11,
                      fontWeight:
                          isSelected ? FontWeight.bold : FontWeight.w500,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  Text(
                    '${opt.votes} votes (${opt.percentage.toStringAsFixed(1)}%)',
                    style: TextStyle(
                      color: color,
                      fontSize: 9,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ──────────────────────────────────────────────
// Colorful Pie Chart Painter with Slice Highlighting
// ──────────────────────────────────────────────
class ColorfulPieChartPainter extends CustomPainter {
  final List<PollOption> options;
  final int totalVotes;
  final List<Color> colors;
  final int? selectedIndex;

  ColorfulPieChartPainter({
    required this.options,
    required this.totalVotes,
    required this.colors,
    this.selectedIndex,
  });

  @override
  void paint(Canvas canvas, Size size) {
    if (totalVotes == 0) return;

    final center = Offset(size.width / 2, size.height / 2);
    final baseRadius = math.min(size.width / 2, size.height / 2) - 4;

    double startAngle = -math.pi / 2;

    for (int i = 0; i < options.length; i++) {
      final opt = options[i];
      final sweepAngle = (opt.votes / totalVotes) * 2 * math.pi;
      final isSelected = selectedIndex == i;

      final radius = isSelected ? baseRadius + 4 : baseRadius;
      final rect = Rect.fromCircle(center: center, radius: radius);

      final paint = Paint()
        ..style = PaintingStyle.fill
        ..color = colors[i % colors.length];

      canvas.drawArc(rect, startAngle, sweepAngle, true, paint);

      // Separator border
      final borderPaint = Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = isSelected ? 3 : 2
        ..color = isSelected ? Colors.white : const Color(0xFF424242);

      canvas.drawArc(rect, startAngle, sweepAngle, true, borderPaint);

      startAngle += sweepAngle;
    }
  }

  @override
  bool shouldRepaint(covariant ColorfulPieChartPainter oldDelegate) {
    return oldDelegate.totalVotes != totalVotes ||
        oldDelegate.options != options ||
        oldDelegate.selectedIndex != selectedIndex;
  }
}

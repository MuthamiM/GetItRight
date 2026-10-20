import 'dart:async';
import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:share_plus/share_plus.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../core/models/poll_model.dart';
import '../../../core/location/precise_location.dart';
import '../../../core/network/api_client.dart';

class PollsFeedScreen extends StatefulWidget {
  const PollsFeedScreen({super.key});

  @override
  State<PollsFeedScreen> createState() => PollsFeedScreenState();
}

class PollsFeedScreenState extends State<PollsFeedScreen>
    with SingleTickerProviderStateMixin {
  final ApiClient _apiClient = ApiClient();
  final ScrollController scrollController = ScrollController();
  List<Poll> _polls = [];
  bool _isLoading = true;
  bool _showBackToTop = false;
  String _selectedFilter = 'ALL';
  final List<String> _statusFilters = ['ALL', 'CLOSING', 'ENDED'];
  int _visibleCount = 5; // Show 5 polls on home screen by default
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

    scrollController.addListener(() {
      final show = scrollController.hasClients && scrollController.offset > 150;
      if (show != _showBackToTop && mounted) {
        setState(() => _showBackToTop = show);
      }
    });

    _loadPolls();
  }

  @override
  void dispose() {
    scrollController.dispose();
    _ssupController.dispose();
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

  bool _isZakSyengoPoll(Poll p) {
    final titleLower = p.title.toLowerCase();
    final idLower = p.id.toLowerCase();
    return idLower.contains('kitui-east') ||
        titleLower.contains('kitui east') ||
        titleLower.contains('zak syengo') ||
        p.options.any((o) => o.text.toLowerCase().contains('syengo'));
  }

  String? _accountVoteCachePrefix(SharedPreferences prefs) {
    final accountId = prefs.getString('gir_user_id')?.trim();
    if (accountId == null || accountId.isEmpty) return null;
    return 'gir_account_vote_${Uri.encodeComponent(accountId)}';
  }

  String? _cachedAccountVote(Poll poll, SharedPreferences prefs) {
    final prefix = _accountVoteCachePrefix(prefs);
    if (prefix == null ||
        prefs.getBool('${prefix}_${poll.id}_has_voted') != true) {
      return null;
    }
    final optionId = prefs.getString('${prefix}_${poll.id}_option');
    return optionId != null &&
            poll.options.any((option) => option.id == optionId)
        ? optionId
        : '__voted__';
  }

  Future<void> _cacheAccountVote(
    Poll poll,
    SharedPreferences prefs, {
    String? optionId,
  }) async {
    final prefix = _accountVoteCachePrefix(prefs);
    if (prefix == null) return;
    await prefs.setBool('${prefix}_${poll.id}_has_voted', true);
    if (optionId != null) {
      await prefs.setString('${prefix}_${poll.id}_option', optionId);
    } else {
      await prefs.remove('${prefix}_${poll.id}_option');
    }
  }

  Future<void> _clearAccountVoteCache(
      Poll poll, SharedPreferences prefs) async {
    final prefix = _accountVoteCachePrefix(prefs);
    if (prefix == null) return;
    await prefs.remove('${prefix}_${poll.id}_has_voted');
    await prefs.remove('${prefix}_${poll.id}_option');
  }

  int? _optionArrayIndex(Poll poll, Object? rawOptionIndex) {
    final optionIndex = rawOptionIndex is int
        ? rawOptionIndex
        : int.tryParse(rawOptionIndex?.toString() ?? '');
    if (optionIndex == null) return null;
    final apiIndex =
        poll.options.indexWhere((option) => option.index == optionIndex);
    if (apiIndex >= 0) return apiIndex;
    if (optionIndex >= 0 && optionIndex < poll.options.length) {
      return optionIndex;
    }
    return null;
  }

  String? _optionIdForStatus(Poll poll, Map<String, dynamic>? status) {
    final arrayIndex = _optionArrayIndex(poll, status?['optionIndex']);
    return arrayIndex == null ? null : poll.options[arrayIndex].id;
  }

  /// Format countdown strictly as "Xd Xh XXmins left", no emojis, no Root, no 0x
  String _formatPollCountdown(Poll poll) {
    DateTime deadline;
    if (poll.endDate != null) {
      deadline = poll.endDate!;
    } else {
      deadline = poll.createdAt.add(const Duration(days: 7));
    }
    final diff = deadline.difference(DateTime.now());
    if (diff.isNegative) {
      return 'Voting Closed';
    }
    final days = diff.inDays;
    final hours = diff.inHours % 24;
    final minutes = diff.inMinutes % 60;
    pad(int n) => n.toString().padLeft(2, '0');
    if (days >= 1) {
      return '${days}d ${hours}h ${pad(minutes)}mins left';
    } else {
      return '${hours}h ${pad(minutes)}mins left';
    }
  }

  Future<void> _loadPolls() async {
    final polls = await _apiClient.fetchPolls();
    // Prioritize Zak Syengo / Kitui East poll at the very top, then newest
    polls.sort((a, b) {
      final isZakA = _isZakSyengoPoll(a);
      final isZakB = _isZakSyengoPoll(b);
      if (isZakA && !isZakB) return -1;
      if (!isZakA && isZakB) return 1;
      return b.createdAt.compareTo(a.createdAt);
    });
    final prefs = await SharedPreferences.getInstance();
    final savedNationalId = prefs.getString('gir_voter_id_number') ??
        prefs.getString('gir_user_national_id') ??
        '';
    final savedVoterKey = prefs.getString('gir_voter_key');
    final hasAccountSession = (prefs.getString('gir_token') ?? '').isNotEmpty;
    final hasIdentity = savedNationalId.isNotEmpty ||
        (savedVoterKey != null && savedVoterKey.isNotEmpty);
    final serverVoteStatuses = hasAccountSession || hasIdentity
        ? await Future.wait(polls.map((poll) => _apiClient.getVoteStatus(
              poll.id,
              // Check both the signed-in account and the ID used on older
              // ballots, which may not have an account ID recorded yet.
              savedNationalId,
              // A device-wide voter key must never follow a user into another
              // signed-in account.
              voterKey: hasAccountSession ? null : savedVoterKey,
            )))
        : List<Map<String, dynamic>?>.filled(polls.length, null);
    final now = DateTime.now();

    final activePolls = <Poll>[];
    for (var index = 0; index < polls.length; index++) {
      final p = polls[index];
      final isZak = _isZakSyengoPoll(p);
      final serverStatus = serverVoteStatuses[index];

      if (serverStatus?['hasVoted'] == true) {
        p.selectedOptionId = _optionIdForStatus(p, serverStatus) ?? '__voted__';
        await _cacheAccountVote(
          p,
          prefs,
          optionId:
              p.selectedOptionId == '__voted__' ? null : p.selectedOptionId,
        );
      } else if (serverStatus?['hasVoted'] == false) {
        // Server ballot status is authoritative; clear this account's cache.
        await _clearAccountVoteCache(p, prefs);
        p.selectedOptionId = null;
      } else {
        // Preserve a confirmed local state during a temporary network outage,
        // but scope it to this account so shared devices do not cross-contaminate.
        p.selectedOptionId = _cachedAccountVote(p, prefs);
      }

      // Keep server-confirmed votes visible so users can always see their
      // VOTED status after signing in again. Only expire old ended polls from
      // the feed; their ballot status remains stored on the server.
      if (!isZak) {
        if (p.status == 'closed' || p.status == 'ended') {
          final deadline = p.createdAt.add(const Duration(hours: 24));
          if (now.isAfter(deadline.add(const Duration(hours: 5)))) {
            continue; // Hide 5 hours after countdown / results final
          }
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

  Future<void> _openUrl(String url) async {
    try {
      final uri = Uri.parse(url);
      if (await canLaunchUrl(uri)) {
        await launchUrl(uri, mode: LaunchMode.externalApplication);
      } else {
        await launchUrl(uri, mode: LaunchMode.platformDefault);
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Could not open link: $url'),
            backgroundColor: const Color(0xFFE5E5E5),
          ),
        );
      }
    }
  }

  Future<void> _sharePoll(Poll poll) async {
    final shareUrl = _apiClient.generateShareLink(type: 'poll', id: poll.id);
    final shareMessage =
        'Cast your vote on IcapsQ!\n\n${poll.title}\n\nVote now: $shareUrl';

    // Copy to clipboard
    Clipboard.setData(ClipboardData(text: shareUrl));

    if (!mounted) return;

    // Show interactive bottom sheet with clickable link
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF2E2E2E),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (ctx) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 20, 20, 24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    'Share Poll Link',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close, color: Colors.white70),
                    onPressed: () => Navigator.pop(ctx),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              Text(
                poll.title,
                style: const TextStyle(color: Color(0xFFB8B8B8), fontSize: 13),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 16),
              // Directly clickable shared link
              InkWell(
                onTap: () {
                  Navigator.pop(ctx);
                  _openUrl(shareUrl);
                },
                borderRadius: BorderRadius.circular(12),
                child: Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: const Color(0xFF3D3D3D),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: const Color(0xFF555555)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.link,
                          color: Color(0xFF64B5F6), size: 18),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          shareUrl,
                          style: const TextStyle(
                            color: Color(0xFF64B5F6),
                            fontSize: 13,
                            fontWeight: FontWeight.w600,
                            decoration: TextDecoration.underline,
                            decorationColor: Color(0xFF64B5F6),
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      const SizedBox(width: 8),
                      const Icon(Icons.open_in_new,
                          color: Color(0xFF64B5F6), size: 16),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 18),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () {
                        Clipboard.setData(ClipboardData(text: shareUrl));
                        Navigator.pop(ctx);
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text(
                              'Link copied to clipboard',
                              style: TextStyle(
                                  color: Color(0xFF2A2A2A),
                                  fontWeight: FontWeight.bold),
                            ),
                            backgroundColor: Color(0xFFE5E5E5),
                            duration: Duration(seconds: 2),
                          ),
                        );
                      },
                      icon:
                          const Icon(Icons.copy, size: 16, color: Colors.white),
                      label: const Text('Copy Link',
                          style: TextStyle(color: Colors.white)),
                      style: OutlinedButton.styleFrom(
                        side: const BorderSide(color: Color(0xFF666666)),
                        padding: const EdgeInsets.symmetric(vertical: 12),
                        shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(14)),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: ElevatedButton.icon(
                      onPressed: () {
                        Navigator.pop(ctx);
                        Share.share(shareMessage, subject: poll.title);
                      },
                      icon: const Icon(Icons.share,
                          size: 16, color: Color(0xFF2A2A2A)),
                      label: const Text('Share App',
                          style: TextStyle(
                              color: Color(0xFF2A2A2A),
                              fontWeight: FontWeight.bold)),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFFE5E5E5),
                        foregroundColor: const Color(0xFF2A2A2A),
                        padding: const EdgeInsets.symmetric(vertical: 12),
                        shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(14)),
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  static const List<String> _kenyaCounties = [
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
    "Murang'a",
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
    'West Pokot'
  ];

  Future<void> _pickDobForPolls(
      BuildContext context,
      TextEditingController controller,
      void Function(void Function()) setDialogState) async {
    final now = DateTime.now();
    DateTime initial = DateTime(now.year - 20, now.month, now.day);
    if (controller.text.trim().isNotEmpty) {
      try {
        final parsed = DateTime.parse(controller.text.trim());
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
      setDialogState(() {
        controller.text = formatted;
      });
    }
  }

  Future<bool> _showVoterDemographicsDialog(BuildContext context) async {
    final prefs = await SharedPreferences.getInstance();
    if (!context.mounted) return false;
    final nameController = TextEditingController(
        text: prefs.getString('gir_voter_name') ??
            prefs.getString('gir_user_name') ??
            '');
    final savedId = (prefs.getString('gir_voter_id_number') ??
            prefs.getString('gir_user_national_id') ??
            '')
        .replaceAll(RegExp(r'\D'), '');
    final idController = TextEditingController(
        text: savedId.length > 12 ? savedId.substring(0, 12) : savedId);
    final dobController = TextEditingController(
        text: prefs.getString('gir_v_dob') ??
            prefs.getString('gir_user_dob') ??
            '');
    String? selectedCounty =
        prefs.getString('gir_user_county') ?? prefs.getString('gir_county');
    if (!_kenyaCounties.contains(selectedCounty)) selectedCounty = null;
    bool isCheckingLocation = false;

    final result = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (ctx) {
        return StatefulBuilder(
          builder: (dialogCtx, setDialogState) {
            return Dialog(
              backgroundColor: const Color(0xFF303030),
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(20)),
              child: ConstrainedBox(
                constraints: BoxConstraints(
                    maxHeight: MediaQuery.of(dialogCtx).size.height * .82),
                child: SingleChildScrollView(
                  padding: const EdgeInsets.all(22),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Container(
                            width: 32,
                            height: 32,
                            decoration: BoxDecoration(
                              color: const Color(0xFFE5E5E5),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: const Icon(Icons.how_to_vote,
                                size: 18, color: Color(0xFF303030)),
                          ),
                          const SizedBox(width: 10),
                          const Expanded(
                            child: Text(
                              'Identity Verification',
                              style: TextStyle(
                                  color: Color(0xFFE5E5E5),
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      const Text('Full Name · as printed on ID',
                          style: TextStyle(
                              color: Color(0xFFE5E5E5),
                              fontSize: 12,
                              fontWeight: FontWeight.bold)),
                      const SizedBox(height: 6),
                      Container(
                        height: 48,
                        decoration: BoxDecoration(
                          color: const Color(0xFF404040),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: const Color(0xFF606060)),
                        ),
                        padding: const EdgeInsets.symmetric(horizontal: 14),
                        alignment: Alignment.center,
                        child: TextField(
                          controller: nameController,
                          textCapitalization: TextCapitalization.words,
                          style: const TextStyle(color: Color(0xFFE5E5E5)),
                          decoration: const InputDecoration(
                            hintText: '',
                            hintStyle: TextStyle(color: Color(0xFF888888)),
                            border: InputBorder.none,
                          ),
                        ),
                      ),
                      const SizedBox(height: 14),
                      const Text('National ID Number · 5–12 digits only',
                          style: TextStyle(
                              color: Color(0xFFE5E5E5),
                              fontSize: 12,
                              fontWeight: FontWeight.bold)),
                      const SizedBox(height: 6),
                      Container(
                        height: 48,
                        padding: const EdgeInsets.symmetric(horizontal: 14),
                        decoration: BoxDecoration(
                          color: const Color(0xFF404040),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: const Color(0xFF606060)),
                        ),
                        child: TextField(
                          controller: idController,
                          keyboardType: TextInputType.number,
                          inputFormatters: [
                            FilteringTextInputFormatter.digitsOnly,
                            LengthLimitingTextInputFormatter(12),
                          ],
                          style: const TextStyle(color: Color(0xFFE5E5E5)),
                          decoration: const InputDecoration(
                            hintText: 'Enter 5–12 digits',
                            hintStyle: TextStyle(color: Color(0xFF888888)),
                            border: InputBorder.none,
                          ),
                        ),
                      ),
                      const SizedBox(height: 14),
                      const Text('County · choose one',
                          style: TextStyle(
                              color: Color(0xFFE5E5E5),
                              fontSize: 12,
                              fontWeight: FontWeight.bold)),
                      const SizedBox(height: 6),
                      Container(
                        height: 48,
                        padding: const EdgeInsets.symmetric(horizontal: 14),
                        decoration: BoxDecoration(
                          color: const Color(0xFF404040),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: const Color(0xFF606060)),
                        ),
                        child: DropdownButtonHideUnderline(
                          child: DropdownButton<String>(
                            value: selectedCounty,
                            hint: const Text('Choose your county',
                                style: TextStyle(color: Color(0xFF888888))),
                            dropdownColor: const Color(0xFF404040),
                            isExpanded: true,
                            style: const TextStyle(
                                color: Color(0xFFE5E5E5),
                                fontSize: 13,
                                fontWeight: FontWeight.bold),
                            items: _kenyaCounties
                                .map((c) => DropdownMenuItem(
                                    value: c, child: Text('$c County')))
                                .toList(),
                            onChanged: (val) {
                              setDialogState(() => selectedCounty = val);
                            },
                          ),
                        ),
                      ),
                      const SizedBox(height: 14),
                      const Text('Date of Birth · YYYY-MM-DD',
                          style: TextStyle(
                              color: Color(0xFFE5E5E5),
                              fontSize: 12,
                              fontWeight: FontWeight.bold)),
                      const SizedBox(height: 6),
                      InkWell(
                        onTap: () => _pickDobForPolls(
                            dialogCtx, dobController, setDialogState),
                        borderRadius: BorderRadius.circular(12),
                        child: Container(
                          height: 48,
                          padding: const EdgeInsets.symmetric(horizontal: 14),
                          decoration: BoxDecoration(
                            color: const Color(0xFF404040),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: const Color(0xFF606060)),
                          ),
                          child: Row(
                            children: [
                              const Icon(Icons.calendar_today_outlined,
                                  color: Color(0xFFB8BAC0), size: 18),
                              const SizedBox(width: 10),
                              Expanded(
                                child: Text(
                                  dobController.text.isEmpty
                                      ? 'Select date'
                                      : dobController.text,
                                  style: TextStyle(
                                    color: dobController.text.isEmpty
                                        ? const Color(0xFF888888)
                                        : const Color(0xFFE5E5E5),
                                    fontSize: 13,
                                    fontWeight: dobController.text.isEmpty
                                        ? FontWeight.normal
                                        : FontWeight.w600,
                                  ),
                                ),
                              ),
                              const Icon(Icons.calendar_month,
                                  color: Color(0xFFE5E5E5), size: 22),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 18),
                      Row(
                        children: [
                          Expanded(
                            child: TextButton(
                              onPressed: () => Navigator.pop(ctx, false),
                              child: const Text('Cancel',
                                  style: TextStyle(
                                      color: Color(0xFFB8B8B8),
                                      fontWeight: FontWeight.bold)),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            flex: 2,
                            child: ElevatedButton(
                              style: ElevatedButton.styleFrom(
                                backgroundColor: const Color(0xFFE5E5E5),
                                foregroundColor: const Color(0xFF2A2A2A),
                                shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(12)),
                                padding:
                                    const EdgeInsets.symmetric(vertical: 12),
                              ),
                              onPressed: isCheckingLocation
                                  ? null
                                  : () async {
                                      final dob = dobController.text.trim();
                                      final voterName =
                                          nameController.text.trim();
                                      final voterIdNumber =
                                          idController.text.trim();
                                      if (voterName.length < 3 ||
                                          !RegExp(r'^\d{5,12}$')
                                              .hasMatch(voterIdNumber) ||
                                          selectedCounty == null ||
                                          dob.isEmpty) {
                                        ScaffoldMessenger.of(context)
                                            .showSnackBar(
                                          const SnackBar(
                                              content: Text(
                                                  'Please provide correct details: full name, 5–12 digit National ID, county, and date of birth are required.')),
                                        );
                                        return;
                                      }
                                      final birthDate = DateTime.tryParse(dob);
                                      final today = DateTime.now();
                                      var age = birthDate == null
                                          ? -1
                                          : today.year - birthDate.year;
                                      if (birthDate != null &&
                                          (today.month < birthDate.month ||
                                              (today.month == birthDate.month &&
                                                  today.day < birthDate.day))) {
                                        age--;
                                      }
                                      if (birthDate == null ||
                                          birthDate.isAfter(today) ||
                                          age < 18) {
                                        ScaffoldMessenger.of(context)
                                            .showSnackBar(
                                          const SnackBar(
                                              content: Text(
                                                  'Please provide correct details: enter a valid date of birth.')),
                                        );
                                        return;
                                      }
                                      setDialogState(
                                          () => isCheckingLocation = true);
                                      final location =
                                          await PreciseLocation.acquire();
                                      if (!location.succeeded) {
                                        setDialogState(
                                            () => isCheckingLocation = false);
                                        ScaffoldMessenger.of(context)
                                            .showSnackBar(
                                          const SnackBar(
                                              content: Text(
                                                  'Precise location is needed to verify your selected county.')),
                                        );
                                        if (location.issue != null &&
                                            context.mounted) {
                                          await PreciseLocation.promptSettings(
                                              context, location.issue!);
                                        }
                                        return;
                                      }
                                      final position = location.position!;
                                      await prefs.setString(
                                          'gir_voter_name', voterName);
                                      await prefs.setString(
                                          'gir_voter_id_number', voterIdNumber);
                                      await prefs.setString(
                                          'gir_user_national_id',
                                          voterIdNumber);
                                      await prefs.setString(
                                          'gir_user_county', selectedCounty!);
                                      await prefs.setString(
                                          'gir_county', selectedCounty!);
                                      await prefs.setString('gir_v_dob', dob);
                                      await prefs.setDouble(
                                          'gir_latitude', position.latitude);
                                      await prefs.setDouble(
                                          'gir_longitude', position.longitude);
                                      await prefs.setDouble(
                                          'gir_location_accuracy',
                                          position.accuracy);
                                      await prefs.setString('gir_gps',
                                          '${position.latitude},${position.longitude}');
                                      await prefs.setBool(
                                          'gir_voter_verified', true);
                                      if (!ctx.mounted) return;
                                      Navigator.pop(ctx, true);
                                    },
                              child: isCheckingLocation
                                  ? const SizedBox(
                                      width: 18,
                                      height: 18,
                                      child: CircularProgressIndicator(
                                          strokeWidth: 2))
                                  : const Text('Confirm & Vote',
                                      style: TextStyle(
                                          fontWeight: FontWeight.bold,
                                          fontSize: 13)),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            );
          },
        );
      },
    );

    nameController.dispose();
    idController.dispose();
    dobController.dispose();
    return result ?? false;
  }

  Future<void> _handleVote(Poll poll, String optionId,
      {int? optionIndex}) async {
    final prefs = await SharedPreferences.getInstance();
    var savedDob =
        prefs.getString('gir_v_dob') ?? prefs.getString('gir_user_dob');
    var savedCounty =
        prefs.getString('gir_user_county') ?? prefs.getString('gir_county');
    var savedName =
        prefs.getString('gir_voter_name') ?? prefs.getString('gir_user_name');
    var savedId = prefs.getString('gir_voter_id_number') ??
        prefs.getString('gir_user_national_id');
    final savedIdBeforePrompt = savedId;

    final hasAccountSession = (prefs.getString('gir_token') ?? '').isNotEmpty;
    final voterKey =
        hasAccountSession ? null : await _apiClient.getOrCreateVoterKey();
    final priorVote = await _apiClient.getVoteStatus(
      poll.id,
      savedId ?? '',
      voterKey: voterKey,
    );
    if (priorVote == null) {
      _showVoteError(
          'Unable to check your ballot history. Check your connection and try again.');
      return;
    }
    if (priorVote['error'] != null) {
      _showVoteError(priorVote['error'].toString());
      return;
    }
    if (priorVote['hasVoted'] == true) {
      final savedOptionId = _optionIdForStatus(poll, priorVote);
      await _cacheAccountVote(poll, prefs, optionId: savedOptionId);
      if (mounted) {
        setState(() => poll.selectedOptionId = savedOptionId ?? '__voted__');
      }
      return;
    }
    if (priorVote['hasVoted'] != false) {
      _showVoteError(
          'Unable to confirm your ballot status. Check your connection and try again.');
      return;
    }

    if (savedDob == null ||
        savedDob.isEmpty ||
        savedCounty == null ||
        savedCounty.isEmpty ||
        savedName == null ||
        savedName.trim().length < 3 ||
        savedId == null ||
        !RegExp(r'^\d{5,12}$').hasMatch(savedId)) {
      if (!mounted) return;
      final verified = await _showVoterDemographicsDialog(context);
      if (!verified) return;
      savedDob = prefs.getString('gir_v_dob');
      savedCounty = prefs.getString('gir_user_county');
      savedName = prefs.getString('gir_voter_name');
      savedId = prefs.getString('gir_voter_id_number');
    }

    if (savedDob == null ||
        savedCounty == null ||
        savedName == null ||
        savedId == null) return;

    if (savedId != savedIdBeforePrompt) {
      final identityStatus = await _apiClient.getVoteStatus(
        poll.id,
        savedId,
        voterKey: hasAccountSession ? null : voterKey,
      );
      if (identityStatus == null || identityStatus['error'] != null) {
        _showVoteError(identityStatus?['error']?.toString() ??
            'Unable to check your ballot history. Check your connection and try again.');
        return;
      }
      if (identityStatus['hasVoted'] == true) {
        final savedOptionId = _optionIdForStatus(poll, identityStatus);
        await _cacheAccountVote(poll, prefs, optionId: savedOptionId);
        if (mounted) {
          setState(() => poll.selectedOptionId = savedOptionId ?? '__voted__');
        }
        return;
      }
      if (identityStatus['hasVoted'] != false) {
        _showVoteError(
            'Unable to confirm your ballot status. Check your connection and try again.');
        return;
      }
    }

    final location = await PreciseLocation.acquire();
    if (!location.succeeded) {
      _showVoteError(
          'Precise location is needed to verify your selected county.');
      if (location.issue != null && mounted) {
        await PreciseLocation.promptSettings(context, location.issue!);
      }
      return;
    }
    final position = location.position!;

    final result = await _apiClient.castVote(
      poll.id,
      optionId,
      optionIndex: optionIndex,
      county: savedCounty,
      dob: savedDob,
      voterName: savedName,
      voterIdNumber: savedId,
      latitude: position.latitude,
      longitude: position.longitude,
      accuracy: position.accuracy,
    );
    if (result['success'] != true) {
      if (result['alreadyVoted'] == true) {
        // A vote from another device may win after the status check. Refresh
        // the committed ballot so the badge and selected option match the DB.
        final duplicateStatus = await _apiClient.getVoteStatus(
          poll.id,
          savedId,
          voterKey: voterKey,
        );
        final savedOptionId = duplicateStatus?['hasVoted'] == true
            ? _optionIdForStatus(poll, duplicateStatus)
            : null;
        await _cacheAccountVote(poll, prefs, optionId: savedOptionId);
        if (mounted) {
          setState(() => poll.selectedOptionId = savedOptionId ?? '__voted__');
          _showVoteError('This poll already has a recorded vote.');
        }
        return;
      }
      _showVoteError(result['error']?.toString() ??
          'Please provide correct details and try again.');
      return;
    }

    await _cacheAccountVote(poll, prefs, optionId: optionId);
    await prefs.setDouble('gir_latitude', position.latitude);
    await prefs.setDouble('gir_longitude', position.longitude);
    await prefs.setDouble('gir_location_accuracy', position.accuracy);

    setState(() {
      poll.selectedOptionId = optionId;
      final serverTotal = result['totalVotes'];
      poll.totalVotes =
          serverTotal is num ? serverTotal.toInt() : poll.totalVotes + 1;
      for (var opt in poll.options) {
        if (opt.id == optionId) {
          opt.votes += 1;
        }
        opt.percentage =
            poll.totalVotes > 0 ? (opt.votes / poll.totalVotes) * 100.0 : 0.0;
      }
    });

    if (mounted) {
      ScaffoldMessenger.of(context).hideCurrentSnackBar();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Row(
            children: [
              Icon(Icons.check_circle, color: Color(0xFF2A2A2A), size: 18),
              SizedBox(width: 8),
              Expanded(
                child: Text(
                  'Vote recorded! (Votes cannot be changed)',
                  style: TextStyle(
                    color: Color(0xFF2A2A2A),
                    fontWeight: FontWeight.bold,
                    fontSize: 13,
                  ),
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

  void _showVoteError(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).hideCurrentSnackBar();
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: const Color(0xFFE5E5E5),
        duration: const Duration(seconds: 3),
      ),
    );
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

    // Show 5 in home, with ability to reveal next polls
    final displayedPolls = filteredPolls.take(_visibleCount).toList();
    final hasMorePolls = filteredPolls.length > _visibleCount;

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

                const SizedBox(height: 4),

                // Screen frame with CURVED EDGES OF ALL SIDES OF SCREEN
                // Inside: NO CARDS! Pure words and typography!
                Expanded(
                  child: Container(
                    margin: const EdgeInsets.fromLTRB(10, 4, 10, 10),
                    decoration: BoxDecoration(
                      color: const Color(0xFF262626),
                      borderRadius:
                          BorderRadius.circular(24), // Curved edges all sides
                      border: Border.all(
                        color: const Color(0xFF3E3E3E),
                        width: 1.2,
                      ),
                    ),
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(24),
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
                                      controller: scrollController,
                                      physics:
                                          const AlwaysScrollableScrollPhysics(),
                                      children: const [
                                        SizedBox(height: 120),
                                        Center(
                                          child: Text(
                                            'No polls available',
                                            style: TextStyle(
                                                color: Color(0xFFB8B8B8)),
                                          ),
                                        ),
                                      ],
                                    )
                                  : ListView.builder(
                                      controller: scrollController,
                                      physics:
                                          const AlwaysScrollableScrollPhysics(),
                                      padding: const EdgeInsets.symmetric(
                                          horizontal: 16, vertical: 14),
                                      // Displayed polls + optional "Next Poll" words button
                                      itemCount: displayedPolls.length +
                                          (hasMorePolls ||
                                                  (_visibleCount > 5 &&
                                                      filteredPolls.length > 5)
                                              ? 1
                                              : 0),
                                      itemBuilder: (context, index) {
                                        // "Next Poll" underlined link at bottom of 5 polls
                                        if (index >= displayedPolls.length) {
                                          if (hasMorePolls) {
                                            final remaining =
                                                filteredPolls.length -
                                                    displayedPolls.length;
                                            return InkWell(
                                              onTap: () {
                                                setState(() {
                                                  _visibleCount += 5;
                                                });
                                              },
                                              child: Padding(
                                                padding:
                                                    const EdgeInsets.symmetric(
                                                        vertical: 24,
                                                        horizontal: 16),
                                                child: Center(
                                                  child: Column(
                                                    mainAxisSize:
                                                        MainAxisSize.min,
                                                    children: [
                                                      Text(
                                                        'Next Poll ($remaining remaining) →',
                                                        style: const TextStyle(
                                                          color:
                                                              Color(0xFF64B5F6),
                                                          fontSize: 16,
                                                          fontWeight:
                                                              FontWeight.bold,
                                                          decoration:
                                                              TextDecoration
                                                                  .underline,
                                                          decorationColor:
                                                              Color(0xFF64B5F6),
                                                          decorationThickness:
                                                              2.0,
                                                          letterSpacing: 0.5,
                                                        ),
                                                      ),
                                                      const SizedBox(height: 6),
                                                      const Text(
                                                        'Tap to view next available poll',
                                                        style: TextStyle(
                                                          color:
                                                              Color(0xFF9E9E9E),
                                                          fontSize: 12,
                                                        ),
                                                      ),
                                                    ],
                                                  ),
                                                ),
                                              ),
                                            );
                                          } else {
                                            // Option to collapse back to 5
                                            return InkWell(
                                              onTap: () {
                                                setState(() {
                                                  _visibleCount = 5;
                                                });
                                                scrollToTop();
                                              },
                                              child: const Padding(
                                                padding: EdgeInsets.symmetric(
                                                    vertical: 20),
                                                child: Center(
                                                  child: Text(
                                                    'Show 5 in Home ↑',
                                                    style: TextStyle(
                                                      color: Color(0xFF64B5F6),
                                                      fontSize: 14,
                                                      fontWeight:
                                                          FontWeight.bold,
                                                      decoration: TextDecoration
                                                          .underline,
                                                      decorationColor:
                                                          Color(0xFF64B5F6),
                                                    ),
                                                  ),
                                                ),
                                              ),
                                            );
                                          }
                                        }

                                        final poll = displayedPolls[index];
                                        final isZak = _isZakSyengoPoll(poll);
                                        final shareUrl =
                                            _apiClient.generateShareLink(
                                                type: 'poll', id: poll.id);

                                        // NOT A CARD: Pure words and typography layout!
                                        return Padding(
                                          padding: const EdgeInsets.symmetric(
                                              vertical: 12),
                                          child: Column(
                                            crossAxisAlignment:
                                                CrossAxisAlignment.start,
                                            children: [
                                              // Header Text Words & Status
                                              Row(
                                                mainAxisAlignment:
                                                    MainAxisAlignment
                                                        .spaceBetween,
                                                children: [
                                                  Row(
                                                    children: [
                                                      if (isZak) ...[
                                                        const Text(
                                                          'FEATURED • ',
                                                          style: TextStyle(
                                                            color: Color(
                                                                0xFFE5E5E5),
                                                            fontSize: 11,
                                                            fontWeight:
                                                                FontWeight.w900,
                                                            letterSpacing: 0.8,
                                                          ),
                                                        ),
                                                      ],
                                                      Text(
                                                        poll.trackName
                                                            .toUpperCase(),
                                                        style: const TextStyle(
                                                          color:
                                                              Color(0xFFB0B0B0),
                                                          fontSize: 11,
                                                          fontWeight:
                                                              FontWeight.bold,
                                                          letterSpacing: 0.8,
                                                        ),
                                                      ),
                                                    ],
                                                  ),
                                                  Row(
                                                    children: [
                                                      if (poll.selectedOptionId !=
                                                          null) ...[
                                                        Container(
                                                          padding:
                                                              const EdgeInsets
                                                                  .symmetric(
                                                                  horizontal: 9,
                                                                  vertical: 5),
                                                          decoration:
                                                              BoxDecoration(
                                                            color: const Color(
                                                                0xFFF2F2F3),
                                                            borderRadius:
                                                                BorderRadius
                                                                    .circular(
                                                                        30),
                                                          ),
                                                          child: const Row(
                                                            mainAxisSize:
                                                                MainAxisSize
                                                                    .min,
                                                            children: [
                                                              Icon(Icons.check,
                                                                  size: 12,
                                                                  color: Color(
                                                                      0xFF2E3035)),
                                                              SizedBox(
                                                                  width: 4),
                                                              Text(
                                                                'VOTED',
                                                                style:
                                                                    TextStyle(
                                                                  color: Color(
                                                                      0xFF2E3035),
                                                                  fontSize: 9,
                                                                  fontWeight:
                                                                      FontWeight
                                                                          .w900,
                                                                  letterSpacing:
                                                                      0.6,
                                                                ),
                                                              ),
                                                            ],
                                                          ),
                                                        ),
                                                        const SizedBox(
                                                            width: 8),
                                                      ],
                                                      InkWell(
                                                        onTap: () =>
                                                            _sharePoll(poll),
                                                        child: const Row(
                                                          children: [
                                                            Icon(Icons.share,
                                                                size: 12,
                                                                color: Colors
                                                                    .white70),
                                                            SizedBox(width: 4),
                                                            Text(
                                                              'Share',
                                                              style: TextStyle(
                                                                color: Colors
                                                                    .white70,
                                                                fontSize: 11,
                                                                fontWeight:
                                                                    FontWeight
                                                                        .bold,
                                                              ),
                                                            ),
                                                          ],
                                                        ),
                                                      ),
                                                    ],
                                                  ),
                                                ],
                                              ),
                                              const SizedBox(height: 8),

                                              // Poll Question Title (Pure words, bold and clear)
                                              Text(
                                                poll.title,
                                                style: const TextStyle(
                                                  color: Colors.white,
                                                  fontSize: 17,
                                                  fontWeight: FontWeight.w800,
                                                  height: 1.3,
                                                ),
                                              ),

                                              // Description Words
                                              if (poll
                                                  .description.isNotEmpty) ...[
                                                const SizedBox(height: 5),
                                                Text(
                                                  poll.description,
                                                  style: const TextStyle(
                                                    color: Color(0xFFB8B8B8),
                                                    fontSize: 12.5,
                                                    height: 1.35,
                                                  ),
                                                ),
                                              ],

                                              const SizedBox(height: 14),

                                              // Interactive Pie Chart Breakdown
                                              InteractivePieChartWidget(
                                                  key: ValueKey(
                                                      '${poll.id}:${poll.selectedOptionId ?? ''}'),
                                                  poll: poll),

                                              const SizedBox(height: 14),

                                              // Candidate Options — PURE WORDS! NOT IN A CARD!
                                              ...poll.options
                                                  .asMap()
                                                  .entries
                                                  .map((entry) {
                                                final i = entry.key;
                                                final opt = entry.value;
                                                final isSelected =
                                                    poll.selectedOptionId ==
                                                        opt.id;
                                                final sliceColor =
                                                    InteractivePieChartWidget
                                                            .sliceColors[
                                                        i %
                                                            InteractivePieChartWidget
                                                                .sliceColors
                                                                .length];

                                                return InkWell(
                                                  onTap:
                                                      poll.selectedOptionId ==
                                                              null
                                                          ? () => _handleVote(
                                                              poll, opt.id,
                                                              optionIndex: i)
                                                          : null,
                                                  borderRadius:
                                                      BorderRadius.circular(8),
                                                  child: Padding(
                                                    padding: const EdgeInsets
                                                        .symmetric(
                                                        vertical: 8,
                                                        horizontal: 2),
                                                    child: Row(
                                                      crossAxisAlignment:
                                                          CrossAxisAlignment
                                                              .center,
                                                      children: [
                                                        // Selection indicator circle / checkmark
                                                        Container(
                                                          width: 18,
                                                          height: 18,
                                                          decoration:
                                                              BoxDecoration(
                                                            color: isSelected
                                                                ? sliceColor
                                                                : Colors
                                                                    .transparent,
                                                            shape:
                                                                BoxShape.circle,
                                                            border: Border.all(
                                                              color: isSelected
                                                                  ? sliceColor
                                                                  : sliceColor
                                                                      .withOpacity(
                                                                          0.6),
                                                              width: 1.8,
                                                            ),
                                                          ),
                                                          child: isSelected
                                                              ? const Icon(
                                                                  Icons.check,
                                                                  size: 12,
                                                                  color: Color(
                                                                      0xFF1E1E1E))
                                                              : null,
                                                        ),
                                                        const SizedBox(
                                                            width: 12),

                                                        // Candidate name words
                                                        Expanded(
                                                          child: Text(
                                                            opt.text,
                                                            style: TextStyle(
                                                              color: isSelected
                                                                  ? Colors.white
                                                                  : const Color(
                                                                      0xFFECECEC),
                                                              fontSize: 14,
                                                              fontWeight: isSelected
                                                                  ? FontWeight
                                                                      .bold
                                                                  : FontWeight
                                                                      .w500,
                                                              height: 1.3,
                                                            ),
                                                          ),
                                                        ),

                                                        const SizedBox(
                                                            width: 8),

                                                        // Votes & percentage words
                                                        Text(
                                                          '${opt.votes} votes (${opt.percentage.toStringAsFixed(1)}%)',
                                                          style: TextStyle(
                                                            color: sliceColor,
                                                            fontSize: 12,
                                                            fontWeight:
                                                                FontWeight.bold,
                                                          ),
                                                        ),
                                                      ],
                                                    ),
                                                  ),
                                                );
                                              }),

                                              const SizedBox(height: 10),

                                              // CLICKABLE SHARED LINK (Directly tappable on screen)
                                              InkWell(
                                                onTap: () => _openUrl(shareUrl),
                                                child: Padding(
                                                  padding: const EdgeInsets
                                                      .symmetric(vertical: 4),
                                                  child: Row(
                                                    children: [
                                                      const Icon(Icons.link,
                                                          size: 14,
                                                          color: Color(
                                                              0xFF64B5F6)),
                                                      const SizedBox(width: 6),
                                                      Expanded(
                                                        child: Text(
                                                          shareUrl,
                                                          style:
                                                              const TextStyle(
                                                            color: Color(
                                                                0xFF64B5F6),
                                                            fontSize: 12,
                                                            fontWeight:
                                                                FontWeight.w600,
                                                            decoration:
                                                                TextDecoration
                                                                    .underline,
                                                            decorationColor:
                                                                Color(
                                                                    0xFF64B5F6),
                                                          ),
                                                          maxLines: 1,
                                                          overflow: TextOverflow
                                                              .ellipsis,
                                                        ),
                                                      ),
                                                      const SizedBox(width: 4),
                                                      const Icon(
                                                          Icons.open_in_new,
                                                          size: 13,
                                                          color: Color(
                                                              0xFF64B5F6)),
                                                    ],
                                                  ),
                                                ),
                                              ),

                                              const SizedBox(height: 8),

                                              // Total votes & countdown
                                              Row(
                                                mainAxisAlignment:
                                                    MainAxisAlignment
                                                        .spaceBetween,
                                                crossAxisAlignment:
                                                    CrossAxisAlignment.end,
                                                children: [
                                                  // Left column: total votes + countdown below
                                                  Column(
                                                    crossAxisAlignment:
                                                        CrossAxisAlignment
                                                            .start,
                                                    children: [
                                                      Text(
                                                        '${poll.totalVotes} total votes',
                                                        style: const TextStyle(
                                                          color:
                                                              Color(0xFFAAAAAA),
                                                          fontSize: 12,
                                                          fontWeight:
                                                              FontWeight.w500,
                                                        ),
                                                      ),
                                                      const SizedBox(height: 3),
                                                      Text(
                                                        _formatPollCountdown(
                                                            poll),
                                                        style: const TextStyle(
                                                          color:
                                                              Color(0xFFE5E5E5),
                                                          fontSize: 11,
                                                          fontWeight:
                                                              FontWeight.w700,
                                                          letterSpacing: 0.02,
                                                          fontFamily:
                                                              'monospace',
                                                        ),
                                                      ),
                                                    ],
                                                  ),
                                                  ElevatedButton.icon(
                                                    onPressed: () =>
                                                        _sharePoll(poll),
                                                    icon: const Icon(
                                                        Icons.share,
                                                        size: 13,
                                                        color:
                                                            Color(0xFF2A2A2A)),
                                                    label: const Text(
                                                      'Share Poll',
                                                      style: TextStyle(
                                                        color:
                                                            Color(0xFF2A2A2A),
                                                        fontWeight:
                                                            FontWeight.bold,
                                                        fontSize: 12,
                                                      ),
                                                    ),
                                                    style: ElevatedButton
                                                        .styleFrom(
                                                      backgroundColor:
                                                          const Color(
                                                              0xFFE5E5E5),
                                                      foregroundColor:
                                                          const Color(
                                                              0xFF2A2A2A),
                                                      padding: const EdgeInsets
                                                          .symmetric(
                                                          horizontal: 14,
                                                          vertical: 6),
                                                      minimumSize: Size.zero,
                                                      tapTargetSize:
                                                          MaterialTapTargetSize
                                                              .shrinkWrap,
                                                      shape:
                                                          RoundedRectangleBorder(
                                                        borderRadius:
                                                            BorderRadius
                                                                .circular(16),
                                                      ),
                                                      elevation: 0,
                                                    ),
                                                  ),
                                                ],
                                              ),

                                              const SizedBox(height: 14),
                                              // Subtle line divider between polls
                                              const Divider(
                                                  color: Color(0xFF383838),
                                                  height: 24,
                                                  thickness: 1.0),
                                            ],
                                          ),
                                        );
                                      },
                                    ),
                            ),
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
    _selectedIndex = _votedArrayIndex(widget.poll);
    _countdownTimer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (mounted) setState(() {});
    });
  }

  int? _votedArrayIndex(Poll poll) {
    final selectedOptionId = poll.selectedOptionId;
    if (selectedOptionId == null || selectedOptionId == '__voted__')
      return null;
    final index =
        poll.options.indexWhere((option) => option.id == selectedOptionId);
    return index < 0 ? null : index;
  }

  @override
  void didUpdateWidget(covariant InteractivePieChartWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.poll.id != widget.poll.id) {
      _selectedIndex = _votedArrayIndex(widget.poll);
    } else if (oldWidget.poll.selectedOptionId !=
        widget.poll.selectedOptionId) {
      _selectedIndex = _votedArrayIndex(widget.poll);
    }
  }

  @override
  void dispose() {
    _countdownTimer?.cancel();
    super.dispose();
  }

  String _formatMovingCountdown() {
    DateTime deadline;
    if (widget.poll.endDate != null) {
      deadline = widget.poll.endDate!;
    } else {
      deadline = widget.poll.createdAt.add(const Duration(days: 7));
    }
    final diff = deadline.difference(DateTime.now());
    if (diff.isNegative) {
      return 'Voting Closed';
    }
    final days = diff.inDays;
    final hours = diff.inHours % 24;
    final minutes = diff.inMinutes % 60;
    pad(int n) => n.toString().padLeft(2, '0');
    if (days >= 1) {
      return '${days}d ${hours}h ${pad(minutes)}mins left';
    } else {
      return '${hours}h ${pad(minutes)}mins left';
    }
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
              setState(() => _selectedIndex = _votedArrayIndex(widget.poll));
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
                final votedIndex = _votedArrayIndex(widget.poll);
                setState(() {
                  _selectedIndex =
                      _selectedIndex == i && votedIndex != i ? null : i;
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

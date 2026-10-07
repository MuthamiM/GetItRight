import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../../core/models/survey_model.dart';
import '../../../core/network/api_client.dart';

class SurveyDetailScreen extends StatefulWidget {
  final Survey survey;
  final String userId;

  const SurveyDetailScreen({
    super.key,
    required this.survey,
    required this.userId,
  });

  @override
  State<SurveyDetailScreen> createState() => _SurveyDetailScreenState();
}

class _SurveyDetailScreenState extends State<SurveyDetailScreen> {
  final ApiClient _apiClient = ApiClient();
  final Map<int, dynamic> _answers = {};
  final Map<int, TextEditingController> _textControllers = {};

  // Pre-verification state
  bool _isVerified = false;
  bool _isLoadingVerification = true;
  bool _isFlaggedCheat = false;
  final _dobController = TextEditingController();
  final _zipController = TextEditingController();
  String _selectedPlaceOfBirth = 'Voo / Kyamatu Ward';

  final List<String> _placesOfBirth = [
    'Voo / Kyamatu Ward',
    'Kyangwithya West Ward',
    'Township Ward (Kitui Central)',
    'Mutomo Ward',
    'Ikutha Ward',
    'Mwingi Central Ward',
    'Other County Ward',
  ];

  bool _isSubmitting = false;

  @override
  void initState() {
    super.initState();
    _checkInitialVerificationStatus();
    for (var q in widget.survey.questions) {
      if (q.questionType == 'text') {
        _textControllers[q.id] = TextEditingController();
      }
    }
  }

  Future<void> _checkInitialVerificationStatus() async {
    final prefs = await SharedPreferences.getInstance();
    final savedVerified = prefs.getBool('gir_voter_verified') ?? false;
    final savedDob = prefs.getString('gir_v_dob');

    // If user has verified once in the past, skip verification for all surveys
    if (savedVerified || savedDob != null) {
      if (mounted) {
        setState(() {
          _isVerified = true;
          _isLoadingVerification = false;
        });
      }
    } else {
      if (mounted) {
        setState(() {
          _isVerified = false;
          _isLoadingVerification = false;
        });
      }
    }
  }

  @override
  void dispose() {
    _dobController.dispose();
    _zipController.dispose();
    for (var controller in _textControllers.values) {
      controller.dispose();
    }
    super.dispose();
  }

  Future<void> _processPreVerification() async {
    final dob = _dobController.text.trim();
    final zip = _zipController.text.trim();

    if (dob.isEmpty || zip.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please complete all verification fields'),
          backgroundColor: Color(0xFF505050),
        ),
      );
      return;
    }

    // Normalize strings for comparison (remove spaces/dashes/slashes)
    final normDob = dob.replaceAll(RegExp(r'[\s\/\-]'), '').toLowerCase();
    final normZip = zip.replaceAll(RegExp(r'[\s\/\-]'), '').toLowerCase();

    final prefs = await SharedPreferences.getInstance();
    final savedDob = prefs.getString('gir_v_dob');
    final savedPlace = prefs.getString('gir_v_place');
    final savedZip = prefs.getString('gir_v_zip');

    if (savedDob != null && savedPlace != null && savedZip != null) {
      final normSavedDob = savedDob.replaceAll(RegExp(r'[\s\/\-]'), '').toLowerCase();
      final normSavedZip = savedZip.replaceAll(RegExp(r'[\s\/\-]'), '').toLowerCase();

      // Check for mismatch / cheating attempt
      if (normSavedDob != normDob ||
          savedPlace != _selectedPlaceOfBirth ||
          normSavedZip != normZip) {
        setState(() {
          _isFlaggedCheat = true;
        });
        return;
      }
    } else {
      // Save first verification record for new user
      await prefs.setString('gir_v_dob', dob);
      await prefs.setString('gir_v_place', _selectedPlaceOfBirth);
      await prefs.setString('gir_v_zip', zip);
      await prefs.setBool('gir_voter_verified', true);
    }

    setState(() {
      _isVerified = true;
    });
  }

  Future<void> _submitSurvey() async {
    // Collect text field answers
    for (var entry in _textControllers.entries) {
      if (entry.value.text.trim().isNotEmpty) {
        _answers[entry.key] = entry.value.text.trim();
      }
    }

    // Default auto-selection if no answers provided to ensure survey can be submitted
    if (_answers.isEmpty && widget.survey.questions.isNotEmpty) {
      for (var q in widget.survey.questions) {
        if (q.options.isNotEmpty) {
          _answers[q.id] = q.options.first;
        } else {
          _answers[q.id] = 'Verified Response';
        }
      }
    }

    // Ensure every question has an answer (fill missing with first option or placeholder)
    for (var q in widget.survey.questions) {
      if (!_answers.containsKey(q.id)) {
        if (q.options.isNotEmpty) {
          _answers[q.id] = q.options.first;
        } else {
          _answers[q.id] = 'No response';
        }
      }
    }

    setState(() => _isSubmitting = true);

    final formattedAnswers = _answers.entries.map((e) {
      return {
        'questionId': e.key,
        'answer': e.value,
      };
    }).toList();

    print('[SURVEY DETAIL] Submitting survey ${widget.survey.id} with ${formattedAnswers.length} answers');
    print('[SURVEY DETAIL] Formatted answers: $formattedAnswers');

    try {
      final result = await _apiClient.submitSurveyResponse(
        surveyId: widget.survey.id,
        answers: formattedAnswers,
        voterPseudonym: 'User_${widget.userId}',
      );

      print('[SURVEY DETAIL] Submit result: $result');

      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('gir_survey_completed_time_${widget.survey.id}', DateTime.now().toIso8601String());

      setState(() => _isSubmitting = false);

      if (!mounted) return;

      showDialog(
        context: context,
        builder: (context) => AlertDialog(
          backgroundColor: const Color(0xFF424242),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
          title: const Row(
            children: [
              Icon(Icons.check_circle, color: Colors.white, size: 24),
              SizedBox(width: 10),
              Text('Survey Complete', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
            ],
          ),
          content: const Text(
            'Your survey responses have been submitted successfully.',
            style: TextStyle(color: Color(0xFFD0D0D0), fontSize: 14),
          ),
          actions: [
            ElevatedButton(
              onPressed: () {
                Navigator.of(context).pop();
                Navigator.of(context).pop();
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFFE5E5E5),
                foregroundColor: const Color(0xFF2A2A2A),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              ),
              child: const Text('Done', style: TextStyle(fontWeight: FontWeight.bold)),
            ),
          ],
        ),
      );
    } catch (e) {
      print('[SURVEY DETAIL] Submit error: $e');
      setState(() => _isSubmitting = false);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Submission failed: $e'),
          backgroundColor: const Color(0xFF505050),
          duration: const Duration(seconds: 4),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF303030),
      appBar: AppBar(
        backgroundColor: const Color(0xFF303030),
        elevation: 0,
        title: Text(
          widget.survey.title,
          style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16),
        ),
        centerTitle: true,
      ),
      body: SafeArea(
        child: _isLoadingVerification
            ? const Center(
                child: CircularProgressIndicator(
                  color: Colors.white,
                  strokeWidth: 2,
                ),
              )
            : (_isFlaggedCheat
                ? _buildNoSurveysAvailableView()
                : (!_isVerified ? _buildPreVerificationView() : _buildSurveyQuestionsView())),
      ),
    );
  }

  Widget _buildNoSurveysAvailableView() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 80,
              height: 80,
              decoration: const BoxDecoration(
                color: Color(0xFF424242),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.assignment_late_outlined, size: 42, color: Color(0xFFB8B8B8)),
            ),
            const SizedBox(height: 20),
            const Text(
              'No Surveys Available',
              style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 10),
            const Text(
              'There are no surveys available for you at the moment. Please try again later.',
              textAlign: TextAlign.center,
              style: TextStyle(color: Color(0xFFB8B8B8), fontSize: 14),
            ),
            const SizedBox(height: 28),
            ElevatedButton(
              onPressed: () => Navigator.of(context).pop(),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFFE5E5E5),
                foregroundColor: const Color(0xFF2A2A2A),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
              ),
              child: const Text('Back to Surveys', style: TextStyle(fontWeight: FontWeight.bold)),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPreVerificationView() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(
              color: const Color(0xFF424242),
              borderRadius: BorderRadius.circular(18),
              border: Border.all(color: const Color(0xFF555555)),
            ),
            child: const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Voter Identity Verification',
                  style: TextStyle(color: Colors.white, fontSize: 17, fontWeight: FontWeight.bold),
                ),
                SizedBox(height: 6),
                Text(
                  'Please confirm your voter details before answering this survey.',
                  style: TextStyle(color: Color(0xFFB8B8B8), fontSize: 13),
                ),
              ],
            ),
          ),

          const SizedBox(height: 24),

          const Text('Date of Birth (DD/MM/YYYY)', style: TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.w600)),
          const SizedBox(height: 6),
          _buildPillInput(controller: _dobController, hint: 'e.g. 15/08/1992'),

          const SizedBox(height: 16),

          const Text('Place of Birth / Sub-County Ward', style: TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.w600)),
          const SizedBox(height: 6),

          // Dropdown Input Field
          Container(
            height: 50,
            padding: const EdgeInsets.symmetric(horizontal: 20),
            decoration: BoxDecoration(
              color: const Color(0xFF505050),
              borderRadius: BorderRadius.circular(25),
            ),
            child: DropdownButtonHideUnderline(
              child: DropdownButton<String>(
                value: _selectedPlaceOfBirth,
                dropdownColor: const Color(0xFF505050),
                isExpanded: true,
                icon: const Icon(Icons.arrow_drop_down, color: Colors.white),
                items: _placesOfBirth.map((place) {
                  return DropdownMenuItem(
                    value: place,
                    child: Text(place, style: const TextStyle(color: Colors.white, fontSize: 14)),
                  );
                }).toList(),
                onChanged: (val) {
                  if (val != null) setState(() => _selectedPlaceOfBirth = val);
                },
              ),
            ),
          ),

          const SizedBox(height: 16),

          const Text('Postal / Zip Code', style: TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.w600)),
          const SizedBox(height: 6),
          _buildPillInput(controller: _zipController, hint: 'e.g. 90200', keyboardType: TextInputType.number),

          const SizedBox(height: 32),

          SizedBox(
            width: double.infinity,
            height: 50,
            child: ElevatedButton(
              onPressed: _processPreVerification,
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFFE5E5E5),
                foregroundColor: const Color(0xFF2A2A2A),
                elevation: 0,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(25)),
              ),
              child: const Text('Verify & Continue', style: TextStyle(color: Color(0xFF2A2A2A), fontSize: 15, fontWeight: FontWeight.bold)),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSurveyQuestionsView() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          ...widget.survey.questions.map((q) => _buildQuestionCard(q)),

          const SizedBox(height: 24),

          SizedBox(
            width: double.infinity,
            height: 50,
            child: ElevatedButton(
              onPressed: _isSubmitting ? null : _submitSurvey,
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFFE5E5E5),
                foregroundColor: const Color(0xFF2A2A2A),
                elevation: 0,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(25)),
              ),
              child: _isSubmitting
                  ? const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(color: Colors.black, strokeWidth: 2.5))
                  : const Text('Submit Survey Answers', style: TextStyle(color: Color(0xFF2A2A2A), fontSize: 15, fontWeight: FontWeight.bold)),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildQuestionCard(SurveyQuestion q) {
    return Container(
      margin: const EdgeInsets.only(bottom: 18),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFF424242),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFF555555)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Q${q.index + 1}. ${q.questionText}',
            style: const TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 14),

          if (q.options.isNotEmpty) ...[
            if (q.questionType == 'dropdown' || q.options.length > 3) ...[
              // Dropdown Input Field for multiple options
              Container(
                height: 50,
                padding: const EdgeInsets.symmetric(horizontal: 18),
                decoration: BoxDecoration(
                  color: const Color(0xFF505050),
                  borderRadius: BorderRadius.circular(25),
                  border: Border.all(color: const Color(0xFF666666)),
                ),
                child: DropdownButtonHideUnderline(
                  child: DropdownButton<String>(
                    value: _answers[q.id] as String?,
                    hint: const Text('Select an option...', style: TextStyle(color: Color(0xFFB8B8B8), fontSize: 14)),
                    dropdownColor: const Color(0xFF505050),
                    isExpanded: true,
                    icon: const Icon(Icons.arrow_drop_down, color: Colors.white),
                    items: q.options.map((opt) {
                      return DropdownMenuItem<String>(
                        value: opt,
                        child: Text(
                          opt,
                          style: const TextStyle(color: Colors.white, fontSize: 13),
                          overflow: TextOverflow.ellipsis,
                        ),
                      );
                    }).toList(),
                    onChanged: (val) {
                      if (val != null) setState(() => _answers[q.id] = val);
                    },
                  ),
                ),
              ),
            ] else if (q.questionType == 'rating' || q.questionType == 'rating_scale') ...[
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: q.options.map((opt) {
                  final isSelected = _answers[q.id] == opt;
                  return GestureDetector(
                    onTap: () => setState(() => _answers[q.id] = opt),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                      decoration: BoxDecoration(
                        color: isSelected ? const Color(0xFFE5E5E5) : const Color(0xFF505050),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        opt,
                        style: TextStyle(
                          color: isSelected ? const Color(0xFF2A2A2A) : Colors.white,
                          fontWeight: FontWeight.bold,
                          fontSize: 12,
                        ),
                      ),
                    ),
                  );
                }).toList(),
              ),
            ] else ...[
              ...q.options.map((opt) {
                final isSelected = _answers[q.id] == opt;
                return GestureDetector(
                  onTap: () => setState(() => _answers[q.id] = opt),
                  child: Container(
                    margin: const EdgeInsets.only(bottom: 8),
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    decoration: BoxDecoration(
                      color: isSelected ? const Color(0xFF606060) : const Color(0xFF505050),
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: isSelected ? Colors.white : Colors.transparent, width: isSelected ? 1.5 : 0),
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Expanded(child: Text(opt, style: const TextStyle(color: Colors.white, fontSize: 14))),
                        if (isSelected) const Icon(Icons.check, size: 18, color: Colors.white),
                      ],
                    ),
                  ),
                );
              }),
            ],
          ] else ...[
            _buildPillInput(
              controller: _textControllers[q.id] ??= TextEditingController(),
              hint: 'Enter your answer...',
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildPillInput({
    required TextEditingController controller,
    required String hint,
    TextInputType? keyboardType,
  }) {
    return Container(
      height: 50,
      decoration: BoxDecoration(
        color: const Color(0xFF505050),
        borderRadius: BorderRadius.circular(25),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 20),
      alignment: Alignment.centerLeft,
      child: TextField(
        controller: controller,
        keyboardType: keyboardType,
        style: const TextStyle(color: Colors.white, fontSize: 14),
        cursorColor: Colors.white,
        decoration: InputDecoration(
          hintText: hint,
          hintStyle: const TextStyle(color: Color(0xFFB8B8B8), fontSize: 14),
          border: InputBorder.none,
          enabledBorder: InputBorder.none,
          focusedBorder: InputBorder.none,
          contentPadding: EdgeInsets.zero,
          isDense: true,
        ),
      ),
    );
  }
}

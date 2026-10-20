import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../../core/location/precise_location.dart';
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
  final _voterNameController = TextEditingController();
  final _voterIdController = TextEditingController();
  String? _selectedCounty;
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
    'West Pokot',
  ];

  bool _isSubmitting = false;
  bool _alreadySubmitted = false;

  bool _isAdult(DateTime birthDate) {
    final today = DateTime.now();
    var age = today.year - birthDate.year;
    if (today.month < birthDate.month ||
        (today.month == birthDate.month && today.day < birthDate.day)) {
      age--;
    }
    return age >= 18;
  }

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
    final savedDob =
        prefs.getString('gir_v_dob') ?? prefs.getString('gir_user_dob');
    final savedName =
        prefs.getString('gir_voter_name') ?? prefs.getString('gir_user_name');
    final savedId = prefs.getString('gir_voter_id_number') ??
        prefs.getString('gir_user_national_id');
    final savedCounty =
        prefs.getString('gir_user_county') ?? prefs.getString('gir_county');
    _dobController.text = savedDob ?? '';
    _voterNameController.text = savedName ?? '';
    final sanitizedSavedId = (savedId ?? '').replaceAll(RegExp(r'\D'), '');
    _voterIdController.text = sanitizedSavedId.length > 12
        ? sanitizedSavedId.substring(0, 12)
        : sanitizedSavedId;
    _selectedCounty = _kenyaCounties.contains(savedCounty) ? savedCounty : null;

    // If user has verified once in the past, skip verification for all surveys
    if (savedVerified &&
        savedDob != null &&
        savedName != null &&
        savedId != null &&
        RegExp(r'^\d{5,12}$').hasMatch(savedId) &&
        _selectedCounty != null) {
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
    _voterNameController.dispose();
    _voterIdController.dispose();
    for (var controller in _textControllers.values) {
      controller.dispose();
    }
    super.dispose();
  }

  Future<void> _pickDob() async {
    final now = DateTime.now();
    DateTime initial = DateTime(now.year - 20, now.month, now.day);
    if (_dobController.text.trim().isNotEmpty) {
      try {
        final parsed = DateTime.parse(_dobController.text.trim());
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
      setState(() {
        _dobController.text = formatted;
      });
    }
  }

  Future<void> _processPreVerification() async {
    final dob = _dobController.text.trim();
    final voterName = _voterNameController.text.trim();
    final voterIdNumber = _voterIdController.text.trim();

    if (dob.isEmpty ||
        voterName.length < 3 ||
        !RegExp(r'^\d{5,12}$').hasMatch(voterIdNumber) ||
        _selectedCounty == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
              'Please provide correct details: full name, 5–12 digit National ID, county, and date of birth are required.'),
          backgroundColor: Color(0xFF505050),
        ),
      );
      return;
    }
    final birthDate = DateTime.tryParse(dob);
    if (birthDate == null ||
        birthDate.isAfter(DateTime.now()) ||
        !_isAdult(birthDate)) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content: Text(
                'Please provide correct details: enter a valid date of birth.')),
      );
      return;
    }

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Checking precise device location...')),
    );
    final location = await PreciseLocation.acquire();
    if (!location.succeeded) {
      ScaffoldMessenger.of(context).hideCurrentSnackBar();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content: Text(
                'Precise location is needed to verify your selected county.')),
      );
      if (location.issue != null && mounted) {
        await PreciseLocation.promptSettings(context, location.issue!);
      }
      return;
    }
    final position = location.position!;

    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('gir_voter_name', voterName);
    await prefs.setString('gir_user_name', voterName);
    await prefs.setString('gir_voter_id_number', voterIdNumber);
    await prefs.setString('gir_user_national_id', voterIdNumber);
    await prefs.setString('gir_user_county', _selectedCounty!);
    await prefs.setString('gir_county', _selectedCounty!);
    await prefs.setString('gir_v_dob', dob);
    await prefs.setString('gir_user_dob', dob);
    await prefs.setDouble('gir_latitude', position.latitude);
    await prefs.setDouble('gir_longitude', position.longitude);
    await prefs.setDouble('gir_location_accuracy', position.accuracy);
    await prefs.setString(
        'gir_gps', '${position.latitude},${position.longitude}');
    await prefs.setBool('gir_voter_verified', true);

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

    final missingAnswers = widget.survey.questions.any((q) {
      final answer = _answers[q.id];
      return answer == null || answer.toString().trim().isEmpty;
    });
    if (missingAnswers) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content:
                Text('Please answer every survey question before submitting.')),
      );
      return;
    }

    final prefs = await SharedPreferences.getInstance();
    final voterName = prefs.getString('gir_voter_name') ??
        prefs.getString('gir_user_name') ??
        '';
    final voterIdNumber = prefs.getString('gir_voter_id_number') ??
        prefs.getString('gir_user_national_id') ??
        '';
    final county = prefs.getString('gir_user_county') ??
        prefs.getString('gir_county') ??
        '';
    final dob =
        prefs.getString('gir_v_dob') ?? prefs.getString('gir_user_dob') ?? '';
    if (voterName.trim().length < 3 ||
        !RegExp(r'^\d{5,12}$').hasMatch(voterIdNumber) ||
        !_kenyaCounties.contains(county) ||
        dob.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content: Text('Please provide correct details before submitting.')),
      );
      setState(() => _isVerified = false);
      return;
    }
    final birthDate = DateTime.tryParse(dob);
    if (birthDate == null ||
        birthDate.isAfter(DateTime.now()) ||
        !_isAdult(birthDate)) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content: Text(
                'Please provide correct details: enter a valid date of birth.')),
      );
      return;
    }
    setState(() => _isSubmitting = true);
    final location = await PreciseLocation.acquire();
    if (!location.succeeded) {
      setState(() => _isSubmitting = false);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content: Text(
                'Precise location is needed to verify your selected county.')),
      );
      if (location.issue != null && mounted) {
        await PreciseLocation.promptSettings(context, location.issue!);
      }
      return;
    }
    final position = location.position!;

    final formattedAnswers = _answers.entries.map((e) {
      return {
        'questionId': e.key,
        'answer': e.value,
      };
    }).toList();

    debugPrint(
        '[SURVEY DETAIL] Submitting survey ${widget.survey.id} with ${formattedAnswers.length} answers');

    try {
      final result = await _apiClient.submitSurveyResponse(
        surveyId: widget.survey.id,
        answers: formattedAnswers,
        voterName: voterName,
        voterIdNumber: voterIdNumber,
        county: county,
        dob: dob,
        latitude: position.latitude,
        longitude: position.longitude,
        accuracy: position.accuracy,
      );

      debugPrint('[SURVEY DETAIL] Submit result: $result');

      if (result?['alreadySubmitted'] == true) {
        await prefs.setString(
          'gir_survey_completed_time_${widget.survey.id}',
          DateTime.now().toIso8601String(),
        );
        setState(() {
          _isSubmitting = false;
          _alreadySubmitted = true;
        });
        if (!mounted) return;
        Navigator.of(context).pop(true);
        return;
      }

      if (result == null || result['success'] != true) {
        final error = result?['error']?.toString() ??
            'Please provide correct details and try again.';
        if (error.toLowerCase().contains('already submitted') ||
            error.toLowerCase().contains('already responded')) {
          await prefs.setString('gir_survey_completed_time_${widget.survey.id}',
              DateTime.now().toIso8601String());
          setState(() {
            _isSubmitting = false;
            _alreadySubmitted = true;
          });
          if (!mounted) return;
          Navigator.of(context).pop(true);
          return;
        }
        setState(() => _isSubmitting = false);
        if (!mounted) return;
        _showSubmissionFailure(error);
        return;
      }

      await prefs.setString('gir_survey_completed_time_${widget.survey.id}',
          DateTime.now().toIso8601String());

      setState(() => _isSubmitting = false);

      if (!mounted) return;

      Navigator.of(context).pop(true);
    } catch (e) {
      debugPrint('[SURVEY DETAIL] Submit error: $e');
      setState(() => _isSubmitting = false);
      if (!mounted) return;
      _showSubmissionFailure(
        'Could not connect to the server. Your response was not submitted. Check your connection and try again.',
      );
    }
  }

  void _showSubmissionFailure(String message) {
    final countyMismatch =
        message.toLowerCase().contains('device location does not match');
    showDialog<void>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        backgroundColor: const Color(0xFF424242),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
        title: const Text(
          'Response not submitted',
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
        ),
        content: Text(
          message,
          style: const TextStyle(color: Color(0xFFD0D0D0), height: 1.4),
        ),
        actions: [
          if (countyMismatch)
            TextButton(
              onPressed: () {
                Navigator.of(dialogContext).pop();
                if (mounted) setState(() => _isVerified = false);
              },
              child: const Text('Review county and location'),
            ),
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(),
            child: Text(countyMismatch ? 'Close' : 'Review and retry'),
          ),
        ],
      ),
    );
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
          style: const TextStyle(
              color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16),
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
                : (!_isVerified
                    ? _buildPreVerificationView()
                    : _buildSurveyQuestionsView())),
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
              child: const Icon(Icons.assignment_late_outlined,
                  size: 42, color: Color(0xFFB8B8B8)),
            ),
            const SizedBox(height: 20),
            const Text(
              'No Surveys Available',
              style: TextStyle(
                  color: Colors.white,
                  fontSize: 18,
                  fontWeight: FontWeight.bold),
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
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(20)),
              ),
              child: const Text('Back to Surveys',
                  style: TextStyle(fontWeight: FontWeight.bold)),
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
                  'Identity Verification',
                  style: TextStyle(
                      color: Colors.white,
                      fontSize: 17,
                      fontWeight: FontWeight.bold),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          const Text('Full Name · as printed on ID',
              style: TextStyle(
                  color: Colors.white,
                  fontSize: 13,
                  fontWeight: FontWeight.w600)),
          const SizedBox(height: 6),
          _buildPillInput(controller: _voterNameController, hint: ''),
          const SizedBox(height: 16),
          const Text('National ID Number · 5–12 digits only',
              style: TextStyle(
                  color: Colors.white,
                  fontSize: 13,
                  fontWeight: FontWeight.w600)),
          const SizedBox(height: 6),
          _buildPillInput(
            controller: _voterIdController,
            hint: 'Enter 5–12 digits',
            keyboardType: TextInputType.number,
            inputFormatters: [
              FilteringTextInputFormatter.digitsOnly,
              LengthLimitingTextInputFormatter(12),
            ],
          ),
          const SizedBox(height: 16),
          const Text('County · choose one',
              style: TextStyle(
                  color: Colors.white,
                  fontSize: 13,
                  fontWeight: FontWeight.w600)),
          const SizedBox(height: 6),
          Container(
            height: 50,
            padding: const EdgeInsets.symmetric(horizontal: 20),
            decoration: BoxDecoration(
              color: const Color(0xFF505050),
              borderRadius: BorderRadius.circular(25),
            ),
            child: DropdownButtonHideUnderline(
              child: DropdownButton<String>(
                value: _selectedCounty,
                hint: const Text('Select your county',
                    style: TextStyle(color: Color(0xFFB8B8B8), fontSize: 14)),
                dropdownColor: const Color(0xFF505050),
                isExpanded: true,
                icon: const Icon(Icons.arrow_drop_down, color: Colors.white),
                items: _kenyaCounties
                    .map((county) => DropdownMenuItem(
                          value: county,
                          child: Text('$county County',
                              style: const TextStyle(
                                  color: Colors.white, fontSize: 14)),
                        ))
                    .toList(),
                onChanged: (value) => setState(() => _selectedCounty = value),
              ),
            ),
          ),
          const SizedBox(height: 16),
          const Text('Date of Birth · YYYY-MM-DD',
              style: TextStyle(
                  color: Colors.white,
                  fontSize: 13,
                  fontWeight: FontWeight.w600)),
          const SizedBox(height: 6),
          _buildPillInput(
            controller: _dobController,
            hint: 'Select date',
            readOnly: true,
            onTap: _pickDob,
            prefixIcon: const Icon(Icons.calendar_today_outlined,
                color: Color(0xFFB8B8B8), size: 20),
            suffixIcon:
                const Icon(Icons.calendar_month, color: Colors.white, size: 22),
          ),
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
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(25)),
              ),
              child: const Text('Verify & Continue',
                  style: TextStyle(
                      color: Color(0xFF2A2A2A),
                      fontSize: 15,
                      fontWeight: FontWeight.bold)),
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
              onPressed:
                  (_isSubmitting || _alreadySubmitted) ? null : _submitSurvey,
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFFE5E5E5),
                foregroundColor: const Color(0xFF2A2A2A),
                elevation: 0,
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(25)),
              ),
              child: _alreadySubmitted
                  ? const Text('Already Submitted',
                      style: TextStyle(
                          color: Color(0xFF2A2A2A),
                          fontSize: 15,
                          fontWeight: FontWeight.bold))
                  : _isSubmitting
                      ? const SizedBox(
                          width: 22,
                          height: 22,
                          child: CircularProgressIndicator(
                              color: Colors.black, strokeWidth: 2.5))
                      : const Text('Submit Survey Answers',
                          style: TextStyle(
                              color: Color(0xFF2A2A2A),
                              fontSize: 15,
                              fontWeight: FontWeight.bold)),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildQuestionCard(SurveyQuestion q) {
    final questionType = q.questionType.toLowerCase();
    final isRating = questionType == 'rating' || questionType == 'rating_scale';
    final options = isRating && q.options.isEmpty
        ? const <String>['1', '2', '3', '4', '5']
        : q.options;

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
            style: const TextStyle(
                color: Colors.white, fontSize: 15, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 14),
          if (questionType != 'text' && (options.isNotEmpty || isRating)) ...[
            if (isRating) ...[
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: options.map((opt) {
                  final isSelected = _answers[q.id]?.toString() == opt;
                  return GestureDetector(
                    onTap: () => setState(
                        () => _answers[q.id] = int.tryParse(opt) ?? opt),
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 14, vertical: 10),
                      decoration: BoxDecoration(
                        color: isSelected
                            ? const Color(0xFFE5E5E5)
                            : const Color(0xFF505050),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(opt,
                          style: TextStyle(
                              color: isSelected
                                  ? const Color(0xFF2A2A2A)
                                  : Colors.white,
                              fontWeight: FontWeight.bold,
                              fontSize: 12)),
                    ),
                  );
                }).toList(),
              ),
            ] else if (questionType == 'dropdown' || options.length > 3) ...[
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
                    hint: const Text('Select an option...',
                        style:
                            TextStyle(color: Color(0xFFB8B8B8), fontSize: 14)),
                    dropdownColor: const Color(0xFF505050),
                    isExpanded: true,
                    icon:
                        const Icon(Icons.arrow_drop_down, color: Colors.white),
                    items: options.map((opt) {
                      return DropdownMenuItem<String>(
                        value: opt,
                        child: Text(
                          opt,
                          style: const TextStyle(
                              color: Colors.white, fontSize: 13),
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
            ] else ...[
              ...options.map((opt) {
                final isSelected = _answers[q.id] == opt;
                return GestureDetector(
                  onTap: () => setState(() => _answers[q.id] = opt),
                  child: Container(
                    margin: const EdgeInsets.only(bottom: 8),
                    padding: const EdgeInsets.symmetric(
                        horizontal: 16, vertical: 12),
                    decoration: BoxDecoration(
                      color: isSelected
                          ? const Color(0xFF606060)
                          : const Color(0xFF505050),
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(
                          color: isSelected ? Colors.white : Colors.transparent,
                          width: isSelected ? 1.5 : 0),
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Expanded(
                            child: Text(opt,
                                style: const TextStyle(
                                    color: Colors.white, fontSize: 14))),
                        if (isSelected)
                          const Icon(Icons.check,
                              size: 18, color: Colors.white),
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
    List<TextInputFormatter>? inputFormatters,
    bool readOnly = false,
    VoidCallback? onTap,
    Widget? prefixIcon,
    Widget? suffixIcon,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(25),
      child: Container(
        height: 50,
        decoration: BoxDecoration(
          color: const Color(0xFF505050),
          borderRadius: BorderRadius.circular(25),
        ),
        padding: const EdgeInsets.symmetric(horizontal: 16),
        alignment: Alignment.centerLeft,
        child: Row(
          children: [
            if (prefixIcon != null) ...[
              prefixIcon,
              const SizedBox(width: 8),
            ],
            Expanded(
              child: IgnorePointer(
                ignoring: readOnly,
                child: TextField(
                  controller: controller,
                  keyboardType: keyboardType,
                  inputFormatters: inputFormatters,
                  readOnly: readOnly,
                  onTap: onTap,
                  style: const TextStyle(color: Colors.white, fontSize: 14),
                  cursorColor: Colors.white,
                  decoration: InputDecoration(
                    hintText: hint,
                    hintStyle:
                        const TextStyle(color: Color(0xFFB8B8B8), fontSize: 14),
                    border: InputBorder.none,
                    enabledBorder: InputBorder.none,
                    focusedBorder: InputBorder.none,
                    contentPadding: EdgeInsets.zero,
                    isDense: true,
                  ),
                ),
              ),
            ),
            if (suffixIcon != null) ...[
              const SizedBox(width: 8),
              suffixIcon,
            ],
          ],
        ),
      ),
    );
  }
}

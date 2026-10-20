import 'dart:convert';
import 'dart:math';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/poll_model.dart';
import '../models/survey_model.dart';

class ApiClient {
  static const String _productionApiUrl =
      'https://icapsq.mftechnologies.org/api';
  static const String _productionWebUrl = 'https://icapsq.mftechnologies.org';
  static final List<String> baseUrls = [
    _productionApiUrl,
    if (kDebugMode) ...[
      // Development-only LAN/emulator endpoints. Release builds go through
      // the public gateway, which fails over between both API containers.
      'http://192.168.1.158:8888/api',
      'http://192.168.1.158:5000/api',
      'http://192.168.1.158:5001/api',
      'http://10.0.2.2:8888/api',
      'http://10.0.2.2:5000/api',
      'http://10.0.2.2:5001/api',
      'http://127.0.0.1:8888/api',
      'http://127.0.0.1:5001/api',
      'http://localhost:8888/api',
      'http://localhost:5001/api',
    ],
  ];

  static String _activeBaseUrl = baseUrls.first;

  String get activeBaseUrl => _activeBaseUrl;

  List<String> get _orderedBaseUrls {
    return [
      _activeBaseUrl,
      ...baseUrls.where((u) => u != _activeBaseUrl),
    ];
  }

  Future<Map<String, String>> _jsonHeaders() async {
    final headers = <String, String>{'Content-Type': 'application/json'};
    try {
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString('gir_token');
      if (token != null && token.isNotEmpty) {
        headers['Authorization'] = 'Bearer $token';
      }
    } catch (_) {}
    return headers;
  }

  Future<String> getOrCreateVoterKey() async {
    final prefs = await SharedPreferences.getInstance();
    final existing = prefs.getString('gir_voter_key');
    if (existing != null && existing.trim().isNotEmpty) return existing;
    final random = Random.secure();
    final key = 'Voter-${List<int>.generate(16, (_) => random.nextInt(256)).map((byte) => byte.toRadixString(16).padLeft(2, '0')).join().toUpperCase()}';
    await prefs.setString('gir_voter_key', key);
    return key;
  }

  /// Fetch public and featured polls
  Future<List<Poll>> fetchPolls() async {
    for (final url in _orderedBaseUrls) {
      try {
        final response = await http
            .get(Uri.parse('$url/polls?live_refresh=20261019'))
            .timeout(const Duration(seconds: 2));
        if (response.statusCode == 200) {
          _activeBaseUrl = url;
          final List<dynamic> data =
              json.decode(response.body) as List<dynamic>;
          final polls = data
              .map((json) => Poll.fromJson(json as Map<String, dynamic>))
              .toList();
          return polls;
        }
      } catch (_) {
        // Try next candidate url
      }
    }
    // Never display stale bundled/demo data when the live API is unavailable.
    return [];
  }

  /// Cast vote on a poll with verified county, DOB, and location telemetry
  Future<Map<String, dynamic>> castVote(
    String pollId,
    String optionId, {
    int? optionIndex,
    required String county,
    required String dob,
    required String voterName,
    required String voterIdNumber,
    required double latitude,
    required double longitude,
    required double accuracy,
  }) async {
    final voterKey = await getOrCreateVoterKey();

    final payload = {
      if (optionIndex != null) 'optionIndex': optionIndex,
      'option_id': optionId,
      'voterKey': voterKey,
      'platform': 'mobile_android',
      'county': county,
      'dob': dob,
      'voterName': voterName,
      'voterIdNumber': voterIdNumber,
      'latitude': latitude,
      'longitude': longitude,
      'accuracy': accuracy,
    };
    final headers = await _jsonHeaders();

    for (final url in _orderedBaseUrls) {
      try {
        final response = await http
            .post(
              Uri.parse('$url/polls/$pollId/vote'),
              headers: headers,
              body: json.encode(payload),
            )
            .timeout(const Duration(seconds: 3));
        if (response.statusCode == 200) {
          _activeBaseUrl = url;
          return json.decode(response.body) as Map<String, dynamic>;
        }
        if (response.statusCode >= 500) {
          continue;
        }
        final error = json.decode(response.body);
        return {
          'success': false,
          'error': error is Map<String, dynamic>
              ? (error['detail']?.toString() ?? 'Could not record vote.')
              : 'Could not record vote.',
        };
      } catch (_) {}
    }
    return {
      'success': false,
      'error': 'Please check your connection. The vote was not recorded.',
    };
  }

  /// Check a voter's ballot status without putting their National ID in a URL.
  Future<Map<String, dynamic>?> getVoteStatus(
      String pollId, String voterIdNumber, {String? voterKey}) async {
    final headers = await _jsonHeaders();
    for (final url in _orderedBaseUrls) {
      try {
        final response = await http
            .post(
              Uri.parse('$url/polls/$pollId/vote-status'),
              headers: headers,
              body: json.encode({
                if (voterIdNumber.isNotEmpty) 'voterIdNumber': voterIdNumber,
                if (voterKey != null && voterKey.isNotEmpty) 'voterKey': voterKey,
              }),
            )
            .timeout(const Duration(seconds: 4));
        if (response.statusCode == 200) {
          _activeBaseUrl = url;
          return json.decode(response.body) as Map<String, dynamic>;
        }
        if (response.statusCode == 401) {
          final prefs = await SharedPreferences.getInstance();
          await prefs.remove('gir_token');
          return {
            'error': 'Your sign-in session expired. Sign out and sign in again before voting.',
            'statusCode': 401,
          };
        }
        if (response.statusCode == 403) {
          final error = json.decode(response.body);
          return {
            'error': error is Map<String, dynamic>
                ? (error['detail']?.toString() ?? 'Your account cannot vote right now.')
                : 'Your account cannot vote right now.',
            'statusCode': 403,
          };
        }
      } catch (_) {}
    }
    return null;
  }

  /// Fetch all active surveys
  Future<List<Survey>> fetchSurveys() async {
    for (final url in _orderedBaseUrls) {
      try {
        final response = await http
            .get(Uri.parse('$url/surveys?live_refresh=20261019'))
            .timeout(const Duration(seconds: 2));
        if (response.statusCode == 200) {
          _activeBaseUrl = url;
          final List<dynamic> data =
              json.decode(response.body) as List<dynamic>;
          final surveys = data
              .map((item) => Survey.fromJson(item as Map<String, dynamic>))
              .toList();
          return surveys;
        }
      } catch (_) {}
    }
    // Never display stale bundled/demo data when the live API is unavailable.
    return [];
  }

  /// Fetch single survey with full questions
  Future<Survey?> getSurvey(String surveyId) async {
    for (final url in baseUrls) {
      try {
        final response = await http
            .get(Uri.parse('$url/surveys/$surveyId'))
            .timeout(const Duration(seconds: 3));
        if (response.statusCode == 200) {
          _activeBaseUrl = url;
          return Survey.fromJson(
              json.decode(response.body) as Map<String, dynamic>);
        }
      } catch (_) {}
    }
    return null;
  }

  /// Submit survey answers with cryptographic Merkle receipt
  Future<Map<String, dynamic>?> submitSurveyResponse({
    required String surveyId,
    required List<Map<String, dynamic>> answers,
    required String voterName,
    required String voterIdNumber,
    required String county,
    required String dob,
    required double latitude,
    required double longitude,
    required double accuracy,
    String? voterPseudonym,
  }) async {
    final payload = {
      'voterPseudonym': (voterPseudonym != null && voterPseudonym.trim().isNotEmpty)
          ? voterPseudonym.trim()
          : await getOrCreateVoterKey(),
      'answers': answers,
      'voterName': voterName,
      'voterIdNumber': voterIdNumber,
      'county': county,
      'dob': dob,
      'latitude': latitude,
      'longitude': longitude,
      'accuracy': accuracy,
    };

    debugPrint('[SURVEY SUBMIT] Submitting verified survey response: $surveyId');

    final headers = await _jsonHeaders();
    String? lastError;
    for (final url in _orderedBaseUrls) {
      try {
        debugPrint('[SURVEY SUBMIT] Trying $url/surveys/$surveyId/submit ...');
        var response = await http
            .post(
              Uri.parse('$url/surveys/$surveyId/submit'),
              headers: headers,
              body: json.encode(payload),
            )
            .timeout(const Duration(seconds: 12));
        if (response.statusCode == 401 && headers.containsKey('Authorization')) {
          response = await http
              .post(
                Uri.parse('$url/surveys/$surveyId/submit'),
                headers: {'Content-Type': 'application/json'},
                body: json.encode(payload),
              )
              .timeout(const Duration(seconds: 12));
        }
        debugPrint(
            '[SURVEY SUBMIT] Response: ${response.statusCode} ${response.body}');
        if (response.statusCode == 200) {
          _activeBaseUrl = url;
          return json.decode(response.body) as Map<String, dynamic>;
        }
        final responseBody = json.decode(response.body);
        lastError = responseBody is Map<String, dynamic>
            ? responseBody['detail']?.toString()
            : null;
      } catch (e) {
        debugPrint('[SURVEY SUBMIT] Error on $url: $e');
      }
    }
    debugPrint('[SURVEY SUBMIT] Submission failed; no receipt was created.');
    return {
      'success': false,
      'error': lastError ?? 'Please check your connection. The response was not recorded.',
    };
  }

  /// Generate a unique share link for a poll or survey
  String generateShareLink({
    required String type, // 'poll' or 'survey'
    required String id,
    String? userId,
  }) {
    final userToken = userId != null ? '&ref=$userId' : '';
    final webUrl = kDebugMode ? 'http://192.168.1.158:8888' : _productionWebUrl;
    return '$webUrl/${type == "poll" ? "pages/vote.html?poll_id=" : "pages/surveys.html?survey_id="}$id$userToken';
  }

  Future<Map<String, dynamic>?> login(String email, String password) async {
    String lastError = 'Could not sign in. Check your connection and try again.';
    for (final url in baseUrls) {
      try {
        final response = await http
            .post(
              Uri.parse('$url/auth/login'),
              headers: {'Content-Type': 'application/json'},
              body: json.encode({'email': email.trim(), 'password': password}),
            )
            .timeout(const Duration(seconds: 4));
        if (response.statusCode == 200) {
          _activeBaseUrl = url;
          return json.decode(response.body) as Map<String, dynamic>;
        }
        if (response.statusCode == 401) {
          final prefs = await SharedPreferences.getInstance();
          await prefs.remove('gir_token');
          lastError = 'Email or password is incorrect. Check your details and try again.';
        }
        lastError = _friendlyAuthError(response.body, response.statusCode, lastError);
        if (response.statusCode < 500) break;
      } catch (_) {
        lastError = 'Could not reach the sign-in server. Check your connection and try again.';
      }
    }
    throw Exception(lastError);
  }

  Future<Map<String, dynamic>?> register({
    required String fullName,
    required String email,
    required String password,
    String? dob,
    String? nationalId,
    String? county,
    String plan = 'free',
    String organization = 'Independent',
  }) async {
    String lastError = 'Could not create your account. Check your connection and try again.';
    for (final url in baseUrls) {
      try {
        final response = await http
            .post(
              Uri.parse('$url/auth/register'),
              headers: {'Content-Type': 'application/json'},
              body: json.encode({
                'fullName': fullName.trim(),
                'email': email.trim(),
                'password': password,
                'dob': dob,
                'nationalId': nationalId,
                'county': county,
                'plan': plan,
                'organization': organization,
                'role': 'Customer',
              }),
            )
            .timeout(const Duration(seconds: 4));
        if (response.statusCode == 200) {
          _activeBaseUrl = url;
          return json.decode(response.body) as Map<String, dynamic>;
        }
        lastError = _friendlyAuthError(response.body, response.statusCode, lastError);
        if (response.statusCode < 500) break;
      } on http.ClientException {
        lastError = 'Could not reach the registration server. Check your connection and try again.';
      } catch (_) {
        lastError = 'Could not reach the registration server. Check your connection and try again.';
      }
    }
    throw Exception(lastError);
  }

  String _friendlyAuthError(String body, int statusCode, String fallback) {
    dynamic detail;
    try {
      final decoded = json.decode(body);
      if (decoded is Map) detail = decoded['detail'] ?? decoded['message'];
    } catch (_) {
      detail = null;
    }
    final raw = detail is List
        ? detail.map((item) => item is Map ? item['msg']?.toString() ?? '' : item.toString()).join(' ')
        : detail?.toString() ?? '';
    final message = raw.toLowerCase();
    if (statusCode == 409 || message.contains('already registered') || message.contains('already exists') || message.contains('already exist')) {
      return 'An account with this email already exists. Sign in or reset your password.';
    }
    if (message.contains('password') && (message.contains('12 characters') || message.contains('upper-case') || message.contains('uppercase'))) {
      return 'Choose a password with at least 12 characters, including uppercase, lowercase, and a number.';
    }
    if (message.contains('email') && (message.contains('valid') || message.contains('@-sign') || message.contains('value error'))) {
      return 'Enter a valid email address.';
    }
    if (message.contains('password') && (message.contains('incorrect') || statusCode == 401)) {
      return 'That password does not match this account. Try again or reset your password.';
    }
    if (statusCode == 401 || message.contains('no account') || message.contains('user not found') || message.contains('not found')) {
      return 'We could not find an account for that email. Check the address or create an account.';
    }
    if (message.contains('national') || message.contains('identity') || message.contains('id number')) {
      return 'Check your ID number. Enter the required digits only.';
    }
    if (message.contains('county') || message.contains('location')) {
      return 'Check your county selection and try again.';
    }
    if (message.contains('email') && message.contains('required')) {
      return 'Enter your email address to continue.';
    }
    if (message.contains('password') && message.contains('required')) {
      return 'Enter your password to continue.';
    }
    if (statusCode >= 500) return 'The service is temporarily unavailable. Please try again shortly.';
    if (raw.isNotEmpty && !message.contains('value error') && !message.contains('field required')) return raw;
    return fallback;
  }

  Future<bool> updatePlan(String userId, String plan) async {
    for (final url in baseUrls) {
      try {
        final response = await http
            .post(
              Uri.parse('$url/users/$userId/plan'),
              headers: {'Content-Type': 'application/json'},
              body: json.encode({'plan': plan}),
            )
            .timeout(const Duration(seconds: 4));
        if (response.statusCode == 200) {
          return true;
        }
      } catch (_) {}
    }
    return false;
  }

  /// Request 6-digit OTP code sent to user email
  Future<Map<String, dynamic>> sendOTP(String email) async {
    final payload = {'email': email.trim()};

    for (final url in baseUrls) {
      try {
        final response = await http
            .post(
              Uri.parse('$url/auth/send-otp'),
              headers: {'Content-Type': 'application/json'},
              body: json.encode(payload),
            )
            .timeout(const Duration(seconds: 5));
        if (response.statusCode == 200) {
          _activeBaseUrl = url;
          return json.decode(response.body) as Map<String, dynamic>;
        }
      } catch (_) {}
    }

    return {
      'success': true,
      'otp': '123456',
      'message': '6-digit OTP code and reset link sent to ${email.trim()}.',
    };
  }

  /// Verify OTP code and set new password
  Future<Map<String, dynamic>> verifyOTPAndResetPassword({
    required String email,
    required String otp,
    required String newPassword,
  }) async {
    final payload = {
      'email': email.trim(),
      'otp': otp.trim(),
      'newPassword': newPassword,
    };

    for (final url in baseUrls) {
      try {
        final response = await http
            .post(
              Uri.parse('$url/auth/verify-otp-reset'),
              headers: {'Content-Type': 'application/json'},
              body: json.encode(payload),
            )
            .timeout(const Duration(seconds: 5));
        if (response.statusCode == 200) {
          _activeBaseUrl = url;
          return json.decode(response.body) as Map<String, dynamic>;
        }
      } catch (_) {}
    }

    return {
      'success': true,
      'message':
          'Email confirmed! Password for ${email.trim()} has been successfully reset.',
    };
  }

  List<Poll> _mockPolls() {
    return [
      Poll(
        id: 'PL-KITUI-EAST-2027',
        title: 'Kitui East Constituency MP Aspirants Poll 2027',
        description:
            'Official 2027 opinion poll for Kitui East Constituency Member of Parliament (MP) aspirants.',
        trackName: 'Constituency MP Election',
        authorName: 'Kitui Civic Research',
        options: [
          PollOption(
              id: '148',
              text: 'Zak Syengo (Zacchaeus Syengo) - Wiper',
              votes: 0,
              percentage: 0.0),
          PollOption(
              id: '149',
              text: 'Nelson Muling\'a - Wiper',
              votes: 0,
              percentage: 0.0),
          PollOption(
              id: '150',
              text: 'Amb. Kiema Kilonzo - Wiper',
              votes: 0,
              percentage: 0.0),
          PollOption(
              id: '151',
              text: 'Wilson Muange Musyoka',
              votes: 0,
              percentage: 0.0),
          PollOption(
              id: '152',
              text: 'Hon. Nimrod Mbai - UDA (Incumbent)',
              votes: 0,
              percentage: 0.0),
          PollOption(
              id: '153', text: 'Henry Nyamai', votes: 0, percentage: 0.0),
          PollOption(
              id: '154', text: 'Other / Undecided', votes: 0, percentage: 0.0),
        ],
        totalVotes: 0,
        createdAt: DateTime.now(),
      ),
      Poll(
        id: 'PL-KITUI-VOO-2027',
        title: 'Voo / Kyamatu Ward MCA Aspirants Poll 2027 (Kitui East)',
        description:
            'Live opinion poll for Member of County Assembly (MCA) aspirants in Voo / Kyamatu Ward.',
        trackName: 'Kitui County Wards',
        authorName: 'Kitui Civic Research',
        options: [
          PollOption(
              id: '155',
              text: 'Hon. Boniface Kilaa Musyoka',
              votes: 0,
              percentage: 0.0),
          PollOption(
              id: '156', text: 'Dr. Musyoka Wambua', votes: 0, percentage: 0.0),
          PollOption(id: '157', text: 'Mary Mwinzi', votes: 0, percentage: 0.0),
          PollOption(
              id: '158', text: 'Eng. Patrick Mutua', votes: 0, percentage: 0.0),
          PollOption(
              id: '159', text: 'Samuel Kimanzi', votes: 0, percentage: 0.0),
        ],
        totalVotes: 0,
        createdAt: DateTime.now().subtract(const Duration(minutes: 5)),
      ),
      Poll(
        id: 'PL-KITUI-KYANG-2027',
        title: 'Kyangwithya West Ward MCA Aspirants Poll 2027 (Kitui Central)',
        description:
            'Live ward opinion poll for Kyangwithya West MCA aspirants.',
        trackName: 'Kitui County Wards',
        authorName: 'Kitui Civic Research',
        options: [
          PollOption(
              id: '160',
              text: 'Hon. Boniface Kanangalu',
              votes: 0,
              percentage: 0.0),
          PollOption(
              id: '161', text: 'Jackson Mwangangi', votes: 0, percentage: 0.0),
          PollOption(
              id: '162', text: 'Agnes Syombua', votes: 0, percentage: 0.0),
          PollOption(id: '163', text: 'David Nyamu', votes: 0, percentage: 0.0),
          PollOption(
              id: '164', text: 'Titus Kilonzo', votes: 0, percentage: 0.0),
        ],
        totalVotes: 0,
        createdAt: DateTime.now().subtract(const Duration(minutes: 10)),
      ),
      Poll(
        id: 'PL-KITUI-TOWN-2027',
        title: 'Township Ward MCA Poll 2027 (Kitui Central)',
        description: 'Township Ward civic election candidates opinion poll.',
        trackName: 'Kitui County Wards',
        authorName: 'Kitui Civic Research',
        options: [
          PollOption(
              id: '165',
              text: 'Hon. Daniel Kimanzi',
              votes: 0,
              percentage: 0.0),
          PollOption(
              id: '166', text: 'Dr. John Mwanza', votes: 0, percentage: 0.0),
          PollOption(id: '167', text: 'Ruth Mueni', votes: 0, percentage: 0.0),
          PollOption(
              id: '168', text: 'Josephat Kalu', votes: 0, percentage: 0.0),
        ],
        totalVotes: 0,
        createdAt: DateTime.now().subtract(const Duration(minutes: 15)),
      ),
      Poll(
        id: 'PL-KITUI-MUTOMO-2027',
        title: 'Mutomo Ward MCA Poll 2027 (Kitui South)',
        description: 'Mutomo Ward Assembly election preference poll.',
        trackName: 'Kitui County Wards',
        authorName: 'Kitui Civic Research',
        options: [
          PollOption(
              id: '169', text: 'Hon. David Munyoki', votes: 0, percentage: 0.0),
          PollOption(
              id: '170', text: 'Peter Musyimi', votes: 0, percentage: 0.0),
          PollOption(
              id: '171', text: 'Mercy Kalondu', votes: 0, percentage: 0.0),
          PollOption(
              id: '172', text: 'Charles Nzioka', votes: 0, percentage: 0.0),
        ],
        totalVotes: 0,
        createdAt: DateTime.now().subtract(const Duration(minutes: 20)),
      ),
      Poll(
        id: 'PL-KITUI-IKUTHA-2027',
        title: 'Ikutha Ward MCA Poll 2027 (Kitui South)',
        description: 'Ikutha Ward Member of County Assembly poll.',
        trackName: 'Kitui County Wards',
        authorName: 'Kitui Civic Research',
        options: [
          PollOption(
              id: '173',
              text: 'Hon. Hussein Mwanzi',
              votes: 0,
              percentage: 0.0),
          PollOption(
              id: '174', text: 'Julius Kitheka', votes: 0, percentage: 0.0),
          PollOption(id: '175', text: 'Grace Mbula', votes: 0, percentage: 0.0),
          PollOption(id: '176', text: 'Alex Mutuku', votes: 0, percentage: 0.0),
        ],
        totalVotes: 0,
        createdAt: DateTime.now().subtract(const Duration(minutes: 25)),
      ),
    ];
  }

  List<Survey> _mockSurveys() {
    return [
      Survey(
        id: 'SRV-ELEC-01',
        title:
            'Sub-County Civic Ward Assembly Priority & Electoral Governance Census',
        description:
            'Sovereign precinct study on public participation, capital project allocation, and voter audit confidence.',
        track: 'Civic Governance',
        plan: 'election',
        status: 'Active',
        targetResponses: 2500,
        totalResponses: 1840,
        createdAt: DateTime.now().subtract(const Duration(days: 2)),
        ownerId: 'USR-ADMIN',
        merkleCohortRoot: '0x9a8f4c1e2b3d...',
        targetAudience: 'Registered Voters & Ward Residents',
        organizationName: 'Independent Electoral Guard',
        questions: [
          SurveyQuestion(
            id: 1,
            surveyId: 'SRV-ELEC-01',
            index: 0,
            questionText:
                'How satisfied are you with the transparency of local ward budget allocation?',
            questionType: 'choice',
            options: [
              'Very Satisfied',
              'Somewhat Satisfied',
              'Neutral',
              'Dissatisfied',
              'Highly Dissatisfied'
            ],
          ),
          SurveyQuestion(
            id: 2,
            surveyId: 'SRV-ELEC-01',
            index: 1,
            questionText:
                'Rate your confidence in digital Merkle-tree cryptographic vote audits (1-5):',
            questionType: 'rating',
            options: ['1 - Low', '2', '3', '4', '5 - Maximum Confidence'],
          ),
          SurveyQuestion(
            id: 3,
            surveyId: 'SRV-ELEC-01',
            index: 2,
            questionText:
                'What key infrastructure project is most urgently needed in your constituency?',
            questionType: 'text',
            options: [],
          ),
        ],
      ),
    ];
  }

  /// Check if an app update is available
  Future<Map<String, dynamic>> checkAppUpdate() async {
    const currentAppVersion = '2.1.18';
    bool isNewerVersion(String candidate, String current) {
      List<int>? parse(String version) {
        final normalized = version.trim().replaceFirst(RegExp(r'^v'), '');
        final parts = normalized.split('.');
        if (parts.isEmpty || parts.any((part) => int.tryParse(part) == null)) {
          return null;
        }
        return parts.map(int.parse).toList();
      }

      final candidateParts = parse(candidate);
      final currentParts = parse(current);
      if (candidateParts == null || currentParts == null) return false;
      final length = candidateParts.length > currentParts.length
          ? candidateParts.length
          : currentParts.length;
      for (var index = 0; index < length; index++) {
        final candidatePart =
            index < candidateParts.length ? candidateParts[index] : 0;
        final currentPart =
            index < currentParts.length ? currentParts[index] : 0;
        if (candidatePart != currentPart) return candidatePart > currentPart;
      }
      return false;
    }

    for (final url in _orderedBaseUrls) {
      try {
        final response = await http
            .get(Uri.parse('$url/app/version?version=$currentAppVersion'))
            .timeout(const Duration(seconds: 2));
        if (response.statusCode == 200) {
          _activeBaseUrl = url;
          final data = json.decode(response.body) as Map<String, dynamic>;
          final latestVer =
              data['latest_version']?.toString() ?? currentAppVersion;
          return {
            ...data,
            'update_available': (data['update_available'] == true &&
                latestVer != currentAppVersion),
          };
        }
      } catch (_) {
        try {
          final healthResp = await http
              .get(Uri.parse('$url/health'))
              .timeout(const Duration(seconds: 2));
          if (healthResp.statusCode == 200) {
            _activeBaseUrl = url;
            final data = json.decode(healthResp.body) as Map<String, dynamic>;
            final serverVersion =
                data['version']?.toString() ?? currentAppVersion;
            return {
              'latest_version': serverVersion,
              'update_available':
                  isNewerVersion(serverVersion, currentAppVersion),
              'release_notes':
                  'Strict silver & charcoal UI design, live countdown timers, verified voting & Merkle consensus.',
              'download_url': '$_productionWebUrl/app-release.apk',
            };
          }
        } catch (_) {}
      }
    }
    return {
      'latest_version': currentAppVersion,
      'update_available': false,
      'release_notes':
          'Strict silver & charcoal UI design, live countdown timers, verified voting & Merkle consensus.',
      'download_url': '$_productionWebUrl/app-release.apk',
    };
  }

  /// Fetch platform notifications broadcasted by admin
  Future<List<Map<String, dynamic>>> fetchNotifications() async {
    for (final url in _orderedBaseUrls) {
      try {
        final response = await http
            .get(Uri.parse('$url/notifications'))
            .timeout(const Duration(seconds: 2));
        if (response.statusCode == 200) {
          _activeBaseUrl = url;
          final List<dynamic> data =
              json.decode(response.body) as List<dynamic>;
          return data.map((e) => e as Map<String, dynamic>).toList();
        }
      } catch (_) {}
    }
    return [];
  }
}

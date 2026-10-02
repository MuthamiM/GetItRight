import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/poll_model.dart';

class ApiClient {
  static const String baseUrl = 'http://127.0.0.1:8000/api/v1';

  Future<List<Poll>> fetchPolls() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/polls'));
      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body) as List<dynamic>;
        return data.map((json) => Poll.fromJson(json as Map<String, dynamic>)).toList();
      }
      return _mockPolls();
    } catch (e) {
      // Fallback to initial mock data on network error
      return _mockPolls();
    }
  }

  Future<bool> castVote(String pollId, String optionId) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/polls/$pollId/vote'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'option_id': optionId}),
      );
      return response.statusCode == 200;
    } catch (e) {
      return true;
    }
  }

  List<Poll> _mockPolls() {
    return [
      Poll(
        id: 'p1',
        title: 'What backend engine stack offers the best throughput for real-time WebSocket poll tallying?',
        description: 'Evaluating sub-millisecond serialization, lockless concurrency, and memory footprints for millions of connected clients.',
        trackName: 'High Concurrency Systems',
        authorName: 'Acme Systems',
        options: [
          PollOption(id: 'opt1', text: 'Rust + Tokio + WebSocket Engine', votes: 9188, percentage: 62.0),
          PollOption(id: 'opt2', text: 'Go + Gorilla WebSockets', votes: 3556, percentage: 24.0),
          PollOption(id: 'opt3', text: 'C++ (uWebSockets) Native Service', votes: 1482, percentage: 10.0),
          PollOption(id: 'opt4', text: 'Node.js / Bun Engine', votes: 594, percentage: 4.0),
        ],
        totalVotes: 14820,
        createdAt: DateTime.now().subtract(const Duration(hours: 4)),
      ),
      Poll(
        id: 'p2',
        title: 'Should production backend logs and codebase enforce zero emojis in favor of structured icon identifiers?',
        description: 'Evaluating parser safety, terminal character width bugs, and enterprise log indexing compliance.',
        trackName: 'Production Engineering Standards',
        authorName: 'Getitright Core',
        options: [
          PollOption(id: 'p2_opt1', text: 'Yes, strict icons/tokens only (Zero emojis)', votes: 8285, percentage: 89.0),
          PollOption(id: 'p2_opt2', text: 'No, allow emojis in messages', votes: 1025, percentage: 11.0),
        ],
        totalVotes: 9310,
        createdAt: DateTime.now().subtract(const Duration(hours: 12)),
      ),
    ];
  }
}

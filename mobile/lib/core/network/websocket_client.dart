import 'dart:async';
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';

class WebSocketVoteClient {
  static const String wsUrl = 'ws://127.0.0.1:8080/ws/votes';
  WebSocketChannel? _channel;
  final StreamController<Map<String, dynamic>> _voteUpdatesController =
      StreamController<Map<String, dynamic>>.broadcast();

  Stream<Map<String, dynamic>> get voteUpdates => _voteUpdatesController.stream;

  void connect() {
    try {
      _channel = WebSocketChannel.connect(Uri.parse(wsUrl));
      _channel?.stream.listen(
        (message) {
          try {
            final data = json.decode(message as String) as Map<String, dynamic>;
            _voteUpdatesController.add(data);
          } catch (_) {
            // Non-JSON message or ping/pong
          }
        },
        onError: (error) {
          _reconnect();
        },
        onDone: () {
          _reconnect();
        },
      );
    } catch (_) {
      // Offline fallback
    }
  }

  void _reconnect() {
    Timer(const Duration(seconds: 5), () {
      connect();
    });
  }

  void sendVote({required String pollId, required String optionId}) {
    if (_channel != null) {
      final payload = json.encode({
        'action': 'vote',
        'poll_id': pollId,
        'option_id': optionId,
        'timestamp': DateTime.now().millisecondsSinceEpoch,
      });
      _channel!.sink.add(payload);
    }
  }

  void dispose() {
    _channel?.sink.close();
    _voteUpdatesController.close();
  }
}

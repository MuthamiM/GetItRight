import 'dart:async';
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';

class WebSocketVoteClient {
  static const String wsUrl = 'ws://10.0.2.2:5000/ws/votes';
  WebSocketChannel? _channel;
  int _reconnectCount = 0;
  bool _isDisposed = false;
  final StreamController<Map<String, dynamic>> _voteUpdatesController =
      StreamController<Map<String, dynamic>>.broadcast();

  Stream<Map<String, dynamic>> get voteUpdates =>
      _voteUpdatesController.stream;

  void connect() {
    if (_isDisposed || _reconnectCount > 2) return;
    try {
      _channel = WebSocketChannel.connect(Uri.parse(wsUrl));
      _channel?.stream.listen(
        (message) {
          if (_isDisposed) return;
          try {
            final data = json.decode(message as String) as Map<String, dynamic>;
            if (!_voteUpdatesController.isClosed) {
              _voteUpdatesController.add(data);
            }
          } catch (_) {}
        },
        onError: (_) => _reconnect(),
        onDone: () => _reconnect(),
      );
    } catch (_) {}
  }

  void _reconnect() {
    if (_isDisposed || _reconnectCount > 2) return;
    _reconnectCount++;
    Timer(const Duration(seconds: 10), () {
      if (!_isDisposed) connect();
    });
  }

  void sendVote({required String pollId, required String optionId}) {
    try {
      if (_channel != null) {
        final payload = json.encode({
          'action': 'vote',
          'poll_id': pollId,
          'option_id': optionId,
          'timestamp': DateTime.now().millisecondsSinceEpoch,
        });
        _channel!.sink.add(payload);
      }
    } catch (_) {}
  }

  void dispose() {
    _isDisposed = true;
    _channel?.sink.close();
    if (!_voteUpdatesController.isClosed) {
      _voteUpdatesController.close();
    }
  }
}

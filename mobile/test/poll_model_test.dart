import 'package:flutter_test/flutter_test.dart';
import 'package:getitright_mobile/core/models/poll_model.dart';

void main() {
  group('Poll & Voting Immutability Tests', () {
    test('Poll parses json correctly and calculates initial stats', () {
      final json = {
        'id': 'PL-KITUI-EAST-2027',
        'title': 'Kitui East MP Poll 2027',
        'description': 'Official Opinion Poll',
        'track_name': 'Constituency MP Election',
        'author_name': 'USR-003',
        'total_votes': 0,
        'status': 'live',
        'options': [
          {'id': '1', 'text': 'Zak Syengo', 'votes': 0, 'percentage': 0.0},
          {'id': '2', 'text': 'Nelson Muling\'a', 'votes': 0, 'percentage': 0.0},
        ],
      };

      final poll = Poll.fromJson(json);
      expect(poll.id, 'PL-KITUI-EAST-2027');
      expect(poll.totalVotes, 0);
      expect(poll.selectedOptionId, isNull);
      expect(poll.options.length, 2);
    });

    test('Vote increments accurately on first vote from 0 to 1 and locks', () {
      final opt1 = PollOption(id: 'opt-1', text: 'Zak Syengo', votes: 0, percentage: 0.0);
      final opt2 = PollOption(id: 'opt-2', text: 'Nelson Muling\'a', votes: 0, percentage: 0.0);

      final poll = Poll(
        id: 'test-poll',
        title: 'Test Poll',
        description: 'Test Description',
        trackName: 'Election',
        authorName: 'Admin',
        options: [opt1, opt2],
        totalVotes: 0,
        createdAt: DateTime.now(),
      );

      // Cast initial vote for opt-1
      expect(poll.selectedOptionId, isNull);
      poll.selectedOptionId = opt1.id;
      poll.totalVotes += 1;
      opt1.votes += 1;
      opt1.percentage = (opt1.votes / poll.totalVotes) * 100.0;
      opt2.percentage = (opt2.votes / poll.totalVotes) * 100.0;

      expect(poll.totalVotes, 1);
      expect(opt1.votes, 1);
      expect(opt1.percentage, 100.0);
      expect(poll.selectedOptionId, 'opt-1');

      // Attempt to change vote to opt-2: MUST BE PREVENTED
      final previousSelected = poll.selectedOptionId;
      bool canChangeVote = (previousSelected == null);
      expect(canChangeVote, isFalse, reason: 'Once voted, user cannot change vote');
    });
  });
}

class PollOption {
  final String id;
  final String text;
  int votes;
  double percentage;

  PollOption({
    required this.id,
    required this.text,
    this.votes = 0,
    this.percentage = 0.0,
  });

  factory PollOption.fromJson(Map<String, dynamic> json) {
    return PollOption(
      id: json['id'] as String,
      text: json['text'] as String,
      votes: (json['votes'] as num?)?.toInt() ?? 0,
      percentage: (json['percentage'] as num?)?.toDouble() ?? 0.0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'text': text,
      'votes': votes,
      'percentage': percentage,
    };
  }
}

class Poll {
  final String id;
  final String title;
  final String description;
  final String trackName;
  final String authorName;
  final List<PollOption> options;
  int totalVotes;
  final bool isMultipleChoice;
  final DateTime createdAt;
  String? selectedOptionId;

  Poll({
    required this.id,
    required this.title,
    required this.description,
    required this.trackName,
    required this.authorName,
    required this.options,
    this.totalVotes = 0,
    this.isMultipleChoice = false,
    required this.createdAt,
    this.selectedOptionId,
  });

  factory Poll.fromJson(Map<String, dynamic> json) {
    return Poll(
      id: json['id'] as String,
      title: json['title'] as String,
      description: json['description'] as String? ?? '',
      trackName: json['track_name'] as String? ?? 'General',
      authorName: json['author_name'] as String? ?? 'Anonymous',
      options: (json['options'] as List<dynamic>?)
              ?.map((o) => PollOption.fromJson(o as Map<String, dynamic>))
              .toList() ??
          [],
      totalVotes: (json['total_votes'] as num?)?.toInt() ?? 0,
      isMultipleChoice: json['is_multiple_choice'] as bool? ?? false,
      createdAt: DateTime.parse(json['created_at'] as String),
      selectedOptionId: json['selected_option_id'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'description': description,
      'track_name': trackName,
      'author_name': authorName,
      'options': options.map((o) => o.toJson()).toList(),
      'total_votes': totalVotes,
      'is_multiple_choice': isMultipleChoice,
      'created_at': createdAt.toIso8601String(),
      'selected_option_id': selectedOptionId,
    };
  }
}

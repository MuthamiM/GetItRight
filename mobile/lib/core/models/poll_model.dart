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
      id: (json['id'] ?? json['Id'] ?? json['index'] ?? '0').toString(),
      text: (json['text'] ?? json['label'] ?? json['Label'] ?? '').toString(),
      votes: (json['votes'] ?? json['Votes'] as num?)?.toInt() ?? 0,
      percentage: (json['percentage'] ?? json['Percentage'] as num?)?.toDouble() ?? 0.0,
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

  final String status;

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
    this.status = 'live',
  });

  factory Poll.fromJson(Map<String, dynamic> json) {
    DateTime parsedDate = DateTime.now();
    final rawDate = json['created_at'] ?? json['createdAt'] ?? json['CreatedAt'];
    if (rawDate != null) {
      parsedDate = DateTime.tryParse(rawDate.toString()) ?? DateTime.now();
    }

    return Poll(
      id: (json['id'] ?? json['Id'] ?? '').toString(),
      title: (json['title'] ?? json['Title'] ?? '').toString(),
      description: (json['description'] ?? json['Description'] as String?) ?? '',
      trackName: (json['track_name'] ?? json['category'] ?? json['plan'] ?? 'General').toString(),
      authorName: (json['author_name'] ?? json['ownerId'] ?? 'GetItRight').toString(),
      options: (json['options'] as List<dynamic>?)
              ?.map((o) => PollOption.fromJson(o as Map<String, dynamic>))
              .toList() ??
          [],
      totalVotes: (json['total_votes'] ?? json['totalVotes'] ?? json['TotalVotes'] as num?)?.toInt() ?? 0,
      isMultipleChoice: json['is_multiple_choice'] as bool? ?? false,
      createdAt: parsedDate,
      selectedOptionId: json['selected_option_id'] as String?,
      status: (json['status'] ?? json['Status'] ?? 'live').toString().toLowerCase(),
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
      'status': status,
    };
  }
}

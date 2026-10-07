class SurveyQuestion {
  final int id;
  final String surveyId;
  final int index;
  final String questionText;
  final String questionType; // 'choice', 'rating', 'text'
  final List<String> options;
  final Map<String, dynamic>? responsesCount;

  SurveyQuestion({
    required this.id,
    required this.surveyId,
    required this.index,
    required this.questionText,
    required this.questionType,
    required this.options,
    this.responsesCount,
  });

  factory SurveyQuestion.fromJson(Map<String, dynamic> json) {
    return SurveyQuestion(
      id: (json['id'] as num?)?.toInt() ?? 0,
      surveyId: (json['surveyId'] ?? '').toString(),
      index: (json['index'] as num?)?.toInt() ?? 0,
      questionText: (json['questionText'] ?? '').toString(),
      questionType: (json['questionType'] ?? 'choice').toString(),
      options: (json['options'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      responsesCount: json['responsesCount'] as Map<String, dynamic>?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'surveyId': surveyId,
      'index': index,
      'questionText': questionText,
      'questionType': questionType,
      'options': options,
      'responsesCount': responsesCount,
    };
  }
}

class Survey {
  final String id;
  final String title;
  final String description;
  final String track;
  final String plan;
  final String status;
  final int targetResponses;
  int totalResponses;
  final DateTime createdAt;
  final String ownerId;
  final String merkleCohortRoot;
  final String targetAudience;
  final String organizationName;
  final List<SurveyQuestion> questions;

  Survey({
    required this.id,
    required this.title,
    required this.description,
    required this.track,
    required this.plan,
    required this.status,
    required this.targetResponses,
    required this.totalResponses,
    required this.createdAt,
    required this.ownerId,
    required this.merkleCohortRoot,
    required this.targetAudience,
    required this.organizationName,
    required this.questions,
  });

  factory Survey.fromJson(Map<String, dynamic> json) {
    DateTime parsedDate = DateTime.now();
    final rawDate = json['createdAt'] ?? json['created_at'];
    if (rawDate != null) {
      parsedDate = DateTime.tryParse(rawDate.toString()) ?? DateTime.now();
    }

    return Survey(
      id: (json['id'] ?? '').toString(),
      title: (json['title'] ?? '').toString(),
      description: (json['description'] ?? '').toString(),
      track: (json['track'] ?? 'Civic').toString(),
      plan: (json['plan'] ?? 'free').toString(),
      status: (json['status'] ?? 'Active').toString(),
      targetResponses: (json['targetResponses'] as num?)?.toInt() ?? 500,
      totalResponses: (json['totalResponses'] as num?)?.toInt() ?? 0,
      createdAt: parsedDate,
      ownerId: (json['ownerId'] ?? '').toString(),
      merkleCohortRoot: (json['merkleCohortRoot'] ?? '').toString(),
      targetAudience: (json['targetAudience'] ?? 'General Public').toString(),
      organizationName: (json['organizationName'] ?? 'Verified Publisher').toString(),
      questions: (json['questions'] as List<dynamic>?)
              ?.map((q) => SurveyQuestion.fromJson(q as Map<String, dynamic>))
              .toList() ??
          [],
    );
  }
}

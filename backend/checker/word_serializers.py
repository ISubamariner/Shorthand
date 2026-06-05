from rest_framework import serializers

from .models import Word, WordAttemptSession, WordTopic


class WordTopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = WordTopic
        fields = ("id", "name", "slug")


class TeelineComponentSerializer(serializers.Serializer):
    letter = serializers.CharField()
    blend_with = serializers.CharField(allow_null=True)
    is_doubled_for_r = serializers.BooleanField()
    position = serializers.IntegerField()


class WordSerializer(serializers.ModelSerializer):
    topic = WordTopicSerializer(read_only=True)
    components = serializers.SerializerMethodField()

    class Meta:
        model = Word
        fields = ("id", "text", "teeline_letters", "difficulty", "topic", "components")

    def get_components(self, obj):
        from .teeline import decompose

        if obj.is_curated:
            components = [
                {
                    "letter": letter,
                    "blend_with": None,
                    "is_doubled_for_r": False,
                    "position": idx,
                }
                for idx, letter in enumerate(obj.teeline_letters)
            ]
        else:
            components = decompose(obj.text)
        return TeelineComponentSerializer(components, many=True).data


class WordListSerializer(serializers.ModelSerializer):
    topic = WordTopicSerializer(read_only=True)

    class Meta:
        model = Word
        fields = ("id", "text", "teeline_letters", "difficulty", "topic")


class WordSessionCreateSerializer(serializers.Serializer):
    word_id = serializers.UUIDField()


class LetterResultSerializer(serializers.Serializer):
    attempt_id = serializers.CharField()
    is_correct = serializers.BooleanField()


class WordSessionSerializer(serializers.ModelSerializer):
    word = WordSerializer(read_only=True)
    letter_results = serializers.DictField(
        child=LetterResultSerializer(),
        read_only=True,
    )

    class Meta:
        model = WordAttemptSession
        fields = (
            "id", "word", "status", "letters_correct",
            "letters_total", "points_awarded", "letter_results",
        )


class WordProgressSerializer(serializers.Serializer):
    word_id = serializers.CharField()
    word_text = serializers.CharField()
    total_sessions = serializers.IntegerField()
    completed_sessions = serializers.IntegerField()
    perfect_sessions = serializers.IntegerField()
    accuracy = serializers.FloatField()

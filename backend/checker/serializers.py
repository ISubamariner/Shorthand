from rest_framework import serializers

from .models import Attempt, Symbol


class SymbolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Symbol
        fields = ("id", "letter", "name", "reference_image_url")


class AttemptSerializer(serializers.ModelSerializer):
    symbol_letter = serializers.CharField(source="symbol.letter", read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Attempt
        fields = (
            "id",
            "symbol",
            "symbol_letter",
            "image_url",
            "predicted_label",
            "confidence",
            "is_correct",
            "status",
            "points",
            "created_at",
        )
        read_only_fields = (
            "id",
            "image_url",
            "predicted_label",
            "confidence",
            "is_correct",
            "status",
            "points",
            "created_at",
        )

    def get_image_url(self, obj):
        if obj.image_data:
            request = self.context.get("request")
            url = f"/api/attempts/{obj.id}/image/"
            if request:
                return request.build_absolute_uri(url)
            return url
        return ""


class AttemptCreateSerializer(serializers.Serializer):
    symbol_letter = serializers.CharField(max_length=1)
    image_data = serializers.CharField(max_length=700_000, help_text="Base64-encoded PNG image data")
    word_session = serializers.UUIDField(required=False, allow_null=True)
    word_position = serializers.IntegerField(required=False, allow_null=True)


class ProgressSerializer(serializers.Serializer):
    symbol_letter = serializers.CharField(source="symbol__letter")
    total = serializers.IntegerField()
    correct = serializers.IntegerField()
    accuracy = serializers.SerializerMethodField()

    def get_accuracy(self, obj):
        if obj["total"] == 0:
            return 0.0
        return round(obj["correct"] / obj["total"], 4)


class ProgressResponseSerializer(serializers.Serializer):
    symbols = ProgressSerializer(many=True)
    current_streak = serializers.IntegerField()
    best_streak = serializers.IntegerField()
    total_score = serializers.IntegerField()


class LeaderboardEntrySerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    display_name = serializers.CharField()
    total_score = serializers.IntegerField()
    best_streak = serializers.IntegerField()
    is_current_user = serializers.BooleanField()

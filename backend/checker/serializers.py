from rest_framework import serializers

from .models import Attempt, Symbol


class SymbolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Symbol
        fields = ("id", "letter", "name", "reference_image_url")


class AttemptSerializer(serializers.ModelSerializer):
    symbol_letter = serializers.CharField(source="symbol.letter", read_only=True)

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
            "created_at",
        )
        read_only_fields = (
            "id",
            "image_url",
            "predicted_label",
            "confidence",
            "is_correct",
            "status",
            "created_at",
        )


class AttemptCreateSerializer(serializers.Serializer):
    symbol_letter = serializers.CharField(max_length=1)
    image_data = serializers.CharField(help_text="Base64-encoded PNG image data")


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

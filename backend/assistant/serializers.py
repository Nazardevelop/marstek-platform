"""The chat contract. The mock and the real assistant share it, so the FE never changes."""

from typing import Any

from rest_framework import serializers

MAX_MESSAGES = 50
MAX_CHARS = 4000


class ChatMessageSerializer(serializers.Serializer[Any]):
    role = serializers.ChoiceField(choices=["user", "assistant"])
    content = serializers.CharField(max_length=MAX_CHARS, trim_whitespace=True)


class ChatContextSerializer(serializers.Serializer[Any]):
    route = serializers.CharField(required=False, max_length=200, help_text="e.g. /stats")
    device_id = serializers.IntegerField(required=False)
    extra = serializers.DictField(required=False, help_text="Page state, e.g. {range: '7d'}")


class ChatRequestSerializer(serializers.Serializer[Any]):
    messages = ChatMessageSerializer(many=True)

    def get_fields(self) -> dict[str, serializers.Field[Any, Any, Any, Any]]:
        # A class attribute named `context` would shadow Serializer.context (DRF's extra-data
        # dict), so this API field is added here instead.
        fields = super().get_fields()
        fields["context"] = ChatContextSerializer(required=False)
        return fields

    def validate_messages(self, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not value:
            raise serializers.ValidationError("Send at least one message")
        if len(value) > MAX_MESSAGES:
            raise serializers.ValidationError(f"At most {MAX_MESSAGES} messages")
        if value[-1]["role"] != "user":
            raise serializers.ValidationError("The last message must be from the user")
        return value

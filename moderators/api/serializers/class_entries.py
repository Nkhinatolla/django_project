from rest_framework import serializers

from main.models import Visit
from moderators.api.serializers import TrainingListSerializer


class ClassEntriesListSerializer(serializers.ModelSerializer):
    training = TrainingListSerializer()

    class Meta:
        model = Visit
        fields = (
            'id',
            'status',
            'training',
        )

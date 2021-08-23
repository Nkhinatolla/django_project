from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from main.models import Training
from moderators.api.serializers import TemplateListSerializer
from utils import messages
from utils.drf.serializers import ISOTimeSerializer


class TrainingListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Training
        fields = (
            'id',
            'name',
            'timestamp_start',
            'timestamp_end'
        )


class TrainingDetailSerializer(serializers.ModelSerializer):
    sport_type = serializers.CharField(source='sport_type.name')
    template = TemplateListSerializer()

    class Meta:
        model = Training
        fields = (
            'id',
            'name',
            'template',
            'sport_type',
            'timestamp_start',
            'timestamp_end',
            'is_premium',
            'left_users',
            'max_users'
        )


class TrainingCreateSerializer(serializers.ModelSerializer):

    max_users = serializers.IntegerField(required=True)
    template_id = serializers.IntegerField(required=True)

    class Meta:
        model = Training
        fields = (
            'template_id',
            'timestamp_start',
            'timestamp_end',
            'max_users'
        )


class TrainingUpdateSerializer(serializers.ModelSerializer):

    max_users = serializers.IntegerField(required=True)
    template_id = serializers.IntegerField(required=True)

    class Meta:
        model = Training
        fields = (
            'template_id',
            'max_users'
        )


class TrainingPartialSerializer(serializers.Serializer):

    training_ids = serializers.ListField(child=serializers.IntegerField(), required=True)

    def is_valid(self, raise_exception=False, **kwargs):
        super().is_valid(raise_exception)
        training_ids = self.data['training_ids']
        if Training.objects.filter(id__in=training_ids, **kwargs).count() != len(training_ids):
            raise ValidationError(messages.INVALID_DATA)
        return not bool(self._errors)


class TrainingCopySerializer(serializers.Serializer):

    copy_date = ISOTimeSerializer(required=True)
    target_date = ISOTimeSerializer(required=True)
    days = serializers.IntegerField(required=True)

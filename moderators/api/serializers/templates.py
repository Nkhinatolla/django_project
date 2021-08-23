from rest_framework import serializers

from main.api.serializers import SportTypeNameSerializer
from main.models import TrainingTemplate
from main.services.fitness import get_subs_type_by_fitness_sport_type


class TemplateListSerializer(serializers.ModelSerializer):

    class Meta:
        model = TrainingTemplate
        fields = ('id', 'image')


class TrainingTemplateSerializer(serializers.ModelSerializer):
    sport_type = SportTypeNameSerializer()
    subs_type = serializers.SerializerMethodField()

    class Meta:
        model = TrainingTemplate
        fields = ('id', 'name', 'description', 'max_users',
                  'sport_type', 'unlimited',
                  'is_premium', 'image', 'subs_type'
                  )

    def get_subs_type(self, obj):
        return get_subs_type_by_fitness_sport_type(obj.fitness, obj.sport_type)


class TrainingTemplateCreateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True)
    sport_type = serializers.IntegerField(required=True)
    image_id = serializers.IntegerField(source='image', required=False)

    class Meta:
        model = TrainingTemplate
        fields = ('name', 'description', 'image_id', 'sport_type', 'unlimited', 'required_items',
                  'max_users', 'is_premium')


class TrainingTemplateUpdateSerializer(serializers.ModelSerializer):
    image_id = serializers.IntegerField(source='image', required=False)

    class Meta:
        model = TrainingTemplate
        fields = ('name', 'description', 'image_id', 'sport_type', 'unlimited', 'required_items',
                  'max_users', 'is_premium')

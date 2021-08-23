from rest_framework import serializers

from moderators.api.serializers import UserPublicSerializer
from main.models import FitnessImage, FitnessSportType, FitnessUserRatingRequest
from moderators.models import PartnerActions
from studios.models import Studio


class StudioReviewListSerializer(serializers.ModelSerializer):
    user = UserPublicSerializer()

    class Meta:
        model = FitnessUserRatingRequest
        fields = (
            'id',
            'rating',
            'review',
            'timestamp',
            'user'
        )


class StudioImagePriorityEntitySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    priority = serializers.IntegerField()


class StudioImagePrioritySerializer(serializers.Serializer):
    images = StudioImagePriorityEntitySerializer(many=True)


class StudioImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = FitnessImage
        fields = (
            'id',
            'image',
            'priority',
        )


class StudioSportTypeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='sport_type.id')
    name = serializers.CharField(source='sport_type.name')
    slug = serializers.CharField(source='sport_type.slug')

    class Meta:
        model = FitnessSportType
        fields = (
            'id',
            'name',
            'slug',
            'is_premium'
        )


class StudioListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Studio
        fields = ['id', 'name', 'is_active', 'city_id', 'slug']


class StudioDetailSerializer(serializers.ModelSerializer):
    images = StudioImageSerializer(source='image_set', many=True)
    sport_types = StudioSportTypeSerializer(source='sport_type_set', many=True)

    class Meta:
        model = Studio
        fields = ['id', 'name', 'rating',
                  'website', 'email', 'phone', 'address', 'description',
                  'qrcode', 'images', 'sport_types']


class PartnerActionSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.full_name')

    class Meta:
        model = PartnerActions
        fields = ['id', 'user', 'action_type', 'action_info', 'timestamp', 'is_new']
from rest_framework import serializers
from authe.models import MainUser


class UserPublicSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = MainUser
        fields = ('id',
                  'full_name',
                  'avatar')

    def get_avatar(self, obj):
        return obj.avatar.short() if obj.avatar else None


class UserTrainingSerializer(serializers.ModelSerializer):
    class Meta:
        model = MainUser
        fields = ['id', 'full_name', 'phone']


from django.utils.decorators import method_decorator
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from authe.models import MainUser
from main.models import Training
from moderators import services
from utils.decorators import response_code_wrapper
from utils.drf.permissions import IsModerator
from utils.drf.viewsets import ModeratorViewSet
from moderators.api import serializers, filters
from moderators import validators, selectors
from utils.time_utils import datetime_from_iso


@method_decorator(response_code_wrapper(), name='dispatch')
class TrainingViewSet(ModeratorViewSet, viewsets.ModelViewSet):
    serializer_class = serializers.TrainingDetailSerializer
    queryset = Training.objects.all()
    filterset_class = filters.TrainingFilter
    permission_classes = [IsAuthenticated, IsModerator]

    def get_serializer_class(self):
        if self.action == "create":
            return serializers.TrainingCreateSerializer
        if self.action == "update":
            return serializers.TrainingUpdateSerializer
        if self.action == "destroy_partial":
            return serializers.TrainingPartialSerializer
        if self.action == "users":
            return serializers.UserTrainingSerializer
        if self.action == "copy":
            return serializers.TrainingCopySerializer
        return serializers.TrainingDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        training = services.create_or_update_training(self.fitness, serializer.validated_data)
        services.partner_action_create_training(self.request.user, self.fitness, training)
        serializer = serializers.TrainingDetailSerializer(training)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        validators.validate_training_passed(instance)
        training = services.create_or_update_training(self.fitness, serializer.validated_data, instance)
        services.partner_action_update_training(self.request.user, self.fitness, training, serializer.validated_data)
        serializer = serializers.TrainingDetailSerializer(training)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance: Training = self.get_object()
        validators.validate_training_moderator_delete(self.request.user, instance)
        services.partner_action_delete_training(self.request.user, self.fitness, instance)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST'], name='Delete Partial')
    def destroy_partial(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True, fitness_id=self.fitness.id)
        queryset = self.filter_queryset(self.get_queryset()).filter(id__in=serializer.data['training_ids'])
        for instance in queryset:
            validators.validate_training_moderator_delete(self.request.user, instance)
        for instance in queryset:
            services.partner_action_delete_training(self.request.user, self.fitness, instance)
            self.perform_destroy(instance)
        return Response(status=status.HTTP_200_OK)

    @action(detail=True, methods=['GET'], name='Get Booked Users')
    def users(self, request, *args, **kwargs):
        instance: Training = self.get_object()
        users = MainUser.objects.filter(id__in=instance.user_ids)
        serializer = self.get_serializer(users, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['POST'], name='Copy Trainings')
    def copy(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(True)
        week_trainings = selectors.get_trainings_to_copy(self.fitness, serializer.validated_data['copy_date'])
        validators.validate_training_copy_exists(week_trainings)
        trainings = services.copy_trainings(self.fitness, week_trainings,
                                            serializer.validated_data['target_date'], serializer.data['days'])
        return Response(status=status.HTTP_200_OK)


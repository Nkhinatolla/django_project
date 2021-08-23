from django.utils.decorators import method_decorator
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from main.models import TrainingTemplate
from moderators import services
from moderators.api.serializers.templates import TrainingTemplateSerializer, TrainingTemplateCreateSerializer, \
    TrainingTemplateUpdateSerializer
from utils.decorators import response_code_wrapper
from utils.drf.permissions import IsModerator
from utils.drf.viewsets import ModeratorViewSet
from moderators import validators


@method_decorator(response_code_wrapper(), name='dispatch')
class TrainingTemplateViewSet(ModeratorViewSet, viewsets.ModelViewSet):
    queryset = TrainingTemplate.objects.all()
    permission_classes = [IsAuthenticated, IsModerator]

    def get_serializer_class(self):
        if self.action == "create":
            return TrainingTemplateCreateSerializer
        if self.action == "update":
            return TrainingTemplateUpdateSerializer
        return TrainingTemplateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        template = TrainingTemplate(fitness=self.fitness, author=self.request.user)
        validators.is_valid_training_template(self.fitness,
                                              serializer.data.get('is_premium', False),
                                              serializer.data['sport_type'])
        training_template = services.create_training_template(template, serializer.data)
        services.partner_action_create_training_template(
            self.request.user, self.fitness, training_template
        )
        headers = self.get_success_headers(serializer.data)
        serializer = TrainingTemplateSerializer(training_template)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        training_template = services.update_training_template(instance, serializer.data)
        services.partner_action_update_training_template(
            self.request.user, self.fitness, training_template
        )
        headers = self.get_success_headers(serializer.data)
        serializer = TrainingTemplateSerializer(training_template)
        return Response(serializer.data, status=status.HTTP_200_OK, headers=headers)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        services.partner_action_delete_training(
            self.request.user, self.fitness, instance
        )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_200_OK)

    def perform_destroy(self, instance):
        instance.deleted = True
        instance.save(update_fields=['deleted'])






from django.utils.decorators import method_decorator
from rest_framework import viewsets, status
from rest_framework.filters import SearchFilter
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from authe.models import MainUser
from main.models import FitnessImage, FitnessUserRatingRequest
from rest_framework.decorators import action
from moderators.api.filters.studios import StudioFilter
from moderators.models import PartnerActions, PartnerSuperModerator
from moderators import services
from studios.models import Studio

from moderators.api import serializers
from utils.decorators import response_code_wrapper
from utils.drf.permissions import IsModerator
from utils.drf.viewsets import ModeratorViewSet
from utils.pagination import OnefitPagination


@method_decorator(response_code_wrapper(), name='dispatch')
class StudioViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = serializers.StudioListSerializer
    ordering = ["name"]
    filter_backends = [SearchFilter]
    filter_class = StudioFilter
    search_fields = ["name"]
    ordering_fields = ["name"]
    permission_classes = [IsAuthenticated, IsModerator]

    def get_queryset(self):
        user: MainUser = self.request.user
        if user.is_super_moderator:
            return Studio.objects.all()
        return Studio.objects.filter(user_set__user=user)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return serializers.StudioDetailSerializer
        return serializers.StudioListSerializer

    def get_object(self):
        self.kwargs['pk'] = self.kwargs['studio_id']
        return super().get_object()


@method_decorator(response_code_wrapper(), name='dispatch')
class StudioImageViewSet(ModeratorViewSet, viewsets.ModelViewSet):
    serializer_class = serializers.StudioImageSerializer
    queryset = FitnessImage.objects.all()
    permission_classes = [IsAuthenticated, IsModerator]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_serializer_class(self):
        if self.action == "priorities":
            return serializers.StudioImagePrioritySerializer
        return serializers.StudioImageSerializer

    @action(detail=False, methods=['POST'], name='Change Priorities')
    def priorities(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.change_studio_image_priorities(serializer.data['images'])
        return Response(status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_200_OK)


@method_decorator(response_code_wrapper(), name='dispatch')
class StudioReviewsViewSet(ModeratorViewSet, viewsets.ReadOnlyModelViewSet):
    serializer_class = serializers.StudioReviewListSerializer
    queryset = FitnessUserRatingRequest.objects.all()
    pagination_class = OnefitPagination
    permission_classes = [IsAuthenticated, IsModerator]

    def get_paginated_response(self, data, key_field='reviews'):
        """
        Return a paginated style `Response` object for the given output data.
        """
        assert self.paginator is not None
        return self.paginator.get_paginated_response(data, key_field)


@method_decorator(response_code_wrapper(), name='dispatch')
class PartnerActionsViewSet(ModeratorViewSet, viewsets.ReadOnlyModelViewSet):
    serializer_class = serializers.PartnerActionSerializer
    queryset = PartnerActions.objects.all()
    pagination_class = OnefitPagination
    permission_classes = [IsAuthenticated, IsModerator]

    def get_paginated_response(self, data, key_field='partner_actions'):
        """
        Return a paginated style `Response` object for the given output data.
        """
        assert self.paginator is not None
        return self.paginator.get_paginated_response(data, key_field)

    def list(self, request, *args, **kwargs):
        super_moderator = PartnerSuperModerator.objects.first()
        services.partner_actions_update_last_check(self.fitness.id, super_moderator)
        return super(PartnerActionsViewSet, self).list(request, *args, **kwargs)
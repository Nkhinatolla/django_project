from django.utils.decorators import method_decorator
from rest_framework import viewsets, serializers
from rest_framework.permissions import IsAuthenticated

from main.serializers import VisitSerializer
from utils.pagination import OnefitPagination

from moderators.api import filters
from utils.drf.permissions import IsModerator
from main.models import Visit
from utils.decorators import response_code_wrapper
from utils.drf.viewsets import ModeratorViewSet


@method_decorator(response_code_wrapper(), name='dispatch')
class ClassEntriesViewSet(viewsets.ReadOnlyModelViewSet, ModeratorViewSet):
    serializer_class = VisitSerializer
    queryset = Visit.objects.all()
    filterset_class = filters.ClassEntryFilter
    pagination_class = OnefitPagination
    permission_classes = [IsAuthenticated, IsModerator]

    def get_paginated_response(self, data, key_field='visits'):
        """
        Return a paginated style `Response` object for the given output data.
        """
        assert self.paginator is not None
        return self.paginator.get_paginated_response(data, key_field)

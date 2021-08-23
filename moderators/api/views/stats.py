from django.utils.decorators import method_decorator
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from moderators.selectors import get_statistics
from utils.decorators import response_code_wrapper
from utils.drf.permissions import IsModerator
from utils.drf.viewsets import ModeratorViewSet
from utils.time_utils import datetime_from_iso


@method_decorator(response_code_wrapper(), name='dispatch')
class StatisticsViewSet(ModeratorViewSet):
    permission_classes = [IsAuthenticated, IsModerator]

    @extend_schema(parameters=[
        OpenApiParameter("timestamp_start", OpenApiTypes.DATETIME, required=True),
        OpenApiParameter("timestamp_end", OpenApiTypes.DATETIME, required=True)
    ])
    def statistics(self, request, *args, **kwargs):
        timestamp_start = datetime_from_iso(self.request.query_params['timestamp_start'])
        timestamp_end = datetime_from_iso(self.request.query_params['timestamp_end'])
        return Response(get_statistics(timestamp_start, timestamp_end, self.fitness))

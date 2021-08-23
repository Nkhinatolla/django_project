from django_filters import rest_framework as filters
from studios.models import Studio


class StudioFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr='icontains')
    country = filters.NumberFilter(field_name="city__country__id", lookup_expr="exact")
    city = filters.NumberFilter(field_name="city__id", lookup_expr="exact")
    is_active = filters.BooleanFilter(field_name="is_active")

    class Meta:
        model = Studio
        fields = ('name', 'city', 'country', 'is_active')

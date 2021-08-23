import django_filters

from main.models import Visit


class ClassEntryFilter(django_filters.FilterSet):
    timestamp_start = django_filters.IsoDateTimeFilter(
        field_name="training__timestamp_start", lookup_expr="gt",
    )
    timestamp_end = django_filters.IsoDateTimeFilter(
        field_name="training__timestamp_end", lookup_expr="lte"
    )
    timestamp = django_filters.IsoDateTimeFilter(
        field_name="timestamp", lookup_expr="gt"
    )

    class Meta:
        model = Visit
        fields = ("timestamp_start", "timestamp_end", "status")


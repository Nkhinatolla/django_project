import django_filters

from main.models import Training


class TrainingFilter(django_filters.FilterSet):
    timestamp = django_filters.IsoDateTimeFromToRangeFilter(field_name="timestamp_start")

    class Meta:
        model = Training
        fields = ("timestamp", )




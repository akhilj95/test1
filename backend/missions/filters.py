import django_filters as filters
from missions.models import Mission

class MissionFilter(filters.FilterSet):
    start_after = filters.DateTimeFilter(field_name="start_time", lookup_expr="gte")
    start_before = filters.DateTimeFilter(field_name="start_time", lookup_expr="lte")
    max_depth__lt = filters.NumberFilter(field_name="max_depth", lookup_expr="lt")
    target_type = filters.CharFilter(lookup_expr="iexact")

    class Meta:
        model = Mission
        fields = ["rover__name", "target_type"]
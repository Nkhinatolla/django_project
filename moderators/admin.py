from dal import autocomplete
from django.contrib import admin

from main.admin_autocompletes import OneFitModelAdmin
from .models import PartnerSuperModerator, PartnerActions, StatsInfo
from main.admin import FitnessFilter


@admin.register(PartnerSuperModerator)
class PartnerSuperModeratorAdmin(OneFitModelAdmin):
    list_display = ('last_check',)


@admin.register(PartnerActions)
class PartnerActionsAdmin(OneFitModelAdmin):
    list_display = ('id', 'user', 'action_type', 'action_info', 'timestamp', 'is_new')
    dal_fields = {
        "user": autocomplete.ModelSelect2(url="/api/main/user-autocomplete"),
        "fitness": autocomplete.ModelSelect2(url="/api/main/fitness-autocomplete"),
    }
    search_fields = ('action_info', )
    list_filter = (FitnessFilter, 'action_type')


@admin.register(StatsInfo)
class StatsInfoAdmin(OneFitModelAdmin):
    list_display = ('id', 'fitness', 'month', 'year', 'money')
    dal_fields = {
        "fitness": autocomplete.ModelSelect2(url="/api/main/fitness-autocomplete"),
    }
    search_fields = ['fitness__name']
    readonly_fields = ['stats']

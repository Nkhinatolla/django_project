from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models

from course.models import CourseSubscription
from main.models import Fitness, Company

from utils import constants
from utils.time_utils import get_iso_time, validate_month_year
from datetime import datetime


class PartnerActions(models.Model):
    class Meta:
        verbose_name = 'Действие партнера'
        verbose_name_plural = 'Действий партнера'
        ordering = ['-timestamp']

    timestamp = models.DateTimeField(verbose_name='Время')
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.DO_NOTHING,
                             related_name='actions_as_partner')
    action_type = models.CharField(max_length=100,
                                   verbose_name='Действие',
                                   choices=constants.PARTNER_ACTIONS)
    fitness = models.ForeignKey(Fitness,
                                on_delete=models.DO_NOTHING,
                                related_name='actions_as_partner')
    action_info = models.TextField(default='')
    is_new = models.BooleanField(default=True)

    def full(self):
        return {
            'id': self.id,
            'user': str(self.user),
            'action_type': self.action_type,
            'action_info': self.action_info,
            'timestamp': get_iso_time(self.timestamp),
            'is_new': self.is_new
        }


class PartnerSuperModerator(models.Model):
    class Meta:
        verbose_name = 'Нужды супер модераторов'
        verbose_name_plural = 'Нужды супер модераторов'
    last_check = models.DateTimeField(verbose_name='Последняя проверка действии партнеров', default=datetime(2000,10,10))


class StatsInfo(models.Model):
    month = models.PositiveIntegerField(default=0)
    year = models.PositiveIntegerField(default=0)
    money = models.PositiveIntegerField(default=0)
    fitness = models.ForeignKey(Fitness, on_delete=models.CASCADE,
                                related_name='fitness')
    stats = JSONField()

    def __str__(self):
        return '{} - {}'.format(self.fitness, self.money)

    class Meta:
        verbose_name = 'Оплата фитнесс залу'
        verbose_name_plural = 'Оплата фитнесс залам'

        unique_together = [('fitness', 'month', 'year'),]


class AdminPermission(models.Model):
    class Meta:
        managed = False
        default_permissions = ()
        permissions = [
            ('view_admin_menu', 'View admin menu'),
            ('download_hcb_report', 'Download HCB report')
        ]

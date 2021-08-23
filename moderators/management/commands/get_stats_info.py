from django.core.management.base import BaseCommand
from main.models import Visit, Fitness, FitnessThreshold
from utils.time_utils import datetime_from_iso, get_iso_time
from datetime import datetime
import json
from dateutil.relativedelta import relativedelta
from django.test import Client
from moderators.models import StatsInfo
import calendar
from authe.models import MainUser, TokenLog

c = Client()


class Command(BaseCommand):
    help = 'get statistics information'

    def handle(self, *args, **options):
        url = '/api/moderators/statistics/'
        time_start = datetime_from_iso('2018-05-31T18:00:00.000Z')
        time_end = datetime_from_iso('2018-06-30T17:59:59.000Z')
        user = MainUser.objects.get(phone='+71234567890')
        token = TokenLog.objects.filter(user=user, deleted=False).first().token
        try:
            while time_end.year < 2020 or time_end.month < 7:
                for fitness in Fitness.objects.all():
                    fitness_id = fitness.id
                    params = {
                        'timestamp_start': get_iso_time(time_start),
                        'timestamp_end': get_iso_time(time_end)
                    }
                    response = c.get(url, params, content_type='application/json',
                                     HTTP_AUTH_TOKEN=token,
                                     HTTP_FITNESS_ID=fitness_id)
                    month = time_end.month
                    year = time_end.year
                    stats = response.json().get('stats')
                    money = response.json().get('stats').get('money')
                    StatsInfo.objects.create(month=month,
                                             year=year,
                                             stats=stats,
                                             money=money,
                                             fitness=fitness
                                             )
                time_start += relativedelta(months=1)
                time_end += relativedelta(months=1)
                time_start = time_start.replace(day=calendar.monthrange(time_start.year, time_start.month)[1])
                time_end = time_end.replace(day=calendar.monthrange(time_end.year, time_end.month)[1])
                print(time_start, time_end)

        except Exception as error:
            print(str(error))
            StatsInfo.objects.all().delete()

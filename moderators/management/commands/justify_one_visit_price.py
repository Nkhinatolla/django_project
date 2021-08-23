from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Исправить цены за посещение'

    def handle(self, *args, **options):
        from main.models import Visit, FitnessSportType
        from datetime import datetime
        import pytz
        i = 0
        october_begin = datetime.now().replace(year=2020, month=10, day=1, hour=0, minute=0, tzinfo=pytz.UTC)
        october_end = datetime.now().replace(year=2020, month=10, day=31, hour=0, minute=0, tzinfo=pytz.UTC)
        print(october_begin, october_end)
        for visit in Visit.objects.filter(timestamp__gte=october_begin, timestamp__lte=october_end):
            try:
                fitness_sport_type = FitnessSportType.objects.get(fitness=visit.fitness,
                                                                  sport_type=visit.sport_type,
                                                                  is_premium=visit.is_premium)
                if visit.one_visit_price > fitness_sport_type.one_visit_price:
                    i += 1
                    print(
                        f'{visit.id}; Fitness:{visit.fitness}; price: {visit.one_visit_price}; Original: '
                        f'{fitness_sport_type.one_visit_price}')
                    visit.one_visit_price = fitness_sport_type.one_visit_price
                    visit.save()
            except Exception as e:
                print('Exception:', str(e))

        print(i)

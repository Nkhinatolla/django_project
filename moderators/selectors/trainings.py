from datetime import timedelta
from main.models import Training


def get_trainings_to_copy(fitness, copy_date):
    week_trainings = []
    for i in range(7):
        trainings = Training.objects.filter_by_date(fitness, copy_date)
        copy_date = copy_date + timedelta(days=1)
        week_trainings.append(trainings)

    return week_trainings

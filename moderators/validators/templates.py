from main.models import FitnessSportType
from utils import messages


def is_valid_training_template(fitness, is_premium, sport_type):
    fitness_sport_type = FitnessSportType.objects.filter(fitness=fitness,
                                                         sport_type_id=sport_type,
                                                         is_premium=is_premium)
    if not fitness_sport_type.exists():
        raise Exception(messages.FITNESS_SPORT_TYPE_NOT_EXIST)

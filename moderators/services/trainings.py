import copy
from datetime import timedelta

from main.models import Training, TrainingRepeat
from moderators.selectors import get_trainings_to_copy
from moderators.validators import validate_training_copy_exists
from utils import constants
from utils.time_utils import datetime_from_iso


def create_or_update_training(fitness, body, training=None):
    from main.tasks import repeat_training
    template = fitness.training_templates.get(id=int(body['template_id']))
    if not training:
        training = Training(fitness=fitness, template=template)
    training.template = template
    training.name = template.name
    training.description = template.description
    training.required_items = template.required_items
    training.sport_type = template.sport_type
    training.max_users = int(body.get('max_users', template.max_users))
    training.coach = body.get('coach', template.coach)
    training.is_premium = template.is_premium
    if datetime_from_iso(body.get('timestamp_start')):
        training.timestamp_start = datetime_from_iso(body.get('timestamp_start'))
    if datetime_from_iso(body.get('timestamp_end')):
        training.timestamp_end = datetime_from_iso(body.get('timestamp_end'))
    training.save()
    if body.get('repeat_type') == constants.WEEKLY:
        training_repeat = TrainingRepeat.objects.create(body=body,
                                                        training=training)
        training.training_repeat = training_repeat
        training.save()
        training = Training.objects.filter(training_repeat=training_repeat).last()
        repeat_training.delay(body=body, training_id=training.id)
    return training


def copy_trainings(fitness, week_trainings, target_date, days):

    total_copied_trainings = []
    for i in range(days):
        weekday = target_date.weekday()
        existing_trainings = Training.objects.filter_by_date(fitness,
                                                             target_date)
        for training in week_trainings[weekday]:
            found = False
            for existing_training in existing_trainings:
                if existing_training.same(training):
                    found = True
                    break
            if found:
                continue
            new_training = copy.deepcopy(training)
            new_training.pk = None
            new_training.visits.all().delete()
            new_training.timestamp_start = training.timestamp_start.replace(
                day=target_date.day, month=target_date.month,
                year=target_date.year)
            new_training.timestamp_end = training.timestamp_end.replace(
                day=target_date.day, month=target_date.month,
                year=target_date.year)
            new_training.training_repeat = training.training_repeat
            # new_training.left_users = 0
            new_training.init()
            total_copied_trainings.append(new_training)
        target_date = target_date + timedelta(days=1)
    Training.objects.bulk_create(total_copied_trainings)

    return total_copied_trainings

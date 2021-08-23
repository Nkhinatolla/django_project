from moderators.models import PartnerActions, PartnerSuperModerator
from django.utils import timezone
from utils import constants


def partner_actions_update_last_check(fitness_id, moderator: PartnerSuperModerator):
    for action in PartnerActions.objects.filter(fitness_id=fitness_id, timestamp__gt=moderator.last_check):
        action.is_new = False
        action.save()

    moderator.last_check = timezone.now()
    moderator.save()


def partner_action_create_training(user, fitness, training):
    PartnerActions.objects.create(user=user,
                                  fitness=fitness,
                                  timestamp=timezone.now(),
                                  action_type=constants.CREATED_SCHEDULE,
                                  action_info='{}'.format(training))


def partner_action_update_training(user, fitness, training, fields):
    PartnerActions.objects.create(user=user,
                                  fitness=fitness,
                                  timestamp=timezone.now(),
                                  action_type=constants.UPDATED_SCHEDULE,
                                  action_info='{0}: {1}'.format(training, fields))


def partner_action_delete_training(user, fitness, training):
    PartnerActions.objects.create(user=user,
                                  fitness=fitness,
                                  timestamp=timezone.now(),
                                  action_type=constants.REMOVED_SCHEDULE,
                                  action_info='{0}'.format(training))


def partner_action_create_training_template(user, fitness, training_template):
    PartnerActions.objects.create(user=user,
                                  fitness=fitness,
                                  timestamp=timezone.now(),
                                  action_type=constants.CREATED_TRAINING,
                                  action_info='{}'.format(training_template))


def partner_action_update_training_template(user, fitness, training_template):
    PartnerActions.objects.create(user=user,
                                  fitness=fitness,
                                  timestamp=timezone.now(),
                                  action_type=constants.UPDATED_TRAINING,
                                  action_info='{}'.format(training_template))


def partner_action_delete_training_template(user, fitness, training_template):
    PartnerActions.objects.create(user=user,
                                  fitness=fitness,
                                  timestamp=timezone.now(),
                                  action_type=constants.REMOVED_TRAINING,
                                  action_info='{}'.format(training_template))

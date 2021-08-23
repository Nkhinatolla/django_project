from datetime import timedelta
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from main.models import Training
from utils import messages
from django.utils.translation import gettext


def validate_training_passed(training: Training):
    if training.timestamp_start < timezone.now():
        raise ValidationError(gettext(messages.DELETE_PASSED_TRAINING_NOT_ALLOWED))


def validate_training_moderator_delete(user, training: Training):
    validate_training_passed(training)
    if not user.is_super_moderator and timezone.now() > training.timestamp_start - timedelta(hours=2):
        raise ValidationError(gettext(messages.CANCELLATION_TIME))


def validate_training_copy_exists(trainings):
    if len(trainings) == 0:
        raise ValidationError(gettext(messages.NOTHING_TO_COPY))

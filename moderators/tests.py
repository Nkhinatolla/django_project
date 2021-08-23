from datetime import timedelta, datetime

from django.utils import timezone

from django.contrib.auth import get_user_model
from django.test import Client
from django.test import TestCase
from django.urls import reverse
from freezegun import freeze_time

from ban_system.models import BanStatus
from locations.models import Country
from main.models import Company, Fitness, FitnessUserEntry, Training, \
    TrainingTemplate, SportType, FitnessSportType, \
    FitnessThreshold, Visit, LimitEntry, City
from referrals.models import ReferralSystem
from subscription.models import SubscriptionType, Subscription, UserSubscription
from main.views import book, get_visits
from payments.models import PayBoxTransaction
from utils import codes, token, constants
from faker import Faker
import json

from utils.cloud_payments import process_success_subscription_purchase_paybox
from utils.time_utils import get_iso_time

CODE = 'code'
STATUS_OK = 200
c = Client()
AUTH_TOKEN_HEADER = 'Auth-Token'
User = get_user_model()


class BaseTestCase(TestCase):
    @classmethod
    def setUpTestData(self):
        self.fake = Faker('ru_RU')
        with open('static/assets/bg.jpg', 'rb') as f:
            self.image = f.read()
        # from PIL import Image
        # im = Image.open("")
        self.country = Country.objects.create(name="Kazakhstan", code='KZ')
        self.city = City.objects.create(
            name='Almaty',
            country_id=self.country.id,
            description='Almaty description',
            is_active=True,
            region_code='ALA'
        )
        self.referral_system = ReferralSystem.objects.create(
            is_active=True,
            sender_reward_type=constants.EXACT,
            sender_reward_value=5000,
            receiver_reward_type=ReferralSystem.BONUS,
            receiver_reward_value=3000,
            country=self.country
        )
        self.company = Company.objects.create(name=self.fake.word(),
                                              address=self.fake.address())
        self.phone = self.fake.phone_number()
        self.email = self.fake.email()
        self.user = User.objects.create(phone=self.phone, email=self.email,
                                        is_moderator=True, company=self.company)
        self.password = self.fake.word()
        self.user.set_password(self.password)
        self.user.save()
        self.token = token.create_token(self.user)
        self.fitness = Fitness.objects.create(name=self.fake.word(),
                                              address=self.fake.address(),
                                              company=self.company,
                                              phone=self.fake.phone_number(),
                                              one_visit_price=self.fake.pyint(),
                                              unlimited_price=self.fake.pyint(),
                                              city=self.city,
                                              country=self.country,
                                              latitude=43.232283,
                                              longitude=76.948573)
        self.sport_type = SportType.objects.create(name=self.fake.word())
        FitnessSportType.objects.create(fitness=self.fitness, sport_type=self.sport_type)
        self.training_template = TrainingTemplate.objects.create(author=self.user,
                                                                 fitness=self.fitness,
                                                                 sport_type_id=self.sport_type.id)
        self.training = Training.objects.from_json(self.fitness,
                                                   body={'template_id': self.training_template.id,
                                                         'timestamp_start': self.fake.iso8601(tzinfo=None),
                                                         'timestamp_end': self.fake.iso8601(tzinfo=None)
                                                         }
                                                   )
        self.fitness_user_entry = FitnessUserEntry.objects.create(user=self.user,
                                                                  fitness=self.fitness)

    def common_test(self, response, status_code, code):
        self.assertEqual(response.status_code, status_code)
        self.assertEqual(response.json()[CODE], code)

    def common_test_without_json(self, response, status_code):
        self.assertEqual(response.status_code, status_code)

    def post_params_form_data(self, url, params, status_code, code):
        response = c.post(url, params, HTTP_AUTH_TOKEN=self.token)
        self.common_test(response, status_code, code)

    def post_params(self, url, params, status_code, code, user_token=None):
        if user_token:
            response = c.post(url, json.dumps(params),
                              HTTP_AUTH_TOKEN=user_token,
                              HTTP_FITNESS_ID=self.fitness.id,
                              content_type='application/json')
        else:
            response = c.post(url, json.dumps(params),
                              HTTP_AUTH_TOKEN=self.token,
                              HTTP_FITNESS_ID=self.fitness.id,
                              content_type='application/json')
        self.common_test(response, status_code, code)

    def get_params(self, url, params, status_code, code, user_token=None):
        if user_token:
            response = c.get(url, params, content_type='application/json',
                             HTTP_AUTH_TOKEN=user_token,
                             HTTP_FITNESS_ID=self.fitness.id)
        else:
            response = c.get(url, params, content_type='application/json',
                             HTTP_AUTH_TOKEN=self.token,
                             HTTP_FITNESS_ID=self.fitness.id)
        self.common_test(response, status_code, code)


class ModeratorsTestCase(BaseTestCase):

    def test_get_fitnesses_ok(self):
        url = '/api/moderators/fitnesses/'
        self.get_params(url=url, params={}, status_code=STATUS_OK,
                        code=codes.OK)

    def test_get_trainings_ok(self):
        url = '/api/moderators/trainings/'
        params = {
            'timestamp_start': self.fake.iso8601(tzinfo=None),
            'timestamp_end': self.fake.iso8601(tzinfo=None)
        }
        self.get_params(url=url, params=params, status_code=STATUS_OK,
                        code=codes.OK)

    def test_get_trainings_invalid_dates(self):
        url = '/api/moderators/trainings/'
        params = {
            'timestamp_start': self.fake.iso8601(tzinfo=None)
        }
        self.get_params(url=url, params=params, status_code=STATUS_OK,
                        code=codes.MISSING_REQUIRED_PARAMS)

    def test_get_trainings_permission_denied_not_moderator(self):
        url = '/api/moderators/trainings/'
        user = User.objects.create(phone=self.fake.phone_number())
        user_token = token.create_token(user)
        params = {
            'timestamp_start': self.fake.iso8601(tzinfo=None),
            'timestamp_end': self.fake.iso8601(tzinfo=None)
        }
        self.get_params(url=url, params=params, status_code=STATUS_OK,
                        code=codes.BAD_REQUEST, user_token=user_token)

    def test_get_trainings_permission_denied_different_company(self):
        url = '/api/moderators/trainings/'
        user = User.objects.create(phone=self.fake.phone_number(),
                                   is_moderator=True)
        user_token = token.create_token(user)
        params = {
            'timestamp_start': self.fake.iso8601(tzinfo=None),
            'timestamp_end': self.fake.iso8601(tzinfo=None)
        }
        self.get_params(url=url, params=params, status_code=STATUS_OK,
                        code=codes.BAD_REQUEST, user_token=user_token)

    def test_create_training_ok(self):
        url = '/api/moderators/trainings/create/'
        params = {
            'timestamp_start': self.fake.iso8601(tzinfo=None),
            'timestamp_end': self.fake.iso8601(tzinfo=None),
            'template_id': self.training_template.id
        }
        self.post_params(url=url, params=params, status_code=STATUS_OK,
                         code=codes.OK)

    def test_delete_training_ok(self):
        url = '/api/moderators/trainings/delete/'
        params = {
            'training_id': self.training.id
        }
        user_token = None
        response = c.post(url, json.dumps(params),
                          HTTP_AUTH_TOKEN=user_token,
                          HTTP_FITNESS_ID=self.fitness.id,
                          content_type='application/json')
        self.assertEqual(response.status_code, STATUS_OK)

    def test_get_visits_ok(self):
        url = '/api/moderators/visits/'
        params = {
            'timestamp_start': self.fake.iso8601(tzinfo=None),
            'timestamp_end': self.fake.iso8601(tzinfo=None),
            'sport_type': self.sport_type.id
        }
        user_token = None
        response = c.get(url, params, content_type='application/json',
                         HTTP_AUTH_TOKEN=user_token,
                         HTTP_FITNESS_ID=self.fitness.id)
        self.assertEqual(response.status_code, STATUS_OK)

    def test_get_visits_invalid_dates(self):
        url = '/api/moderators/visits/'
        params = {
            'timestamp_start': self.fake.iso8601(tzinfo=None),
            'sport_type': self.sport_type.id
        }
        user_token = None
        response = c.get(url, params, content_type='application/json',
                         HTTP_AUTH_TOKEN=user_token,
                         HTTP_FITNESS_ID=self.fitness.id)
        self.assertEqual(response.status_code, STATUS_OK)

    def test_get_stats_ok(self):
        url = '/api/moderators/statistics/'
        params = {
            'timestamp_start': self.fake.iso8601(tzinfo=None),
            'timestamp_end': self.fake.iso8601(tzinfo=None)
        }
        self.get_params(url=url, params=params, status_code=STATUS_OK,
                        code=codes.OK)

    def test_get_stats_invalid_dates(self):
        url = '/api/moderators/statistics/'
        params = {
            'timestamp_start': self.fake.iso8601(tzinfo=None)
        }
        self.get_params(url=url, params=params, status_code=STATUS_OK,
                        code=codes.MISSING_REQUIRED_PARAMS)

    # def test_sport_type_image_upload(self):
    #     url = '/api/moderators/fitness/sport_type/image/upload/'
    #
    #     params = {
    #         'sport_type_id': self.sport_type.id,
    #         'image': self.image
    #     }
    #     self.post_params_form_data(url=url, params=params, status_code=STATUS_OK,
    #                                code=codes.OK)

    def test_update_template_ok(self):
        url = '/api/moderators/templates/update/'
        params = {
            'id': self.training_template.id,
            'name': self.fake.word(),
            'max_users': self.fake.pyint(),
            'sport_type': self.sport_type.id,
        }
        self.post_params(url=url, params=params, status_code=STATUS_OK,
                         code=codes.OK)

    def test_delete_template_ok(self):
        url = '/api/moderators/templates/delete/'
        params = {
            'id': self.training_template.id
        }
        self.post_params(url=url, params=params, status_code=STATUS_OK,
                         code=codes.OK)

    def test_get_templates_ok(self):
        url = '/api/moderators/templates/'
        self.get_params(url=url, params={}, status_code=STATUS_OK, code=codes.OK)

    def test_get_company_ok(self):
        url = '/api/moderators/company/'
        params = {
            'company_id': self.company.id
        }
        self.get_params(url=url, params=params, status_code=STATUS_OK,
                        code=codes.OK)


@freeze_time("2020-07-02", as_arg=True)
class FitnessTestCase(TestCase):
    @classmethod
    def setUpTestData(self):
        self.fake = Faker('ru_RU')
        self.country = Country.objects.create(name="Kazakhstan", code='KZ')
        self.city = City.objects.create(
            name='Almaty',
            country_id=self.country.id,
            description='Almaty description',
            is_active=True,
            region_code='ALA'
        )
        self.referral_system = ReferralSystem.objects.create(
            is_active=True,
            sender_reward_type=constants.EXACT,
            sender_reward_value=5000,
            receiver_reward_type=ReferralSystem.BONUS,
            receiver_reward_value=3000,
            country=self.country
        )
        self.phone = self.fake.phone_number()
        self.email = self.fake.email()
        self.user = User.objects.create(phone=self.phone, email=self.email, is_super_moderator=True, is_moderator=True)
        self.regular_ban_status = BanStatus.objects.create(
            title='Регуляр',
            emoji='Регуляр',
            description='Доступно неограниченное количество единовременных записей на тренировки.',
            status_type=BanStatus.REGULAR,
        )
        self.password = self.fake.word()
        self.user.set_password(self.password)
        self.user.save()
        self.token = token.create_token(self.user)
        self.company = Company.objects.create(name=self.fake.word(),
                                              address=self.fake.address())
        self.fitness = Fitness.objects.create(name=self.fake.word(),
                                              company=self.company,
                                              latitude=43.232283,
                                              longitude=76.948573,
                                              country=self.country,
                                              city=self.city)
        """
            4 sport types: dance, group, gym, massage
        """
        self.dance = SportType.objects.create(name=self.fake.word())
        self.group = SportType.objects.create(name=self.fake.word())
        self.gym = SportType.objects.create(name=self.fake.word())
        self.massage = SportType.objects.create(name=self.fake.word())
        self.dance_fitness = FitnessSportType.objects.create(fitness=self.fitness, one_visit_price=1000,
                                                             sport_type=self.dance)
        self.dance_fitness_premium = FitnessSportType.objects.create(fitness=self.fitness, one_visit_price=1500,
                                                                     sport_type=self.dance, is_premium=True)

        self.group_fitness = FitnessSportType.objects.create(fitness=self.fitness, one_visit_price=1000,
                                                             sport_type=self.group)
        self.gym_fitness = FitnessSportType.objects.create(fitness=self.fitness, one_visit_price=800,
                                                           sport_type=self.gym)
        self.gym_fitness_premium = FitnessSportType.objects.create(fitness=self.fitness, one_visit_price=1500,
                                                                   sport_type=self.gym, is_premium=True)
        self.massage_fitness_premium = FitnessSportType.objects.create(fitness=self.fitness, one_visit_price=3500,
                                                                       sport_type=self.massage, is_premium=True)
        self.dance_threshold = FitnessThreshold.objects.create(fitness=self.fitness, threshold=True,
                                                               threshold_limit=4, threshold_price=3500)

        self.dance_threshold.sport_types.add(self.dance)
        self.dance_threshold.sport_types.add(self.group)
        self.dance_threshold_premium = FitnessThreshold.objects.create(fitness=self.fitness, threshold=True,
                                                                       threshold_limit=8, threshold_price=5000,
                                                                       is_premium=True)
        self.dance_threshold_premium.sport_types.add(self.dance)
        self.gym_threshold = FitnessThreshold.objects.create(fitness=self.fitness, threshold=True,
                                                             threshold_limit=5, threshold_price=4000)
        self.gym_threshold.sport_types.add(self.gym)
        self.gym_threshold_premium = FitnessThreshold.objects.create(fitness=self.fitness, threshold=False,
                                                                     is_premium=True)
        self.dance_threshold_premium.sport_types.add(self.gym)
        self.massage_threshold = FitnessThreshold.objects.create(fitness=self.fitness, is_premium=True)
        self.massage_threshold.sport_types.add(self.massage)
        self.dance_template = TrainingTemplate.objects.create(fitness=self.fitness, sport_type=self.dance)
        self.dance_template_premium = TrainingTemplate.objects.create(fitness=self.fitness,
                                                                      sport_type=self.dance, is_premium=True)
        self.group_template = TrainingTemplate.objects.create(fitness=self.fitness, sport_type=self.group)
        self.gym_template = TrainingTemplate.objects.create(fitness=self.fitness, sport_type=self.gym)
        self.gym_template_premium = TrainingTemplate.objects.create(fitness=self.fitness,
                                                                    sport_type=self.gym, is_premium=True)
        self.massage_template = TrainingTemplate.objects.create(fitness=self.fitness, sport_type=self.massage,
                                                                is_premium=True)
        self.dance_training = Training.objects.from_json(self.fitness,
                                                         body={'template_id': self.dance_template.id,
                                                               'timestamp_start': get_iso_time(
                                                                   timezone.now() + timedelta(hours=1)),
                                                               'timestamp_end': get_iso_time(
                                                                   timezone.now() + timedelta(hours=1, minutes=2))
                                                               }
                                                         )
        self.dance_training_premium = Training.objects.from_json(self.fitness,
                                                                 body={'template_id': self.dance_template_premium.id,
                                                                       'timestamp_start': get_iso_time(
                                                                           timezone.now() + timedelta(hours=1,
                                                                                                      minutes=2)),
                                                                       'timestamp_end': get_iso_time(
                                                                           timezone.now() + timedelta(hours=1,
                                                                                                      minutes=4))
                                                                       }
                                                                 )
        self.group_training = Training.objects.from_json(self.fitness,
                                                         body={'template_id': self.group_template.id,
                                                               'timestamp_start': get_iso_time(
                                                                   timezone.now() + timedelta(hours=1, minutes=4)),
                                                               'timestamp_end': get_iso_time(
                                                                   timezone.now() + timedelta(hours=1, minutes=6))
                                                               }
                                                         )
        self.gym_training = Training.objects.from_json(self.fitness,
                                                       body={'template_id': self.gym_template.id,
                                                             'timestamp_start': get_iso_time(
                                                                 timezone.now() + timedelta(hours=1, minutes=6)),
                                                             'timestamp_end': get_iso_time(
                                                                 timezone.now() + timedelta(hours=1, minutes=8))
                                                             }
                                                       )

        self.gym_training_premium = Training.objects.from_json(self.fitness,
                                                               body={'template_id': self.gym_template_premium.id,
                                                                     'timestamp_start': get_iso_time(
                                                                         timezone.now() + timedelta(hours=1,
                                                                                                    minutes=6)),
                                                                     'timestamp_end': get_iso_time(
                                                                         timezone.now() + timedelta(hours=1, minutes=8))
                                                                     }
                                                               )
        self.massage_training = Training.objects.from_json(self.fitness,
                                                           body={'template_id': self.massage_template.id,
                                                                 'timestamp_start': get_iso_time(
                                                                     timezone.now() + timedelta(hours=1, minutes=8)),
                                                                 'timestamp_end': get_iso_time(
                                                                     timezone.now() + timedelta(hours=1, minutes=10))
                                                                 }
                                                           )
        self.dance_training2 = Training.objects.from_json(self.fitness,
                                                          body={'template_id': self.dance_template.id,
                                                                'timestamp_start': get_iso_time(
                                                                    timezone.now() + timedelta(hours=1, minutes=10)),
                                                                'timestamp_end': get_iso_time(
                                                                    timezone.now() + timedelta(hours=1, minutes=12))
                                                                }
                                                          )

        self.dance_training3 = Training.objects.from_json(self.fitness,
                                                          body={'template_id': self.dance_template.id,
                                                                'timestamp_start': get_iso_time(
                                                                    timezone.now() + timedelta(hours=1, minutes=12)),
                                                                'timestamp_end': get_iso_time(
                                                                    timezone.now() + timedelta(hours=1, minutes=14))
                                                                }
                                                          )

        self.dance_training4 = Training.objects.from_json(self.fitness,
                                                          body={'template_id': self.dance_template.id,
                                                                'timestamp_start': get_iso_time(
                                                                    timezone.now() + timedelta(hours=1, minutes=14)),
                                                                'timestamp_end': get_iso_time(
                                                                    timezone.now() + timedelta(hours=1, minutes=16))
                                                                }
                                                          )

        url = '/api/moderators/trainings/copy/'
        params = {
            'copy_date': get_iso_time(timezone.now()),
            'target_date': get_iso_time(timezone.now() + timedelta(weeks=1)),
            'days': 7
        }
        response = c.post(url, json.dumps(params),
                          HTTP_AUTH_TOKEN=self.token,
                          HTTP_FITNESS_ID=self.fitness.id,
                          content_type='application/json')

        self.promocode = 'ESxrkLjRVa'
        self.standard = SubscriptionType.objects.create(subscription_type=constants.SUBSCRIPTION_STANDARD)
        self.trial = SubscriptionType.objects.create(subscription_type=constants.SUBSCRIPTION_TRIAL)
        self.premium = SubscriptionType.objects.create(subscription_type=constants.SUBSCRIPTION_PREMIUM)
        self.one_month_free_trial_subscription = Subscription.objects.create(
            months=1, subscription_type=self.trial, free_trial=True)
        self.one_month_standard_subscription = Subscription.objects.create(
            months=1, subscription_type=self.standard)
        self.one_month_premium_subscription = Subscription.objects.create(
            months=1, subscription_type=self.premium)
        self.one_month_free_trial_subscription.cities.add(self.city)
        self.one_month_standard_subscription.cities.add(self.city)
        self.one_month_premium_subscription.cities.add(self.city)

        LimitEntry.objects.create(subscription_type=self.premium, fitness=self.fitness,
                                  sport_type_ids=[self.dance.id], limit=15)
        LimitEntry.objects.create(subscription_type=self.standard, fitness=self.fitness,
                                  sport_type_ids=[self.dance.id, self.group.id], limit=10)
        LimitEntry.objects.create(subscription_type=self.premium, fitness=self.fitness,
                                  sport_type_ids=[self.group.id], limit=10)
        LimitEntry.objects.create(subscription_type=self.standard, fitness=self.fitness,
                                  sport_type_ids=[self.gym.id], limit=30)
        LimitEntry.objects.create(subscription_type=self.premium, fitness=self.fitness,
                                  sport_type_ids=[self.gym.id], limit=35)
        LimitEntry.objects.create(subscription_type=self.premium, fitness=self.fitness,
                                  sport_type_ids=[self.massage.id], limit=4)
        LimitEntry.objects.create(subscription_type=self.trial, fitness=self.fitness,
                                  sport_type_ids=[self.dance.id, self.group.id], limit=1)
        LimitEntry.objects.create(subscription_type=self.trial, fitness=self.fitness,
                                  sport_type_ids=[self.gym.id], limit=1)

    def declare_purchase(self, test_user, test_subs):
        pay_box_transaction = \
            PayBoxTransaction.objects.create(user=test_user,
                                             subscription_id=test_subs.id,
                                             email=test_user.email,
                                             description=self.fake.word(),
                                             amount=UserSubscription.calculate_total_price(test_user, test_subs)[1],
                                             payment_type=constants.TO_TRAIN
                                             )
        return process_success_subscription_purchase_paybox(transaction=pay_box_transaction)

    def abstract_method_subscription(self, subscription, threshold=False):
        frozen_thread = freeze_time("2020-07-02")
        frozen_time = frozen_thread.start()
        today = timezone.now() - timedelta(hours=1)
        frozen_time.move_to(get_iso_time(today))
        self.declare_purchase(self.user, subscription)

        url_book = reverse('main:book')
        response = []

        if subscription.subscription_type.subscription_type == 'Freetrial':
            params_book = {'training_id': self.dance_training.id}
            res = c.post(url_book, json.dumps(params_book), content_type='application/json',
                         HTTP_AUTH_TOKEN=self.token)
            response.append(res)
        elif subscription.subscription_type.subscription_type == 'Premium':
            for train in Training.objects.all():
                params_book = {'training_id': train.id}
                res = c.post(url_book, json.dumps(params_book), content_type='application/json',
                             HTTP_AUTH_TOKEN=self.token)
                response.append(res)
        elif subscription.subscription_type.subscription_type == 'Standard':
            for train in Training.objects.all():
                if not train.template.is_premium:
                    params_book = {'training_id': train.id}
                    res = c.post(url_book, json.dumps(params_book), content_type='application/json',
                                 HTTP_AUTH_TOKEN=self.token)
                    response.append(res)

        today = timezone.now() + timedelta(hours=1, minutes=30)
        frozen_time.move_to(get_iso_time(today))

        kwargs = {'promocode': self.fitness.promocode}
        url2 = reverse('main:scan_qr', kwargs=kwargs)
        for resp in response:
            payload = {
                'visit_id': resp.json()['visit']['id'],
                'latitude': self.fitness.latitude,
                'longitude': self.fitness.longitude
            }
            c.post(url2, data=payload, content_type='application/json', HTTP_AUTH_TOKEN=self.token)

        if threshold:
            today = timezone.now() + timedelta(weeks=1)
            frozen_time.move_to(get_iso_time(today))

            for resp in response[len(response) // 2:]:
                payload = {
                    'visit_id': resp.json()['visit']['id'],
                    'latitude': self.fitness.latitude,
                    'longitude': self.fitness.longitude
                }
                c.post(url2, data=payload, content_type='application/json', HTTP_AUTH_TOKEN=self.token)

        url3 = '/api/moderators/statistics/'
        params3 = {
            'timestamp_start': get_iso_time(timezone.now() - timedelta(days=30)),
            'timestamp_end': get_iso_time(timezone.now() + timedelta(hours=5))
        }
        response = c.get(url3, params3, content_type='application/json',
                         HTTP_AUTH_TOKEN=self.token,
                         HTTP_FITNESS_ID=self.fitness.id)
        frozen_thread.stop()
        return response.status_code, response.json()["stats"]["user_data"][0]["visit_count"], \
               response.json()["stats"]["user_data"][0]["total_price"]

    def test_free_trial_subscription(self):
        status_code, visits, money = self.abstract_method_subscription(self.one_month_free_trial_subscription)
        self.assertEqual(status_code, STATUS_OK)
        self.assertEqual(visits, 1)
        self.assertEqual(money, 1000)

    def test_premium_subscription(self):
        status_code, visits, money = self.abstract_method_subscription(self.one_month_premium_subscription)
        self.assertEqual(status_code, STATUS_OK)
        self.assertEqual(visits, 9)
        self.assertEqual(money, 15000)

    def test_standard_subscription(self):
        status_code, visits, money = self.abstract_method_subscription(self.one_month_standard_subscription)

        self.assertEqual(status_code, STATUS_OK)
        self.assertEqual(visits, 6)
        self.assertEqual(money, 4300)

    def test_threshold_standard(self):
        status_code, visits, money = self.abstract_method_subscription(self.one_month_standard_subscription,
                                                                       threshold=True)
        self.assertEqual(status_code, STATUS_OK)
        self.assertEqual(visits, len(Visit.objects.all()))
        self.assertEqual(money, 5100)

    # def test_threshold_premium(self):
    #     status_code, visits, money = self.abstract_method_subscription(self.one_month_premium_subscription,
    #                                                                    threshold=True)
    #     self.assertEqual(status_code, STATUS_OK)
    #     self.assertEqual(visits, 18)
    #     self.assertEqual(money, 14000)

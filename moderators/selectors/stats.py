from collections import defaultdict

from main.models import Visit, Training, SportType
from moderators.models import StatsInfo
from utils.constants import APPROVED
from dashboard.stats.partner_payouts import init_default_dict
from utils.time_utils import get_iso_time
from django.utils import timezone


def get_stats_info(month, year, fitness):
    return StatsInfo.objects.filter(month=month, year=year, fitness=fitness).first()


def get_statistics(timestamp_start, timestamp_end, fitness):
    stats_info = get_stats_info(timestamp_end.month, timestamp_end.year, fitness)
    if stats_info:
        return stats_info.stats

    visit_query = {'fitness_id': fitness.id,
                   'status': APPROVED,
                   'training__timestamp_start__range': (timestamp_start, timestamp_end)}
    training_query = {'fitness_id': fitness.id, 'timestamp_start__range': (timestamp_start, timestamp_end)}
    visits = Visit.objects.select_related('user__avatar', 'training').filter(**visit_query)
    stats = {
        'trainings': Training.objects.filter(**training_query).count(),
        'visits': visits.count(),
        'users': visits.order_by('user').distinct('user').count(),
        'user_data': [],
        'sport_types': [],
        'money': 0,
    }
    user_limits = defaultdict(lambda: defaultdict(init_default_dict))
    user_datas = {}

    for visit in visits:
        user = visit.user
        ft_id = visit.fitness_threshold_id if visit.fitness_threshold_id else -1
        user_limits[user.id][ft_id]['visit_count'] += 1
        user_limits[user.id][ft_id]['total_price'] += visit.one_visit_price
        user_limits[user.id][ft_id]['has_threshold'] |= visit.has_threshold
        user_limits[user.id][ft_id]['threshold_price'] = max(visit.threshold_price,
                                                             user_limits[user.id][ft_id]['threshold_price'])
        user_limits[user.id][ft_id]['threshold'] = max(visit.threshold, user_limits[user.id][ft_id]['threshold'])
        if user.id not in user_datas:
            user_data = {
                'id': user.id,
                'full_name': user.full_name,
                'avatar': user.avatar.full() if user.avatar else None,
                'visit_count': 0,
                'total_money': 0,
                'visits': []
            }
            user_datas[user.id] = user_data
        visit_short = {
            'id': visit.id,
            'training': {
                'timestamp_start': get_iso_time(visit.training.timestamp_start),
                'timestamp_end': get_iso_time(visit.training.timestamp_end),
                'name': visit.training.name,
                'id': visit.training.id
            }
        }
        user_datas[user.id]['visits'].append(visit_short)

    for user_id, fitness_thresholds in user_limits.items():
        user_visit_count = 0
        user_total_money = 0
        for limit in fitness_thresholds.values():
            if limit['has_threshold'] and limit['visit_count'] >= limit['threshold']:
                limit['total_price'] = limit['threshold_price']
            user_visit_count += limit['visit_count']
            user_total_money += limit['total_price']
        user_datas[user_id]['visit_count'] = user_visit_count
        user_datas[user_id]['total_price'] = user_total_money
        stats['money'] += user_total_money
        stats['user_data'].append(user_datas[user_id])

    for s in SportType.objects.all():
        info = {'name': s.name, 'count': visits.filter(sport_type_id=s.id).count()}
        stats['sport_types'].append(info)

    if timezone.now() > timestamp_end:
        if not StatsInfo.objects.filter(fitness=fitness, month=timestamp_end.month, year=timestamp_end.year).exists():
            StatsInfo.objects.create(month=timestamp_end.month,
                                     year=timestamp_end.year,
                                     stats=stats,
                                     money=stats['money'],
                                     fitness=fitness)
    return {'stats': stats}

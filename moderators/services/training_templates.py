from main.models import ImagePreload


def create_training_template(template, body):
    template.name = body['name']
    template.description = body.get('description', '')
    template.sport_type_id = body['sport_type']
    template.sport_types = [body['sport_type']]
    template.coach = body.get('coach', '')
    template.unlimited = body.get('unlimited', False)
    if body.get('required_items'):
        template.required_items = body.get('required_items')
    if body.get('max_users'):
        template.max_users = int(body['max_users'])
    if body.get('image_id'):
        template.image = ImagePreload.objects.get(id=int(body['image_id'])).image
    template.is_premium = body.get('is_premium', False)
    template.save()
    return template


def update_training_template(template, body):
    from main.tasks import update_template as update_template_task
    template.name = body.get('name', template.name)
    template.description = body.get('description', template.description)
    if body.get('sport_type'):
        template.sport_type_id = body['sport_type']
        template.sport_types = [int(body['sport_type'])]
    template.coach = body.get('coach', template.coach)
    template.unlimited = body.get('unlimited', template.unlimited)
    template.required_items = body.get('required_items', template.required_items)
    template.max_users = int(body.get('max_users', template.max_users))
    if body.get('image_id'):
        template.image = ImagePreload.objects.get(id=int(body['image_id'])).image
    template.is_premium = body.get('is_premium', template.is_premium)
    template.save()
    update_template_task.delay(template.id)
    return template

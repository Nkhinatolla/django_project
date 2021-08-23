from main.models import FitnessImage


def change_studio_image_priorities(images: dict):
    for image in images:
        fitness_image = FitnessImage.objects.get(id=image['id'])
        if fitness_image.priority != image['priority']:
            fitness_image.priority = image['priority']
            fitness_image.save(update_fields=['priority'])

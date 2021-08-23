from django.urls import path
from rest_framework import routers

from moderators.api import views

router = routers.DefaultRouter()
router.register(r'^studios/(?P<studio_id>\d+)/images', views.StudioImageViewSet, basename='studio_images')
router.register(r'^studios/(?P<studio_id>\d+)/trainings', views.TrainingViewSet, basename='trainings')
router.register(r'^studios/(?P<studio_id>\d+)/templates', views.TrainingTemplateViewSet, basename='training-templates'),

urlpatterns = [
    path(
        "studios",
        views.StudioViewSet.as_view({"get": "list"}),
        name="get_studios"
    ),
    path(
        "studios/<int:studio_id>",
        views.StudioViewSet.as_view({"get": "retrieve"}),
        name="get_studio-detail"
    ),
    path(
        "studios/<int:studio_id>/class_entries",
        views.ClassEntriesViewSet.as_view({"get": "list"}),
        name="class_entries-list"
    ),
    path(
        "studios/<int:studio_id>/reviews",
        views.StudioReviewsViewSet.as_view({"get": "list"}),
        name="get_studio_reviews-list"
    ),
    path(
        "studios/<int:studio_id>/statistics",
        views.StatisticsViewSet.as_view({"get": "statistics"}),
        name="get_studio_reviews-list"
    ),
    path(
        "studios/<int:studio_id>/partner_actions",
        views.PartnerActionsViewSet.as_view({"get": "list"}),
        name="get_partner_actions-list"
    ),

] + router.urls

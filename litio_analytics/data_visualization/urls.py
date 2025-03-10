# data_visualization/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('<int:analysis_id>/', views.generate_visualization, name='data_visualization'),
    path('<int:analysis_id>/export/<str:format>/', views.export_visualization, name='export_visualization'),
    path('<int:analysis_id>/update/', views.update_visualization, name='update_visualization'),
    path('<int:analysis_id>/delete/', views.delete_analysis, name='delete_analysis'),
]
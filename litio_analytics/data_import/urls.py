# data_import/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.DataFileListView.as_view(), name='data_file_list'),
    path('upload/', views.DataFileUploadView.as_view(), name='data_file_upload'),
    path('<int:pk>/', views.DataFileDetailView.as_view(), name='data_file_detail'),
    path('<int:pk>/preview/', views.preview_data, name='preview_data'),
    path('<int:pk>/process/', views.process_file, name='process_file'),
    path('<int:pk>/download/', views.download_processed_data, name='download_processed_data'),
]
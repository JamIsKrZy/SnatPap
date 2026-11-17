from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('profile/', views.profile_view, name='profile'),
    path('settings/', views.settings_view, name='settings'),
    
    # Document Hub & Upload page
    path('documents/', views.documents_view, name='documents'),
    path('documents/<int:doc_id>/detail/', views.document_detail_api, name='document_detail_api'),
    path('documents/<int:doc_id>/download/', views.document_download_file, name='document_download_file'),
    path('documents/<int:doc_id>/download-output/<str:format_type>/', views.document_download_output, name='document_download_output'),
    path('documents/<int:doc_id>/reprocess/', views.reprocess_document_view, name='document_reprocess'),
    path('documents/<int:doc_id>/delete/', views.delete_document_view, name='document_delete'),
    
    # Credit System
    path('credits/topup/', views.topup_credits_view, name='credit_topup'),
    
    # External Black-Box System APIs
    path('api/documents/pending/', views.api_pending_documents, name='api_pending_documents'),
    path('api/documents/<int:doc_id>/submit-result/', views.api_submit_result, name='api_submit_result'),
]

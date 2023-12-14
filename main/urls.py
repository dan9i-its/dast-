
from django.urls import path 
from . import views 
urlpatterns = [
    path('', views.index, name='home'),
    path('scans', views.scans, name='scans'),
    path('zap', views.zap, name='zap'),
    path('zap_results/<int:zap_results_id>/', views.zap_results, name='zap_results'),
    path('zap_full_results/<int:scan_full_results_id>/', views.zap_full_results, name='zap_full_results'),
    path('nuclei', views.nuclei, name='nuclei'),
    path('create', views.create, name='create'),
    path('crawl', views.crawl, name='crawl'),
    path('nuclei_resulsts/<int:nuclei_results_id>/', views.nuclei_results, name='nuclei_results'),
    path('crawl_scan/<int:crawl_results_id>/', views.crawl_results, name='crawl_results')
]

"""
The Vault - Core URL Configuration
"""

from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    
    # Couple pairing
    path('couple/', views.couple_setup, name='couple_setup'),
    path('couple/create/', views.create_vault, name='create_vault'),
    path('couple/join/', views.join_vault, name='join_vault'),
    path('couple/select/<int:couple_id>/', views.select_vault, name='select_vault'),
    
    # Home / Dashboard
    path('', views.home, name='home'),

    # Journal
    path('journal/', views.daily_journal, name='daily_journal'),
    path('submit/', views.submit_entry, name='submit_entry'),
    path('check-partner/', views.check_partner_status, name='check_partner_status'),
    
    # History
    path('history/', views.entry_history, name='entry_history'),
    path('history/<int:entry_id>/', views.entry_detail, name='entry_detail'),
    
    # Settings
    path('settings/', views.settings_view, name='settings'),
    
    # Wrapped
    path('wrapped/', views.wrapped_view, name='wrapped'),
    path('wrapped/<int:year>/', views.wrapped_view, name='wrapped_year'),
    
    # Spark - ideas for couples to explore together
    path('spark/', views.spark_index, name='spark_index'),
    path('spark/<str:category>/', views.spark_card, name='spark_card'),
    path('spark/<str:category>/next/', views.spark_next, name='spark_next'),
]

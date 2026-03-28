from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('auth/send-otp/', views.send_otp, name='send-otp'),
    path('auth/verify-otp/', views.verify_otp, name='verify-otp'),
    path('auth/register/', views.register_user, name='register'),
    path('auth/login/', views.login_user, name='login'),
    path('auth/verify-email/', views.verify_email_endpoint, name='verify-email'),
    path('auth/forgot-password/', views.forgot_password, name='forgot-password'),
    path('auth/verify-reset-otp/', views.verify_reset_otp, name='verify-reset-otp'),
    path('auth/reset-password-otp/', views.reset_password_with_otp, name='reset-password-otp'),
    path('auth/reset-password/', views.reset_password, name='reset-password'),
    
    # User Profile
    path('user/profile/', views.get_user_profile, name='user-profile'),
    path('user/profile/update/', views.update_user_profile, name='update-profile'),
    path('user/change-password/', views.change_password, name='change-password'),
    path('user/active-time/', views.update_active_time, name='update-active-time'),
    path('user/session/', views.get_session_data, name='get-session-data'),
    
    # News Articles
    path('news/', views.get_news_articles, name='news-list'),
    path('news/fetch-content/', views.fetch_full_article_content, name='fetch-full-content'),  # Must come before <article_id>
    path('news/proxy-image/', views.proxy_image, name='proxy-image'),
    path('news/refresh/', views.refresh_news, name='refresh-news'),
    path('news/<str:article_id>/', views.get_article_detail, name='article-detail'),
    path('categories/', views.get_categories, name='categories'),
    
    # Interactions
    path('interactions/', views.create_interaction, name='create-interaction'),
    path('interactions/remove/', views.remove_interaction, name='remove-interaction'),
    path('interactions/my/', views.get_user_interactions, name='user-interactions'),
    path('interactions/comments/', views.get_article_comments, name='article-comments'),
    path('interactions/ai-snapshot/', views.generate_ai_snapshot, name='ai-snapshot'),
    
    # Recommendations
    path('recommendations/', views.get_recommendations, name='recommendations'),
    path('knowledge-box/', views.get_knowledge_box, name='knowledge-box'),
    path('trending/', views.get_trending_articles, name='trending'),
    path('user/streak/', views.get_user_streak, name='user-streak'),
]

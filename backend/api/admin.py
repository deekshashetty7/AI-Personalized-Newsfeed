from django.contrib import admin
from .models import User, NewsArticle, NewsSource, UserPreference, Interaction, Recommendation

admin.site.register(User)
admin.site.register(NewsArticle)
admin.site.register(NewsSource)
admin.site.register(UserPreference)
admin.site.register(Interaction)
admin.site.register(Recommendation)

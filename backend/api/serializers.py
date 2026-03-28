from rest_framework import serializers
from .models import User, NewsArticle, NewsSource, UserPreference, Interaction, Recommendation
import json


class UserSerializer(serializers.ModelSerializer):
    interests = serializers.SerializerMethodField()
    _id = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', '_id', 'name', 'email', 'join_date', 'interests', 'profile_photo', 'streak_days', 'active_time']
        read_only_fields = ['id', 'join_date']
    
    def get__id(self, obj):
        """Return id as _id for frontend compatibility"""
        return str(obj.id)
    
    def get_interests(self, obj):
        """Ensure interests are returned as a proper array"""
        interests = obj.interests
        
        # If interests is already a list, return it
        if isinstance(interests, list):
            return interests
        
        # If it's a string, try to parse it
        if isinstance(interests, str):
            try:
                # Try to parse as JSON
                parsed = json.loads(interests.replace("'", '"'))
                return parsed if isinstance(parsed, list) else []
            except:
                # If parsing fails, return empty list
                return []
        
        # Default to empty list
        return []


class UserRegistrationSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)
    interests = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    
    def validate_password(self, value):
        """Validate password strength"""
        import re
        
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long")
        
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("Password must contain at least 1 uppercase letter")
        
        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError("Password must contain at least 1 lowercase letter")
        
        if not re.search(r'[0-9]', value):
            raise serializers.ValidationError("Password must contain at least 1 number")
        
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', value):
            raise serializers.ValidationError("Password must contain at least 1 special character (!@#$%^&*...)")
        
        return value
    
    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("Email already exists")
        
        return data
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User(
            name=validated_data['name'],
            email=validated_data['email'],
            interests=validated_data.get('interests', [])
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class NewsSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsSource
        fields = '__all__'


class NewsArticleSerializer(serializers.ModelSerializer):
    _id = serializers.SerializerMethodField()
    
    class Meta:
        model = NewsArticle
        fields = '__all__'
        read_only_fields = ['id', 'publish_time', 'sentiment_score', 'is_spam']
    
    def get__id(self, obj):
        """Return id as _id for frontend compatibility"""
        return str(obj.id)


class NewsArticleListSerializer(serializers.ModelSerializer):
    source = serializers.SerializerMethodField()
    _id = serializers.SerializerMethodField()
    
    class Meta:
        model = NewsArticle
        fields = ['id', '_id', 'title', 'summary', 'category', 'source', 'publish_time', 'sentiment_score', 'image_url', 'author', 'url']
    
    def get__id(self, obj):
        """Return id as _id for frontend compatibility"""
        return str(obj.id)
    
    def get_source(self, obj):
        """Return source field, fallback to source_id if source is empty"""
        if obj.source and obj.source.strip() and obj.source != 'Unknown':
            return obj.source
        if obj.source_id and obj.source_id.strip():
            return obj.source_id
        return 'Unknown'


class UserPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreference
        fields = '__all__'
        read_only_fields = ['id', 'last_interaction']


class InteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interaction
        fields = '__all__'
        read_only_fields = ['id', 'timestamp', 'sentiment']


class InteractionCreateSerializer(serializers.Serializer):
    article_id = serializers.CharField()
    action = serializers.ChoiceField(choices=['like', 'dislike', 'comment', 'share', 'save', 'read'])
    comment_text = serializers.CharField(required=False, allow_blank=True)
    dwell_time = serializers.IntegerField(required=False, default=0, help_text='Time spent on article in seconds')


class RecommendationSerializer(serializers.ModelSerializer):
    articles = serializers.SerializerMethodField()
    
    class Meta:
        model = Recommendation
        fields = ['id', 'user_id', 'article_ids', 'articles', 'created_at', 'model_version']
    
    def get_articles(self, obj):
        articles = NewsArticle.objects.filter(id__in=obj.article_ids)
        return NewsArticleListSerializer(articles, many=True).data

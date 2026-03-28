from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.auth.hashers import make_password, check_password
from datetime import datetime, timedelta
from django.utils import timezone
import random
import string


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user


class User(AbstractBaseUser):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    join_date = models.DateTimeField(auto_now_add=True)
    interests = models.JSONField(default=list)
    profile_photo = models.CharField(max_length=500, blank=True, null=True)
    streak_days = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    active_time = models.IntegerField(default=0)  # Total active time in seconds
    last_session_time = models.IntegerField(default=0)  # Current/last session time in seconds
    last_session_update = models.DateTimeField(null=True, blank=True)  # Last session update timestamp
    daily_activity = models.JSONField(default=dict)  # Daily activity breakdown: {"2026-01-11": 3600, "2026-01-10": 7200}
    reset_token = models.CharField(max_length=255, blank=True, null=True)
    reset_token_expires = models.DateTimeField(blank=True, null=True)
    reset_otp = models.CharField(max_length=6, blank=True, null=True)  # OTP for password reset
    reset_otp_expires = models.DateTimeField(blank=True, null=True)  # OTP expiration time
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']
    
    class Meta:
        db_table = 'users'
    
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_anonymous(self):
        return False
    
    def set_password(self, raw_password):
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    
    def __str__(self):
        return self.email


class NewsSource(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    api_url = models.CharField(max_length=500)
    type = models.CharField(max_length=50, choices=[
        ('API', 'API'),
        ('RSS', 'RSS'),
        ('SocialMedia', 'Social Media')
    ])
    credibility_score = models.FloatField(default=0.5)
    
    class Meta:
        db_table = 'news_sources'
    
    def __str__(self):
        return self.name


class NewsArticle(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=500)
    summary = models.TextField()
    content = models.TextField()
    category = models.CharField(max_length=100, db_index=True)  # Add index for faster category filtering
    source = models.CharField(max_length=200, blank=True, null=True, default='Unknown')  # Human-readable source name
    source_id = models.CharField(max_length=200, blank=True, null=True)
    publish_time = models.DateTimeField(default=datetime.now, db_index=True)  # Add index for sorting
    sentiment_score = models.FloatField(default=0.0)
    image_url = models.CharField(max_length=500, blank=True, null=True)
    is_spam = models.BooleanField(default=False)
    url = models.CharField(max_length=500, blank=True, null=True)
    author = models.CharField(max_length=200, blank=True, null=True)
    
    class Meta:
        db_table = 'news_articles'
        ordering = []  # Remove default ordering for faster queries
    
    def __str__(self):
        return self.title


class UserPreference(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    preference_score = models.FloatField(default=0.5)
    interaction_count = models.IntegerField(default=0)  # Track total interactions
    total_dwell_time = models.IntegerField(default=0)  # Total time spent in seconds
    last_interaction = models.DateTimeField(auto_now=True)  # For decay calculation
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_preferences'
        indexes = [
            models.Index(fields=['user_id', 'preference_score']),
        ]
    
    def __str__(self):
        return f"{self.user_id} - {self.category} ({self.preference_score:.2f})"


class Interaction(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.CharField(max_length=200)
    article_id = models.CharField(max_length=200)
    action = models.CharField(max_length=50, choices=[
        ('like', 'Like'),
        ('dislike', 'Dislike'),
        ('comment', 'Comment'),
        ('share', 'Share'),
        ('save', 'Save'),
        ('read', 'Read'),
        ('ai_snapshot', 'AI Snapshot')
    ])
    sentiment = models.FloatField(default=0.0)
    timestamp = models.DateTimeField(auto_now_add=True)
    comment_text = models.TextField(blank=True, null=True)
    dwell_time = models.IntegerField(default=0, help_text='Time spent on article in seconds')
    
    class Meta:
        db_table = 'interactions'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user_id} - {self.action}"


class Recommendation(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.CharField(max_length=200)
    article_ids = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    model_version = models.CharField(max_length=50, default='v1.0')
    
    class Meta:
        db_table = 'recommendations'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Recommendations for {self.user_id}"


class KnowledgeBox(models.Model):
    """
    Stores user's learned topics and knowledge accumulated from reading
    """
    id = models.AutoField(primary_key=True)
    user_id = models.CharField(max_length=200, db_index=True)
    topic = models.CharField(max_length=200)
    article_count = models.IntegerField(default=0)
    total_time_spent = models.IntegerField(default=0)  # seconds
    importance_score = models.FloatField(default=0.0)  # 0-1 score
    subtopics = models.JSONField(default=list)  # List of related subtopics
    key_entities = models.JSONField(default=list)  # People, places, organizations
    article_ids = models.JSONField(default=list)  # Related article IDs
    first_read = models.DateTimeField(auto_now_add=True)
    last_read = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'knowledge_box'
        ordering = ['-importance_score', '-last_read']
        indexes = [
            models.Index(fields=['user_id', '-importance_score']),
        ]
    
    def __str__(self):
        return f"{self.user_id} - {self.topic} ({self.article_count} articles)"


class EmailOTP(models.Model):
    id = models.AutoField(primary_key=True)
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'email_otps'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.email} - {self.otp} - {'Verified' if self.is_verified else 'Pending'}"
    
    @staticmethod
    def generate_otp():
        """Generate a 6-digit OTP"""
        return ''.join(random.choices(string.digits, k=6))
    
    def is_expired(self):
        """Check if OTP has expired"""
        return timezone.now() > self.expires_at
    
    @classmethod
    def create_otp(cls, email):
        """Create a new OTP for the given email"""
        # Simply create new OTP - djongo doesn't handle complex filters well
        otp = cls.generate_otp()
        expires_at = timezone.now() + timedelta(minutes=10)  # OTP valid for 10 minutes
        
        return cls.objects.create(
            email=email,
            otp=otp,
            expires_at=expires_at
        )

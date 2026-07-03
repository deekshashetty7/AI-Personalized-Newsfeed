from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q
from django.core.cache import cache
from django.utils import timezone
from datetime import datetime, timedelta
import requests
from collections import defaultdict
import re
from urllib.parse import urlparse

from .models import User, NewsArticle, NewsSource, UserPreference, Interaction, Recommendation
from .serializers import (
    UserSerializer, UserRegistrationSerializer, UserLoginSerializer,
    NewsArticleSerializer, NewsArticleListSerializer, NewsSourceSerializer,
    UserPreferenceSerializer, InteractionSerializer, InteractionCreateSerializer,
    RecommendationSerializer
)
from .services import news_fetcher
from .ai_modules.sentiment_analysis import analyze_sentiment, analyze_article_sentiment
from .ai_modules.spam_detection import detect_article_spam
from .ai_modules.recommendation import generate_recommendations
from .ai_modules.semantic_search import build_semantic_query, rank_results, extract_intent
from .ai_modules.personalization import generate_personalized_feed
from .ai_modules.knowledge_extraction import update_knowledge_box


def clean_article_for_client(article):
    """
    Clean article data before sending to client.
    Removes AI labels, metadata, and ensures professional output.
    Also validates and fixes missing images.
    """
    import hashlib
    import html
    
    # Ensure image exists and is valid
    image_url = article.get('image_url', '')
    
    # Decode HTML entities in URL if present
    if image_url and '&amp;' in image_url:
        image_url = html.unescape(image_url)
        article['image_url'] = image_url
    
    # Check if image is valid and accessible
    # Reddit external preview images and Unsplash source links often don't load reliably
    should_generate_fallback = (
        not image_url or 
        image_url.strip() == '' or 
        'source.unsplash.com' in image_url or
        'external-preview.redd.it' in image_url or
        'redd.it' in image_url or
        '&amp;' in image_url
    )
    
    if should_generate_fallback:
        # Generate fallback image
        title = article.get('title', '')
        category = article.get('category', 'General')
        seed_text = f"{category}-{title[:30]}"
        seed = hashlib.md5(seed_text.encode()).hexdigest()[:8]
        article['image_url'] = f"https://picsum.photos/seed/{seed}/1024/1024"
    
    # Fields to clean from AI labels
    text_fields = ['content', 'summary', 'description', 'title']
    
    for field in text_fields:
        if field in article and article[field]:
            content = str(article[field])
            
            # Remove AI-related labels and markers
            ai_labels = [
                r'\*\*AI Generated\*\*',
                r'\*\*Quick Read\*\*',
                r'\*\*Summary\*\*',
                r'AI-generated',
                r'AI Generated',
                r'Quick Read',
                r'\[AI\]',
                r'\(AI\)',
                r'This article was generated',
                r'This content was generated',
                r'Auto-generated',
                r'Automatically generated',
                r'\*\*Note:?\*\*',
                r'Important Note:',
            ]
            
            for pattern in ai_labels:
                content = re.sub(pattern, '', content, flags=re.IGNORECASE)
            
            # Clean up excessive whitespace
            content = re.sub(r'\n{3,}', '\n\n', content)
            content = re.sub(r' {2,}', ' ', content)
            content = content.strip()
            
            article[field] = content
    
    # Remove metadata fields that shouldn't be exposed
    metadata_fields = [
        'ai_generated',
        'generated_by_ai',
        'content_generated',
        'image_generated',
        'processing_notes',
        'ai_metadata'
    ]
    
    for field in metadata_fields:
        article.pop(field, None)
    
    return article


def derive_display_source(source, source_id, url):
    """Return a user-friendly source name with fallback to URL domain."""
    invalid_values = {
        '', 'unknown', 'unknown source', 'none', 'null', 'n/a', 'na', 'undefined'
    }

    # 1) Prefer explicit source/source_id when valid
    for candidate in [source, source_id]:
        if not candidate:
            continue
        value = str(candidate).strip()
        if value.lower() not in invalid_values:
            return value

    # 2) Fallback to domain extracted from URL
    if not url:
        return 'Unknown'

    try:
        hostname = (urlparse(url).hostname or '').lower().strip()
        if not hostname:
            return 'Unknown'

        hostname = hostname.replace('www.', '')

        # Common friendly aliases
        aliases = {
            'bbc.co.uk': 'BBC News',
            'bbc.com': 'BBC News',
            'cnn.com': 'CNN',
            'reuters.com': 'Reuters',
            'theguardian.com': 'The Guardian',
            'nytimes.com': 'The New York Times',
            'wsj.com': 'The Wall Street Journal',
            'cnbc.com': 'CNBC',
            'npr.org': 'NPR',
            'foxnews.com': 'Fox News',
            'cbsnews.com': 'CBS News',
            'nbcnews.com': 'NBC News',
            'abcnews.go.com': 'ABC News',
            'politico.com': 'Politico',
            'ctvnews.ca': 'CTV News',
        }

        if hostname in aliases:
            return aliases[hostname]

        parts = hostname.split('.')
        if len(parts) >= 3 and parts[-2] in {'co', 'com', 'org', 'net'}:
            site = parts[-3]
        elif len(parts) >= 2:
            site = parts[-2]
        else:
            site = parts[0]

        return site.replace('-', ' ').title() if site else 'Unknown'
    except Exception:
        return 'Unknown'


def ensure_full_content(articles):
    """
    Ensure all articles have full AI-generated content (2000-2500 words).
    Generates content using OpenAI for articles with insufficient content.
    Updates the database with generated content.
    """
    from .utils.content_generator import generate_article_content
    from .models import NewsArticle
    
    enhanced_articles = []
    
    for article in articles:
        try:
            # Check content length
            content = article.get('content', '') or ''
            content_length = len(content)
            
            # If content is too short (less than 1500 chars), generate full article
            if content_length < 1500:
                article_id = article.get('id', '')
                headline = article.get('title', '')
                source = article.get('source', '') or article.get('source_id', '')
                category = article.get('category', 'General')
                summary = article.get('description', '') or article.get('summary', '')
                
                print(f"[GENERATE] Creating full article for: {headline[:50]}...")
                
                # Generate full content using OpenAI
                try:
                    full_content = generate_article_content(
                        headline=headline,
                        source=source,
                        category=category,
                        summary=summary
                    )
                    
                    if full_content and len(full_content) > 1000:
                        article['content'] = full_content
                        
                        # Update database with generated content
                        if article_id:
                            try:
                                NewsArticle.objects.filter(id=article_id).update(
                                    content=full_content
                                )
                                print(f"[SAVED] Updated article in database with {len(full_content)} chars")
                            except Exception as db_error:
                                print(f"[WARN] Could not update database: {db_error}")
                        
                        print(f"[OK] Generated {len(full_content)} chars (~{len(full_content.split())} words)")
                    else:
                        print(f"[WARN] Generated content too short, keeping existing")
                        
                except Exception as gen_error:
                    print(f"[ERROR] Content generation failed: {gen_error}")
                    # Keep existing content if generation fails
            
            enhanced_articles.append(article)
            
        except Exception as e:
            print(f"[ERROR] Error processing article: {e}")
            enhanced_articles.append(article)
    
    return enhanced_articles


def verify_email(email):
    """Verify email using comprehensive checks: regex, DNS, and SMTP"""
    try:
        import dns.resolver
        import smtplib
        from django.conf import settings
        
        # Step 1: Basic format validation (Regex check)
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            print(f"[ERROR] Email format invalid: {email}")
            return {
                'is_valid': False,
                'message': 'Invalid email format',
                'details': {'step': 'regex', 'passed': False}
            }
        
        print(f"[OK] Regex check passed for: {email}")
        
        # Extract domain from email
        domain = email.split('@')[1]
        
        # Step 2: Domain MX Record Check
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_hosts = [str(r.exchange) for r in mx_records]
            print(f"[OK] MX records found for {domain}: {mx_hosts}")
            
            if not mx_hosts:
                print(f"[ERROR] No MX records for domain: {domain}")
                return {
                    'is_valid': False,
                    'message': f'Domain {domain} has no mail servers',
                    'details': {'step': 'mx_record', 'passed': False}
                }
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer) as e:
            print(f"[ERROR] Domain does not exist or has no MX records: {domain}")
            return {
                'is_valid': False,
                'message': f'Domain {domain} does not exist or cannot receive emails',
                'details': {'step': 'mx_record', 'passed': False, 'error': str(e)}
            }
        except Exception as e:
            print(f"[WARN] MX lookup error for {domain}: {str(e)}")
            # Continue to SMTP check even if MX lookup fails
        
        # Step 3: SMTP Mailbox Verification
        try:
            # Get primary MX host
            primary_mx = str(mx_records[0].exchange).rstrip('.')
            print(f"[SEARCH] Attempting SMTP verification with: {primary_mx}")
            
            # Connect to mail server
            server = smtplib.SMTP(timeout=10)
            server.set_debuglevel(0)
            server.connect(primary_mx)
            server.helo(server.local_hostname)
            server.mail('verify@infocred.com')
            code, message = server.rcpt(email)
            server.quit()
            
            # Check SMTP response code
            if code == 250:
                print(f"[OK] SMTP verification passed for: {email}")
                return {
                    'is_valid': True,
                    'message': 'Email verified successfully (all checks passed)',
                    'details': {
                        'regex': True,
                        'mx_record': True,
                        'smtp': True,
                        'smtp_code': code
                    }
                }
            elif code == 550:
                # 550 = Mailbox does not exist (definitive rejection)
                print(f"[ERROR] SMTP verification failed - mailbox does not exist: {email}")
                return {
                    'is_valid': False,
                    'message': 'Email address does not exist',
                    'details': {
                        'regex': True,
                        'mx_record': True,
                        'smtp': False,
                        'smtp_code': code,
                        'smtp_message': message.decode() if isinstance(message, bytes) else str(message)
                    }
                }
            else:
                print(f"[WARN] SMTP returned code {code} for {email}: {message}")
                # For other codes, accept if MX exists (might be temporary issue)
                return {
                    'is_valid': True,
                    'message': 'Email format and domain valid (SMTP check inconclusive)',
                    'details': {
                        'regex': True,
                        'mx_record': True,
                        'smtp': False,
                        'smtp_code': code,
                        'smtp_message': message.decode() if isinstance(message, bytes) else str(message)
                    }
                }
                
        except smtplib.SMTPServerDisconnected:
            print(f"[WARN] SMTP server disconnected for {domain}")
            # Accept if MX records exist
            return {
                'is_valid': True,
                'message': 'Email format and domain valid (SMTP server unavailable)',
                'details': {'regex': True, 'mx_record': True, 'smtp': 'unavailable'}
            }
        except smtplib.SMTPConnectError:
            print(f"[WARN] Cannot connect to SMTP server for {domain}")
            return {
                'is_valid': True,
                'message': 'Email format and domain valid (SMTP connection failed)',
                'details': {'regex': True, 'mx_record': True, 'smtp': 'connection_failed'}
            }
        except Exception as e:
            print(f"[WARN] SMTP verification error for {email}: {str(e)}")
            # Accept if domain checks passed
            return {
                'is_valid': True,
                'message': 'Email format and domain valid (SMTP check failed)',
                'details': {'regex': True, 'mx_record': True, 'smtp': 'error', 'error': str(e)}
            }

    except Exception as e:
        print(f"[WARN] Email validation error: {str(e)}, falling back to format validation")
        # Fallback to format-only validation
        return {
            'is_valid': True,  # Email format is valid, API error
            'message': 'Email format valid (API service error)',
            'details': {'error': str(e), 'fallback': True}
        }


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email_endpoint(request):
    """Endpoint to verify email before registration"""
    try:
        email = request.data.get('email')
        
        print(f"?? Email verification request received for: {email}")
        
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            print(f"[WARN] Email already registered: {email}")
            return Response({
                'is_valid': False,
                'message': 'Email already registered'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify email
        result = verify_email(email)
        print(f"[OK] Verification result: {result}")
        
        if result['is_valid']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        print(f"[ERROR] Error in verify_email_endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'error': 'Email verification failed',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def send_otp(request):
    """Send OTP to user's email for verification"""
    try:
        from .models import EmailOTP
        from .email_service import send_otp_email
        import re
        
        email = request.data.get('email')
        
        if not email:
            return Response({
                'error': 'Email is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Basic email format validation
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            return Response({
                'error': 'Invalid email format'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            return Response({
                'error': 'Email already registered'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create OTP
        otp_record = EmailOTP.create_otp(email)
        
        # Send OTP via email
        email_result = send_otp_email(email, otp_record.otp)
        
        print(f"[OK] OTP generated for {email}: {otp_record.otp}")
        
        return Response({
            'message': email_result['message'],
            'email': email,
            'expires_in': '10 minutes',
            'mode': email_result.get('mode', 'production')
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"[ERROR] Send OTP error: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'error': f'Failed to send OTP: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    """Verify OTP entered by user"""
    try:
        from .models import EmailOTP
        
        email = request.data.get('email')
        otp_code = request.data.get('otp')
        
        print(f"[SEARCH] Verify OTP request - Email: {email}, OTP: {otp_code}")
        
        if not email or not otp_code:
            return Response({
                'error': 'Email and OTP are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Find the latest OTP for this email
        try:
            # Get all OTPs for email, filter in Python (djongo doesn't support complex filters)
            all_otps = list(EmailOTP.objects.filter(email=email).order_by('-created_at'))
            print(f"?? Found {len(all_otps)} total OTP records for {email}")
            
            # Debug: Print all OTPs
            for idx, otp in enumerate(all_otps):
                print(f"  OTP #{idx+1}: code={otp.otp}, verified={otp.is_verified}, expired={otp.is_expired()}, attempts={otp.attempts}")
            
            otp_record = next((otp for otp in all_otps if not otp.is_verified), None)
            
            if not otp_record:
                return Response({
                    'error': 'No OTP found for this email. Please request a new one.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if OTP has expired
            if otp_record.is_expired():
                return Response({
                    'error': 'OTP has expired. Please request a new one.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check attempts
            if otp_record.attempts >= 5:
                return Response({
                    'error': 'Too many failed attempts. Please request a new OTP.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Verify OTP
            if otp_record.otp == otp_code:
                otp_record.is_verified = True
                otp_record.save()
                
                print(f"[OK] OTP verified successfully for {email}")
                
                return Response({
                    'message': 'OTP verified successfully',
                    'email': email,
                    'verified': True
                }, status=status.HTTP_200_OK)
            else:
                # Increment attempts
                otp_record.attempts += 1
                otp_record.save()
                
                remaining = 5 - otp_record.attempts
                print(f"[ERROR] Invalid OTP for {email}. Expected: '{otp_record.otp}', Got: '{otp_code}'. Attempts: {otp_record.attempts}/5")
                
                return Response({
                    'error': f'Invalid OTP. {remaining} attempts remaining.',
                    'attempts_remaining': remaining
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            print(f"[ERROR] OTP verification error: {str(e)}")
            return Response({
                'error': 'Failed to verify OTP'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        print(f"[ERROR] Verify OTP error: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'error': f'Failed to verify OTP: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """Register a new user with email verification"""
    try:
        from .models import EmailOTP
        from .email_service import send_welcome_email
        
        print(f"?? Registration attempt with data: {request.data}")
        
        email = request.data.get('email')
        
        # Check if OTP was verified
        if email:
            # Get all OTPs, filter in Python (djongo compatibility)
            all_otps = list(EmailOTP.objects.filter(email=email).order_by('-created_at'))
            otp_verified = next((otp for otp in all_otps if otp.is_verified), None)
            
            if not otp_verified:
                return Response({
                    'error': 'Email not verified. Please verify your email with OTP first.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if OTP was verified recently (within last 30 minutes)
            if (timezone.now() - otp_verified.created_at).seconds > 1800:
                return Response({
                    'error': 'OTP verification expired. Please request a new OTP.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            print(f"[OK] OTP verified for email: {email}")
        
        serializer = UserRegistrationSerializer(data=request.data)
        
        if not serializer.is_valid():
            print(f"[ERROR] Validation errors: {serializer.errors}")
            # Format validation errors more clearly
            error_messages = []
            for field, errors in serializer.errors.items():
                if isinstance(errors, list):
                    error_messages.extend([f"{field}: {err}" for err in errors])
                else:
                    error_messages.append(f"{field}: {errors}")
            error_msg = "; ".join(error_messages)
            return Response({'error': error_msg}, status=status.HTTP_400_BAD_REQUEST)
        
        # Save user
        user = serializer.save()
        print(f"[OK] User created successfully: {user.email}")
        
        # Send welcome email
        send_welcome_email(user.email, user.name)
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'User registered successfully',
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        print(f"[ERROR] Registration error: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({'error': f'Registration failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    """Login user and return JWT tokens"""
    try:
        print(f"?? Login attempt for email: {request.data.get('email')}")
        serializer = UserLoginSerializer(data=request.data)
        
        if not serializer.is_valid():
            print(f"[ERROR] Login validation errors: {serializer.errors}")
            return Response({'error': 'Invalid input data'}, status=status.HTTP_400_BAD_REQUEST)
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        try:
            user = User.objects.get(email=email)
            
            if user.check_password(password):
                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                
                print(f"[OK] Login successful for: {email}")
                return Response({
                    'message': 'Login successful',
                    'user': UserSerializer(user).data,
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    }
                })
            else:
                print(f"[ERROR] Invalid password for: {email}")
                return Response({
                    'error': 'Invalid email or password'
                }, status=status.HTTP_401_UNAUTHORIZED)
        
        except User.DoesNotExist:
            print(f"[ERROR] User not found: {email}")
            return Response({
                'error': 'Invalid email or password'
            }, status=status.HTTP_401_UNAUTHORIZED)
    
    except Exception as e:
        print(f"[ERROR] Login error: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({'error': f'Login failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    """Get current user profile"""
    user_id = request.user.id
    try:
        user = User.objects.get(id=user_id)
        return Response(UserSerializer(user).data)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_user_profile(request):
    """Update user profile"""
    user_id = request.user.id
    try:
        user = User.objects.get(id=user_id)
        
        # Update allowed fields
        if 'name' in request.data:
            user.name = request.data['name']
        if 'interests' in request.data:
            user.interests = request.data['interests']
        if 'profile_photo' in request.data:
            user.profile_photo = request.data['profile_photo']
        
        user.save()
        return Response(UserSerializer(user).data)
    
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """Change user password"""
    user_id = request.user.id
    try:
        user = User.objects.get(id=user_id)
        
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        
        if not old_password or not new_password:
            return Response({'error': 'Both old and new passwords are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify old password
        if not user.check_password(old_password):
            return Response({'error': 'Current password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate new password
        if len(new_password) < 6:
            return Response({'error': 'New password must be at least 6 characters'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)
    
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_active_time(request):
    """Update user's active time on the website"""
    user_id = request.user.id
    try:
        user = User.objects.get(id=user_id)
        
        # Get the time increment in seconds
        time_seconds = request.data.get('time_seconds', 0)
        
        # Update active time
        user.active_time = user.active_time + int(time_seconds)
        user.save()
        
        return Response({
            'message': 'Active time updated successfully',
            'total_active_time': user.active_time
        }, status=status.HTTP_200_OK)
    
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    """Send OTP to email for password reset"""
    try:
        email = request.data.get('email')
        
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # For security, don't reveal if email exists
            return Response({
                'message': 'If an account with that email exists, an OTP has been sent.'
            }, status=status.HTTP_200_OK)
        
        # Generate 6-digit OTP
        import random
        otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
        user.reset_otp = otp
        user.reset_otp_expires = timezone.now() + timedelta(minutes=10)  # OTP expires in 10 minutes
        user.save()
        
        # Send OTP email
        from .email_service import send_password_reset_otp
        email_result = send_password_reset_otp(email, otp)
        
        print(f"[OK] Password reset OTP sent to {email}: {otp}")
        
        return Response({
            'message': 'If an account with that email exists, an OTP has been sent.',
            'otp': otp  # Include for testing - remove in production
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"[ERROR] Error in forgot_password: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({'error': 'Failed to process password reset request'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_reset_otp(request):
    """Verify OTP for password reset"""
    try:
        email = request.data.get('email')
        otp = request.data.get('otp')
        
        if not email or not otp:
            return Response({'error': 'Email and OTP are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Find user with this email and OTP
        try:
            user = User.objects.get(email=email, reset_otp=otp)
        except User.DoesNotExist:
            return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if OTP is expired
        if user.reset_otp_expires and timezone.now() > user.reset_otp_expires:
            return Response({'error': 'OTP has expired. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)
        
        print(f"[OK] OTP verified successfully for user: {user.email}")
        
        return Response({
            'message': 'OTP verified successfully',
            'verified': True
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"[ERROR] Error in verify_reset_otp: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({'error': 'Failed to verify OTP'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password_with_otp(request):
    """Reset password using verified OTP"""
    try:
        email = request.data.get('email')
        otp = request.data.get('otp')
        new_password = request.data.get('new_password')
        
        if not email or not otp or not new_password:
            return Response({'error': 'Email, OTP, and new password are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if len(new_password) < 6:
            return Response({'error': 'Password must be at least 6 characters'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Find user with this email and OTP
        try:
            user = User.objects.get(email=email, reset_otp=otp)
        except User.DoesNotExist:
            return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if OTP is expired
        if user.reset_otp_expires and timezone.now() > user.reset_otp_expires:
            return Response({'error': 'OTP has expired. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Reset password
        user.set_password(new_password)
        user.reset_otp = None
        user.reset_otp_expires = None
        user.save()
        
        print(f"[OK] Password reset successful for user: {user.email}")
        
        return Response({
            'message': 'Password has been reset successfully'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"[ERROR] Error in reset_password_with_otp: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({'error': 'Failed to reset password'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    """Reset password using token"""
    try:
        token = request.data.get('token')
        new_password = request.data.get('new_password')
        
        if not token or not new_password:
            return Response({'error': 'Token and new password are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if len(new_password) < 6:
            return Response({'error': 'Password must be at least 6 characters'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Find user with this token
        try:
            user = User.objects.get(reset_token=token)
        except User.DoesNotExist:
            return Response({'error': 'Invalid or expired reset token'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if token is expired
        from datetime import datetime
        if user.reset_token_expires and timezone.now() > user.reset_token_expires:
            return Response({'error': 'Reset token has expired'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Reset password
        user.set_password(new_password)
        user.reset_token = None
        user.reset_token_expires = None
        user.save()
        
        print(f"[OK] Password reset successful for user: {user.email}")
        
        return Response({
            'message': 'Password has been reset successfully'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"[ERROR] Error in reset_password: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({'error': 'Failed to reset password'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_active_time(request):
    """Update user's active time and session tracking"""
    try:
        user = request.user
        time_increment = request.data.get('time_seconds', 0)
        is_session_end = request.data.get('is_session_end', False)
        
        if time_increment > 0:
            now = timezone.now()
            today = now.strftime('%Y-%m-%d')
            
            # Get current daily_activity
            daily_activity = user.daily_activity if hasattr(user, 'daily_activity') and user.daily_activity else {}
            
            # Update today's activity
            if today in daily_activity:
                daily_activity[today] = daily_activity[today] + time_increment
            else:
                daily_activity[today] = time_increment
            
            # Update based on session state
            if is_session_end:
                # Session ending - add to active_time and reset session
                user.active_time = (user.active_time or 0) + time_increment
                user.last_session_time = 0
                user.last_session_update = now
                user.daily_activity = daily_activity
            else:
                # Ongoing session - increment both active_time and session_time
                user.active_time = (user.active_time or 0) + time_increment
                user.last_session_time = (user.last_session_time or 0) + time_increment
                user.last_session_update = now
                user.daily_activity = daily_activity
            
            user.save()
            
            return Response({
                'message': 'Active time updated successfully',
                'total_active_time': user.active_time,
                'current_session_time': user.last_session_time,
                'last_updated': user.last_session_update
            }, status=status.HTTP_200_OK)
        
        return Response({
            'message': 'No time increment provided',
            'total_active_time': user.active_time or 0,
            'current_session_time': user.last_session_time or 0,
            'last_updated': user.last_session_update
        }, status=status.HTTP_200_OK)
    
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"[ERROR] Error in update_active_time: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_session_data(request):
    """Get user's session data including last session time and daily activity breakdown"""
    try:
        from datetime import datetime, timedelta
        user = request.user
        
        # Get daily activity for last 7 days
        daily_activity = user.daily_activity if hasattr(user, 'daily_activity') else {}
        
        # Generate last 7 days data
        today = datetime.now()
        today_str = today.strftime('%Y-%m-%d')
        
        last_7_days = {}
        
        for i in range(7):
            date = (today - timedelta(days=6-i)).strftime('%Y-%m-%d')
            last_7_days[date] = daily_activity.get(date, 0)
        
        print(f"[SESSION DATA] Returning activity: {last_7_days}")
        
        return Response({
            'last_session_time': user.last_session_time or 0,
            'last_session_update': user.last_session_update,
            'total_active_time': user.active_time or 0,
            'daily_activity': last_7_days
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_news_articles(request):
    """Get news articles with optional filtering - always returns data"""
    category = request.query_params.get('category')
    search = request.query_params.get('search')
    page_size = int(request.query_params.get('page_size', 100))
    unlimited = request.query_params.get('unlimited', 'false').lower() == 'true'
    
    # Clean up category parameter - remove quotes and brackets if present
    if category:
        category = category.strip().strip("[]'\"")
    
    print(f"[NEWS] News API called - Category: {category}, Search: {search}, Page Size: {page_size}, Unlimited: {unlimited}")
    
    try:
        # Use Django ORM directly (faster fallback than MongoDB)
        from api.models import NewsArticle
        from django.db.models import Q
        
        print(f"[DB] Querying Django ORM for articles...")
        
        # Build query
        query = Q()
        
        # Apply category filter
        if category and category.lower() not in ['all', '']:
            query &= Q(category__iexact=category)
            print(f"[DB] Filtering by category: {category}")
        
        # Apply search filter
        if search:
            search_query = Q(title__icontains=search) | Q(description__icontains=search) | Q(content__icontains=search)
            query &= search_query
            print(f"[DB] Filtering by search: {search}")
        
        # Fetch articles - ALWAYS sorted by publish_time descending (most recent first)
        if unlimited:
            max_articles = min(page_size * 10, 2000)  # Cap at 2000
            articles_qs = NewsArticle.objects.filter(query).order_by('-publish_time').select_related()[:max_articles]
            print(f"[DB] Unlimited mode: fetching up to {max_articles} articles")
        else:
            articles_qs = NewsArticle.objects.filter(query).order_by('-publish_time').select_related()[:page_size]
        
        # Force sorting to ensure consistent ordering
        articles_list = list(articles_qs)
        articles_list.sort(key=lambda x: x.publish_time, reverse=True)  # Latest first
        
        # Convert to dictionaries
        articles_data = []
        for article in articles_list:
            display_source = derive_display_source(article.source, article.source_id, article.url)
            article_data = {
                '_id': str(article.id),
                'title': article.title,
                'description': article.summary or '',
                'summary': article.summary or '',
                'content': article.content or '',
                'category': article.category or 'General',
                'publish_time': article.publish_time.isoformat() if article.publish_time else '',
                'sentiment_score': article.sentiment_score or 0.0,
                'image_url': article.image_url or '',
                'source': display_source,
                'source_id': article.source_id or 'unknown',
                'author': article.author or 'Unknown',
                'url': article.url or '',
                'is_liked': False,
                'is_disliked': False,
                'is_saved': False,
            }

            # Ensure client-safe content and reliable image URLs
            article_data = clean_article_for_client(article_data)
            articles_data.append(article_data)
        
        # Final verification - ensure response is sorted by publish_time descending
        articles_data.sort(key=lambda x: x.get('publish_time', ''), reverse=True)
        
        print(f"[OK] Returning {len(articles_data)} articles from Django ORM (sorted by latest first)")
        return Response(articles_data)
        
    except Exception as e:
        print(f"[ERROR] Error fetching articles: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback: Try NewsAPI
        try:
            from api.services import news_fetcher
            print("[FALLBACK] Falling back to NewsAPI...")
            api_articles = news_fetcher.fetch_top_headlines(page_size=page_size)
            normalized_articles = [news_fetcher.normalize_article(article) for article in api_articles]
            print(f"[OK] Returning {len(normalized_articles)} articles from NewsAPI fallback")
            return Response(normalized_articles)
        except Exception as fallback_err:
            print(f"[WARN] NewsAPI fallback failed: {fallback_err}")
            
            # Last resort fallback
            try:
                articles = news_fetcher._get_fallback_news(category)
                normalized_articles = [news_fetcher.normalize_article(article) for article in articles]
                print(f"[OK] Returning {len(normalized_articles)} articles from hardcoded fallback")
                return Response(normalized_articles)
            except:
                print(f"[ERROR] All fallbacks failed, returning empty array")
                return Response([])


@api_view(['GET'])
@permission_classes([AllowAny])
def get_article_detail(request, article_id):
    """Get single article details"""
    try:
        # Try to convert to int for Django ORM lookup
        try:
            article_id_int = int(article_id)
            article = NewsArticle.objects.get(id=article_id_int)
            return Response(NewsArticleSerializer(article).data)
        except (ValueError, TypeError):
            # It's a MongoDB ObjectId string, query MongoDB directly
            from pymongo import MongoClient
            from bson import ObjectId
            client = MongoClient('mongodb://localhost:27017/')
            db = client['ai_newsfeed']
            
            try:
                # Try to find by MongoDB _id
                article = db.news_articles.find_one({'_id': ObjectId(article_id)})
                if article:
                    # Convert ObjectId to string
                    article['_id'] = str(article['_id'])
                    # Map fields for frontend
                    if 'description' in article:
                        article['summary'] = article.pop('description')
                    return Response(article)
            except:
                pass
            
            # Not found
            return Response({'error': 'Article not found'}, status=status.HTTP_404_NOT_FOUND)
            
    except NewsArticle.DoesNotExist:
        return Response({'error': 'Article not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_interaction(request):
    """Create or toggle user interaction with article (authenticated users only)"""
    serializer = InteractionCreateSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    user_id = str(request.user.id)
    article_id = serializer.validated_data['article_id']
    action = serializer.validated_data['action']
    comment_text = serializer.validated_data.get('comment_text', '')
    dwell_time = serializer.validated_data.get('dwell_time', 0)
    
    # MUTUAL EXCLUSIVITY: Like and Dislike cannot coexist
    if action == 'like':
        # Check if like already exists (toggle off)
        existing_like = Interaction.objects.filter(
            user_id=user_id,
            article_id=article_id,
            action='like'
        ).order_by('-timestamp').first()
        
        if existing_like:
            # Toggle off: Remove like
            existing_like.delete()
            return Response({'message': 'like removed', 'toggled': False}, status=status.HTTP_200_OK)
        
        # Remove any existing dislike (mutual exclusivity)
        Interaction.objects.filter(
            user_id=user_id,
            article_id=article_id,
            action='dislike'
        ).delete()
    
    elif action == 'dislike':
        # Check if dislike already exists (toggle off)
        existing_dislike = Interaction.objects.filter(
            user_id=user_id,
            article_id=article_id,
            action='dislike'
        ).order_by('-timestamp').first()
        
        if existing_dislike:
            # Toggle off: Remove dislike
            existing_dislike.delete()
            return Response({'message': 'dislike removed', 'toggled': False}, status=status.HTTP_200_OK)
        
        # Remove any existing like (mutual exclusivity)
        Interaction.objects.filter(
            user_id=user_id,
            article_id=article_id,
            action='like'
        ).delete()
    
    elif action == 'save':
        # Check if save already exists (toggle)
        existing_save = Interaction.objects.filter(
            user_id=user_id,
            article_id=article_id,
            action='save'
        ).order_by('-timestamp').first()
        
        if existing_save:
            # Toggle off: Remove save
            existing_save.delete()
            return Response({'message': 'save removed', 'toggled': False}, status=status.HTTP_200_OK)
    
    # Analyze sentiment if there's a comment
    sentiment_score = 0.0
    if comment_text:
        sentiment_score = analyze_sentiment(comment_text)
    
    # Create interaction
    interaction = Interaction.objects.create(
        user_id=user_id,
        article_id=article_id,
        action=action,
        comment_text=comment_text,
        sentiment=sentiment_score,
        dwell_time=dwell_time
    )
    
    # Update user preferences based on interaction (AI Learning)
    try:
        # Try to get article - handle both Django ORM and MongoDB
        article = None
        category = 'General'  # Default category
        
        try:
            article_id_int = int(article_id)
            article = NewsArticle.objects.get(id=article_id_int)
            category = article.category
        except (ValueError, TypeError, NewsArticle.DoesNotExist):
            # It's a MongoDB ObjectId, query MongoDB for category
            try:
                from pymongo import MongoClient
                from bson import ObjectId
                client = MongoClient('mongodb://localhost:27017/')
                db = client['ai_newsfeed']
                
                article_doc = db.news_articles.find_one({'_id': ObjectId(article_id)})
                if article_doc:
                    category = article_doc.get('category', 'General')
                else:
                    print(f"[WARN] Article not found in MongoDB: {article_id}")
            except Exception as e:
                print(f"[WARN] Error fetching article from MongoDB: {e}")
        
        # Get or create preference
        pref, created = UserPreference.objects.get_or_create(
            user_id=user_id,
            category=category,
            defaults={'preference_score': 0.5, 'interaction_count': 0, 'total_dwell_time': 0}
        )
        
        # Calculate score boost based on action type and dwell time
        score_boost = 0.0
        
        if action == 'like':
            score_boost = 0.15  # Strong positive signal
        elif action == 'dislike':
            score_boost = -0.2  # Strong negative signal
        elif action == 'save':
            score_boost = 0.12  # Very strong interest
        elif action == 'share':
            score_boost = 0.10  # Strong engagement
        elif action == 'read':
            # Dwell time matters for read action
            if dwell_time > 30:
                score_boost = 0.08  # Good engagement
            elif dwell_time > 10:
                score_boost = 0.04  # Moderate engagement
            else:
                score_boost = 0.01  # Minimal engagement
        
        # Update preference score with momentum (weighted average)
        pref.preference_score = min(1.0, max(0.0, 
            pref.preference_score * 0.9 + (0.5 + score_boost) * 0.1
        ))
        
        # Update interaction metrics
        pref.interaction_count += 1
        if dwell_time > 0:
            pref.total_dwell_time += dwell_time
        
        pref.save()
        
        # Also update user interests in User model
        user = User.objects.get(id=user_id)
        if category not in user.interests:
            user.interests.append(category)
            user.save()
        
        # Update Knowledge Box for significant engagement
        if action in ['read', 'like', 'save', 'share'] and dwell_time >= 10:
            article_data = {
                '_id': article.id,
                'title': article.title,
                'summary': article.summary,
                'category': article.category
            }
            update_knowledge_box(user_id, article_data, dwell_time)
            
    except NewsArticle.DoesNotExist:
        pass
    
    return Response({**InteractionSerializer(interaction).data, 'toggled': True}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_interactions(request):
    """Get user's interactions"""
    user_id = str(request.user.id)
    action = request.query_params.get('action')
    
    interactions = Interaction.objects.filter(user_id=user_id)
    
    if action:
        interactions = interactions.filter(action=action)
        
        # Clean up duplicates for save/like/dislike actions
        if action in ['save', 'like', 'dislike']:
            # Get all interactions of this type
            all_interactions = list(interactions.order_by('-timestamp'))
            seen_articles = set()
            duplicates_to_delete = []
            
            # Keep only the most recent interaction per article
            for interaction in all_interactions:
                if interaction.article_id in seen_articles:
                    duplicates_to_delete.append(interaction.id)
                else:
                    seen_articles.add(interaction.article_id)
            
            # Delete duplicates if found
            if duplicates_to_delete:
                Interaction.objects.filter(id__in=duplicates_to_delete).delete()
                # Refresh interactions after cleanup
                interactions = Interaction.objects.filter(user_id=user_id, action=action)
    
    serializer = InteractionSerializer(interactions, many=True)
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_interaction(request):
    """Remove user interaction (unlike, unsave, etc.)"""
    user_id = str(request.user.id)
    article_id = request.data.get('article_id')
    action = request.data.get('action')
    
    if not article_id or not action:
        return Response({'error': 'article_id and action are required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Find and delete the most recent interaction of this type
    try:
        interaction = Interaction.objects.filter(
            user_id=user_id,
            article_id=article_id,
            action=action
        ).order_by('-timestamp').first()
        
        if interaction:
            interaction.delete()
            return Response({'message': f'{action} removed successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'Interaction not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_ai_snapshot(request):
    """Generate AI-powered 5-6 line summary using Claude Haiku 4.5 with Gemini failover"""
    from api.utils.gemini_summarizer import generate_summary
    
    article_id = request.data.get('article_id')
    
    if not article_id:
        return Response({'error': 'article_id is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Try Django ORM first (integer IDs)
        try:
            article_id_int = int(article_id)
            article = NewsArticle.objects.get(id=article_id_int)
        except (ValueError, TypeError, NewsArticle.DoesNotExist):
            # It's a MongoDB ObjectId, query MongoDB directly
            from pymongo import MongoClient
            from bson import ObjectId
            client = MongoClient('mongodb://localhost:27017/')
            db = client['ai_newsfeed']
            
            article_doc = db.news_articles.find_one({'_id': ObjectId(article_id)})
            if not article_doc:
                return Response({'error': 'Article not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Create a simple object with needed attributes
            class ArticleProxy:
                def __init__(self, doc):
                    self.title = doc.get('title', '')
                    self.content = doc.get('content', '')
                    self.summary = doc.get('description', doc.get('summary', ''))
            
            article = ArticleProxy(article_doc)
        
        print(f"[AI SNAPSHOT] Generating for article: {article.title}")
        print(f"[AI SNAPSHOT] Article title: {article.title}")
        
        # Use article content or summary as input
        content_to_summarize = article.content if article.content and len(article.content) > 100 else article.summary
        print(f"[AI SNAPSHOT] Content length: {len(content_to_summarize) if content_to_summarize else 0}")
        
        if not content_to_summarize or len(content_to_summarize) < 50:
            return Response({
                'error': 'Article content is too short to generate a meaningful summary.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate summary using Claude Haiku 4.5 with automatic Gemini failover
        ai_summary = generate_summary(article.title, content_to_summarize)
        
        # Record this as an interaction
        user_id = str(request.user.id)
        Interaction.objects.create(
            user_id=user_id,
            article_id=article_id,
            action='ai_snapshot',
            comment_text=''
        )
        
        # Prepare response
        response_data = {
            'summary': ai_summary,
            'article_id': article_id
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    except NewsArticle.DoesNotExist:
        return Response({'error': 'Article not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"[ERROR] AI Snapshot error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_article_comments(request):
    """Get all comments for a specific article"""
    article_id = request.query_params.get('article_id')
    
    if not article_id:
        return Response({'error': 'article_id is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Fetch all comment interactions for the article
    comments = Interaction.objects.filter(
        article_id=article_id, 
        action='comment'
    ).order_by('-timestamp')
    
    # Build response with user details (only non-empty comments)
    comments_data = []
    for comment in comments:
        # Skip empty comments
        if not comment.comment_text or comment.comment_text.strip() == '':
            continue
            
        try:
            user = User.objects.get(id=comment.user_id)
            comments_data.append({
                '_id': str(comment.id),
                'user_id': comment.user_id,
                'username': user.name,
                'profile_photo': user.profile_photo if user.profile_photo else None,
                'comment_text': comment.comment_text,
                'sentiment': comment.sentiment,
                'timestamp': comment.timestamp
            })
        except User.DoesNotExist:
            # Skip comments from deleted users
            continue
    
    return Response(comments_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_recommendations(request):
    """
    AI-Powered "AI Picks" Recommendations
    Implements comprehensive personalization based on user behavior and content analysis
    """
    user_id = str(request.user.id)
    
    try:
        user = User.objects.get(id=user_id)
        
        # Get user preferences (interest profile)
        user_preferences = UserPreference.objects.filter(user_id=user_id)
        
        # Get recent quality articles (exclude spam)
        articles = NewsArticle.objects.filter(is_spam=False).order_by('-publish_time')[:200]
        articles_data = [
            {
                '_id': str(article.id),
                'title': article.title,
                'category': article.category,
                'summary': article.summary,
                'sentiment_score': article.sentiment_score,
                'publish_time': article.publish_time,
                'image_url': article.image_url,
            }
            for article in articles
        ]
        
        # Get recent interactions to avoid repetition
        recent_interactions = Interaction.objects.filter(
            user_id=user_id
        ).order_by('-timestamp')[:50].values_list('article_id', flat=True)
        recent_article_ids = list(recent_interactions)
        
        # Generate personalized feed using AI engine
        recommended_ids = generate_personalized_feed(
            user_preferences=user_preferences,
            articles=articles_data,
            recent_interactions=recent_article_ids,
            top_n=50
        )
        
        # Get articles with full data
        if recommended_ids:
            # Preserve order from AI ranking
            id_order = {str(aid): idx for idx, aid in enumerate(recommended_ids)}
            recommended_articles = NewsArticle.objects.filter(id__in=recommended_ids)
            recommended_articles = sorted(
                recommended_articles, 
                key=lambda a: id_order.get(str(a.id), 999)
            )
        else:
            # Fallback for new users
            recommended_articles = articles[:30]
        
        # Get user's top interests for display
        top_interests = []
        if user_preferences.exists():
            top_prefs = user_preferences.order_by('-preference_score')[:5]
            top_interests = [
                {
                    'category': pref.category,
                    'score': round(pref.preference_score, 2),
                    'interactions': pref.interaction_count
                }
                for pref in top_prefs
            ]
        
        return Response({
            'articles': NewsArticleListSerializer(recommended_articles, many=True).data,
            'count': len(recommended_articles),
            'personalized': bool(user_preferences.exists()),
            'top_interests': top_interests,
            'algorithm': 'AI-powered collaborative filtering with time decay'
        })
    
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        # Silent fallback - return recent quality articles
        print(f"Recommendation error: {e}")
        articles = NewsArticle.objects.filter(is_spam=False).order_by('-publish_time')[:30]
        return Response({
            'articles': NewsArticleListSerializer(articles, many=True).data,
            'count': len(articles),
            'personalized': False,
            'top_interests': [],
            'algorithm': 'fallback'
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_knowledge_box(request):
    """
    Get user's Knowledge Box - AI-organized personal library
    """
    from .ai_modules.knowledge_extraction import get_knowledge_summary
    
    user_id = str(request.user.id)
    
    try:
        # Get organized knowledge summary
        knowledge_data = get_knowledge_summary(user_id)
        
        return Response({
            'topics': knowledge_data,
            'count': len(knowledge_data)
        })
    
    except Exception as e:
        print(f"Knowledge box error: {e}")
        return Response({
            'topics': [],
            'count': 0
        })


@api_view(['GET'])
@permission_classes([AllowAny])
def get_trending_articles(request):
    """Get trending articles based on recent interactions"""
    try:
        # Get articles with most interactions in last 24 hours
        cutoff = datetime.now() - timedelta(hours=24)
        
        # Count interactions per article
        recent_interactions = Interaction.objects.filter(timestamp__gte=cutoff)
        article_counts = {}
        
        for interaction in recent_interactions:
            aid = interaction.article_id
            if aid not in article_counts:
                article_counts[aid] = 0
            
            # Weight different actions
            if interaction.action == 'share':
                article_counts[aid] += 3
            elif interaction.action == 'like':
                article_counts[aid] += 2
            else:
                article_counts[aid] += 1
        
        # Sort by count
        sorted_articles = sorted(article_counts.items(), key=lambda x: x[1], reverse=True)
        trending_ids = [aid for aid, count in sorted_articles[:10]]
        
        # Get articles
        if trending_ids:
            articles = NewsArticle.objects.filter(id__in=trending_ids)
            if articles.count() > 0:
                return Response(NewsArticleListSerializer(articles, many=True).data)
    except Exception as e:
        print(f"Trending error: {e}")
    
    # Fallback: Return recent news from database or API (without heavy sentiment analysis)
    try:
        # Try database first - much faster
        recent_articles = NewsArticle.objects.all().order_by('-publish_time')[:10]
        if recent_articles.count() > 0:
            return Response(NewsArticleListSerializer(recent_articles, many=True).data)
    except Exception as e:
        print(f"Database fallback error: {e}")
    
    # API fallback (skip sentiment analysis for speed)
    api_articles = news_fetcher.fetch_top_headlines(page=1)
    response_data = []
    for article_data in api_articles[:10]:
        normalized = news_fetcher.normalize_article(article_data)
        
        response_data.append({
            '_id': f"temp_{hash(normalized['title'])}",
            'title': normalized['title'],
            'summary': normalized['summary'],
            'category': normalized['category'],
            'publish_time': normalized['publish_time'],
            'sentiment_score': 0.0,  # Skip sentiment analysis for faster loading
            'image_url': normalized['image_url'],
            'author': normalized['author'],
            'url': normalized['url']
        })
    
    return Response(response_data)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_categories(request):
    """Get available news categories"""
    categories = [
        'Technology', 'Business', 'Sports', 'Entertainment',
        'Health', 'Science', 'Environment', 'Politics', 'General'
    ]
    return Response({'categories': categories})


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_news(request):
    """Manually refresh news from API"""
    category = request.data.get('category')
    
    # Fetch from API
    api_articles = news_fetcher.fetch_top_headlines(category=category, page_size=50)
    
    saved_count = 0
    for article_data in api_articles:
        normalized = news_fetcher.normalize_article(article_data)
        
        # Check if exists
        existing = NewsArticle.objects.filter(title=normalized['title']).first()
        if not existing:
            sentiment_score = analyze_article_sentiment(normalized)
            is_spam, spam_score, reasons = detect_article_spam(normalized)
            
            NewsArticle.objects.create(
                title=normalized['title'],
                summary=normalized['summary'],
                content=normalized['content'],
                category=normalized['category'],
                source_id=normalized['source_id'],
                url=normalized['url'],
                image_url=normalized['image_url'],
                author=normalized['author'],
                sentiment_score=sentiment_score,
                is_spam=is_spam
            )
            saved_count += 1
    
    return Response({
        'message': f'Refreshed {saved_count} new articles',
        'total_fetched': len(api_articles)
    })


def map_news_category(api_category):
    """Map various news API categories to our standard categories"""
    category_mapping = {
        'general': 'General',
        'business': 'Business',
        'entertainment': 'Entertainment',
        'health': 'Health',
        'science': 'Science',
        'sports': 'Sports',
        'technology': 'Technology',
        'environment': 'Environment',
        'politics': 'Politics',
        'world': 'World',
        'nation': 'Politics',
        'tech': 'Technology',
        'finance': 'Business',
        'medical': 'Health',
        'gaming': 'Entertainment',
        'movies': 'Entertainment',
        'music': 'Entertainment',
        'food': 'Lifestyle',
        'travel': 'Lifestyle',
        'education': 'Education',
        'auto': 'Technology',
        'space': 'Science',
        'social media': 'Social Media',
        'twitter': 'Social Media'
    }
    
    if isinstance(api_category, str):
        return category_mapping.get(api_category.lower(), 'General')
    return 'General'


def generate_extended_fallback_news(category=None, count=100):
    """Generate extended fallback news data with multiple articles per category"""
    from datetime import datetime, timedelta
    import random
    
    categories = ['Technology', 'Business', 'Health', 'Sports', 'Entertainment', 'Environment', 'Science', 'Politics']
    
    # Base article templates for each category
    article_templates = {
        'Technology': [
            {'title': 'AI Breakthrough: New Language Model Surpasses Human Performance', 'topic': 'artificial intelligence'},
            {'title': 'Quantum Computing Milestone Achieved by Tech Giants', 'topic': 'quantum computing'},
            {'title': 'Cybersecurity Alert: New Vulnerabilities Discovered', 'topic': 'cybersecurity'},
            {'title': 'Smartphone Innovation: Revolutionary Display Technology Unveiled', 'topic': 'mobile technology'},
            {'title': 'Cloud Computing Revolution: Edge Computing Takes Center Stage', 'topic': 'cloud computing'},
            {'title': 'Blockchain Technology Transforms Financial Sector', 'topic': 'blockchain'},
            {'title': 'Virtual Reality Breakthrough: More Immersive Experiences', 'topic': 'virtual reality'},
            {'title': 'Internet of Things: Smart Cities Initiative Launches', 'topic': 'IoT'},
            {'title': '5G Network Expansion Reaches Rural Communities', 'topic': '5G technology'},
            {'title': 'Robotics Advancement: Humanoid Robots in Healthcare', 'topic': 'robotics'}
        ],
        'Business': [
            {'title': 'Stock Markets Reach Record Highs Amid Economic Recovery', 'topic': 'stock market'},
            {'title': 'Cryptocurrency Market Sees Major Institutional Investment', 'topic': 'cryptocurrency'},
            {'title': 'Global Trade Relations: New Economic Partnerships Formed', 'topic': 'international trade'},
            {'title': 'Startup Funding Boom: Venture Capital Reaches New Records', 'topic': 'venture capital'},
            {'title': 'E-commerce Growth Accelerates Post-Pandemic Recovery', 'topic': 'e-commerce'},
            {'title': 'Supply Chain Innovation: Automation Reduces Costs', 'topic': 'supply chain'},
            {'title': 'Green Finance: ESG Investing Gains Momentum', 'topic': 'sustainable finance'},
            {'title': 'Remote Work Revolution Changes Corporate Real Estate', 'topic': 'remote work'},
            {'title': 'Inflation Impact: Central Banks Adjust Monetary Policy', 'topic': 'monetary policy'},
            {'title': 'Merger & Acquisition Activity Surges in Tech Sector', 'topic': 'M&A'}
        ],
        'Health': [
            {'title': 'Medical Breakthrough: New Cancer Treatment Shows Promise', 'topic': 'cancer research'},
            {'title': 'Mental Health Awareness: Innovative Therapy Approaches', 'topic': 'mental health'},
            {'title': 'Vaccination Campaign: Global Health Initiative Success', 'topic': 'vaccination'},
            {'title': 'Telemedicine Revolution: Healthcare Accessibility Improves', 'topic': 'telemedicine'},
            {'title': 'Genetic Research: Gene Therapy Advances Treatment Options', 'topic': 'genetics'},
            {'title': 'Pharmaceutical Innovation: New Drug Development Accelerated', 'topic': 'pharmaceuticals'},
            {'title': 'Fitness Technology: Wearable Devices Monitor Health Better', 'topic': 'fitness tech'},
            {'title': 'Nutrition Science: Plant-Based Diet Benefits Confirmed', 'topic': 'nutrition'},
            {'title': 'Medical AI: Diagnostic Accuracy Improvements', 'topic': 'medical AI'},
            {'title': 'Global Health: Pandemic Preparedness Strategies Enhanced', 'topic': 'public health'}
        ],
        'Sports': [
            {'title': 'Championship Finals: Underdog Team Claims Victory', 'topic': 'championship'},
            {'title': 'Olympic Preparations: Athletes Train for Upcoming Games', 'topic': 'olympics'},
            {'title': 'Sports Technology: Performance Analytics Revolution', 'topic': 'sports tech'},
            {'title': 'Transfer News: Major League Signings Shake Up Season', 'topic': 'transfers'},
            {'title': 'Injury Recovery: Advanced Rehabilitation Techniques', 'topic': 'sports medicine'},
            {'title': 'Youth Sports: Development Programs Show Success', 'topic': 'youth sports'},
            {'title': 'Women\'s Sports: Growing Popularity and Investment', 'topic': 'women\'s sports'},
            {'title': 'Sports Broadcasting: Streaming Changes Viewing Experience', 'topic': 'sports media'},
            {'title': 'Stadium Innovation: Fan Experience Enhancements', 'topic': 'stadium tech'},
            {'title': 'Esports Growth: Professional Gaming Reaches Mainstream', 'topic': 'esports'}
        ],
        'Entertainment': [
            {'title': 'Box Office Record: Blockbuster Film Breaks Opening Weekend', 'topic': 'movies'},
            {'title': 'Streaming Wars: New Platform Launches with Exclusive Content', 'topic': 'streaming'},
            {'title': 'Music Industry: Artists Embrace NFT Technology', 'topic': 'music'},
            {'title': 'Gaming Revolution: Virtual Reality Gaming Advances', 'topic': 'gaming'},
            {'title': 'Celebrity News: Star Announces Major Career Change', 'topic': 'celebrities'},
            {'title': 'Television Golden Age: Award-Winning Series Renewed', 'topic': 'television'},
            {'title': 'Concert Industry: Live Music Returns Post-Pandemic', 'topic': 'concerts'},
            {'title': 'Social Media: Platform Updates Change User Experience', 'topic': 'social media'},
            {'title': 'Fashion Week: Sustainable Fashion Takes Center Stage', 'topic': 'fashion'},
            {'title': 'Book Publishing: Digital Reading Trends Evolve', 'topic': 'publishing'}
        ],
        'Environment': [
            {'title': 'Climate Change: Renewable Energy Targets Exceeded', 'topic': 'climate change'},
            {'title': 'Conservation Success: Endangered Species Population Recovers', 'topic': 'conservation'},
            {'title': 'Ocean Cleanup: Innovative Technology Removes Plastic Waste', 'topic': 'ocean cleanup'},
            {'title': 'Solar Power: Efficiency Records Broken in New Installations', 'topic': 'solar energy'},
            {'title': 'Carbon Capture: Technology Advances Fight Global Warming', 'topic': 'carbon capture'},
            {'title': 'Sustainable Agriculture: Farming Practices Reduce Environmental Impact', 'topic': 'agriculture'},
            {'title': 'Electric Vehicles: Adoption Rates Surge Worldwide', 'topic': 'electric vehicles'},
            {'title': 'Reforestation Project: Million Trees Planted Successfully', 'topic': 'reforestation'},
            {'title': 'Water Conservation: Smart Systems Reduce Waste', 'topic': 'water conservation'},
            {'title': 'Green Building: Sustainable Architecture Gains Popularity', 'topic': 'green building'}
        ],
        'Science': [
            {'title': 'Space Exploration: Mars Mission Makes Historic Discovery', 'topic': 'space'},
            {'title': 'Physics Breakthrough: Quantum Mechanics Theory Confirmed', 'topic': 'physics'},
            {'title': 'Archaeological Find: Ancient Civilization Uncovered', 'topic': 'archaeology'},
            {'title': 'Marine Biology: New Deep Sea Species Discovered', 'topic': 'marine biology'},
            {'title': 'Astronomy: Exoplanet with Earth-like Conditions Found', 'topic': 'astronomy'},
            {'title': 'Chemistry Innovation: New Materials Revolutionize Industry', 'topic': 'chemistry'},
            {'title': 'Paleontology: Dinosaur Fossil Reveals New Information', 'topic': 'paleontology'},
            {'title': 'Neuroscience: Brain Research Unlocks Memory Mysteries', 'topic': 'neuroscience'},
            {'title': 'Geology: Earthquake Prediction Methods Improve', 'topic': 'geology'},
            {'title': 'Biotechnology: CRISPR Gene Editing Advances', 'topic': 'biotechnology'}
        ],
        'Politics': [
            {'title': 'Election Results: Voter Turnout Reaches Historic Levels', 'topic': 'elections'},
            {'title': 'Policy Reform: New Legislation Addresses Social Issues', 'topic': 'policy'},
            {'title': 'International Relations: Diplomatic Summit Yields Agreement', 'topic': 'diplomacy'},
            {'title': 'Government Transparency: Open Data Initiative Launched', 'topic': 'transparency'},
            {'title': 'Economic Policy: Tax Reform Proposal Under Review', 'topic': 'economic policy'},
            {'title': 'Social Justice: Civil Rights Legislation Advances', 'topic': 'civil rights'},
            {'title': 'Immigration Policy: Reform Measures Gain Support', 'topic': 'immigration'},
            {'title': 'Defense Strategy: Military Modernization Program Updated', 'topic': 'defense'},
            {'title': 'Healthcare Policy: Universal Coverage Debate Continues', 'topic': 'healthcare policy'},
            {'title': 'Education Reform: Funding Initiatives Show Promise', 'topic': 'education policy'}
        ]
    }
    
    articles = []
    target_categories = [category] if category and category != 'All' else categories
    articles_per_category = max(count // len(target_categories), 10)
    
    for cat in target_categories:
        templates = article_templates.get(cat, article_templates['Technology'])
        
        for i in range(articles_per_category):
            template_idx = i % len(templates)
            template = templates[template_idx]
            
            article = {
                '_id': f'{cat.lower()}_{i+1}_{random.randint(1000, 9999)}',
                'title': f"{template['title']} - Latest Updates {i+1}",
                'summary': f"Comprehensive coverage of {template['topic']} developments with expert analysis and insights. This story covers the latest developments in {template['topic']} and their impact on the industry and society.",
                'category': cat,
                'publish_time': (datetime.now() - timedelta(hours=random.randint(1, 72))).isoformat(),
                'sentiment_score': random.uniform(0.3, 0.9),
                'image_url': f'https://picsum.photos/600/400?random={random.randint(1, 1000)}&{cat.lower()}',
                'author': f'{cat} Reporter {random.randint(1, 50)}',
                'url': f'https://example.com/{cat.lower()}-news-{i+1}',
                'source': f'{cat} News Network'
            }
            articles.append(article)
    
    return articles[:count] if count else articles


@api_view(['GET'])
@permission_classes([AllowAny])
def fetch_full_article_content(request):
    """Fetch full article content from the source URL using multiple methods"""
    url = request.query_params.get('url')
    article_title = request.query_params.get('title', '')
    
    if not url:
        return Response({'error': 'URL parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    print(f"\n{'='*80}")
    print(f"[FETCH CONTENT] URL: {url}")
    print(f"[FETCH CONTENT] Title: {article_title}")
    print(f"{'='*80}\n")
    
    # Method 0: Try NewsData.io API first (Best quality with API)
    try:
        import re
        NEWSDATA_API_KEY = 'pub_619c113387574246a999cb70deeeef32'
        
        # Extract domain from URL for NewsData.io search
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        
        # Search for the article using domain and title
        search_query = article_title if article_title else domain
        
        newsdata_url = f'https://newsdata.io/api/1/news?apikey={NEWSDATA_API_KEY}&q={search_query}&language=en'
        
        print(f"[SEARCH] Trying NewsData.io API with query: {search_query[:50]}...")
        response = requests.get(newsdata_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('results') and len(data['results']) > 0:
                # Find article matching the URL or title
                for article in data['results'][:5]:  # Check first 5 results
                    article_url = article.get('link', '')
                    article_content = article.get('content') or article.get('description', '')
                    
                    # Match by URL or title similarity
                    if url in article_url or article_url in url or (article_title and article_title.lower() in article.get('title', '').lower()):
                        if article_content and len(article_content) > 200:
                            cleaned_content = clean_article_text(article_content)
                            print(f"[OK] Method 0 (NewsData.io API): Successfully fetched {len(cleaned_content)} characters")
                            return Response({
                                'content': cleaned_content,
                                'success': True,
                                'method': 'newsdata_api',
                                'title': article.get('title', '')
                            })
        
        print("[WARN] Method 0 (NewsData.io) didn't find matching article, trying other methods...")
    
    except Exception as e:
        print(f"[WARN] Method 0 (NewsData.io API) failed: {str(e)}")
    
    # Method 0.5: Try GNews API
    try:
        GNEWS_API_KEY = '32896d007c16b2a520dac2a8ba34fac9'
        
        # Try to search by title or extract keywords from URL
        search_query = article_title if article_title else url.split('/')[-1].replace('-', ' ')[:50]
        
        gnews_url = f'https://gnews.io/api/v4/search?q={search_query}&lang=en&token={GNEWS_API_KEY}&max=5'
        
        print(f"[SEARCH] Trying GNews API with query: {search_query[:50]}...")
        response = requests.get(gnews_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('articles') and len(data['articles']) > 0:
                # Find article matching the URL or title
                for article in data['articles']:
                    article_url = article.get('url', '')
                    article_content = article.get('content', '')
                    
                    # Match by URL or title similarity
                    if url in article_url or article_url in url or (article_title and article_title.lower() in article.get('title', '').lower()):
                        if article_content and len(article_content) > 200:
                            cleaned_content = clean_article_text(article_content)
                            print(f"[OK] Method 0.5 (GNews API): Successfully fetched {len(cleaned_content)} characters")
                            return Response({
                                'content': cleaned_content,
                                'success': True,
                                'method': 'gnews_api',
                                'title': article.get('title', '')
                            })
        
        print("[WARN] Method 0.5 (GNews) didn't find matching article, trying other methods...")
    
    except Exception as e:
        print(f"[WARN] Method 0.5 (GNews API) failed: {str(e)}")
    
    # Method 1: Try using newspaper3k (if available)
    try:
        from newspaper import Article
        
        article = Article(url)
        article.download()
        article.parse()
        
        full_text = article.text
        
        if full_text and len(full_text) > 100:
            full_text = clean_article_text(full_text)
            print(f"[OK] Method 1 (newspaper3k): Successfully extracted {len(full_text)} characters")
            return Response({'content': full_text, 'success': True, 'method': 'newspaper3k'})
    except ImportError:
        print("[WARN] newspaper3k not installed, trying alternative methods")
    except Exception as e:
        print(f"[WARN] Method 1 (newspaper3k) failed: {str(e)}")
    
    # Method 2: Try BeautifulSoup with requests
    try:
        from bs4 import BeautifulSoup
        import re
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script, style, and other non-content elements
        for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe', 'noscript']):
            tag.decompose()
        
        # Try to find article content in common containers
        article_content = None
        
        # Try common article selectors
        selectors = [
            'article',
            '[role="article"]',
            '.article-content',
            '.post-content',
            '.entry-content',
            '.story-body',
            '.article-body',
            '#article-content',
            '.content',
            'main'
        ]
        
        for selector in selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                article_content = content_elem
                break
        
        if not article_content:
            # Fallback: get all paragraphs
            article_content = soup
        
        # Extract text from paragraphs
        paragraphs = article_content.find_all('p')
        full_text = '\n\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
        
        if full_text and len(full_text) > 100:
            full_text = clean_article_text(full_text)
            print(f"[OK] Method 2 (BeautifulSoup): Successfully extracted {len(full_text)} characters")
            return Response({'content': full_text, 'success': True, 'method': 'beautifulsoup'})
    
    except Exception as e:
        print(f"[WARN] Method 2 (BeautifulSoup) failed: {str(e)}")
    
    # Method 3: Simple requests + basic text extraction
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Simple HTML tag removal
        text = response.text
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        # Try to extract meaningful content (paragraphs with reasonable length)
        sentences = text.split('.')
        meaningful_content = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 50 and len(sentence) < 500:
                meaningful_content.append(sentence)
        
        full_text = '. '.join(meaningful_content[:50])  # Limit to first 50 sentences
        
        if full_text and len(full_text) > 200:
            full_text = clean_article_text(full_text)
            print(f"[OK] Method 3 (basic extraction): Successfully extracted {len(full_text)} characters")
            return Response({'content': full_text, 'success': True, 'method': 'basic'})
    
    except Exception as e:
        print(f"[WARN] Method 3 (basic extraction) failed: {str(e)}")
    
    # All methods failed - Generate comprehensive explanation from summary
    print(f"[ERROR] External extraction failed, generating explanation from available data...")
    
    try:
        # Try to get the article from database - first by URL, then by title
        print(f"[DATABASE LOOKUP] Searching for URL: {url[:100]}")
        article_obj = NewsArticle.objects.filter(url=url).first()
        
        if not article_obj and article_title:
            # Try matching by title if URL doesn't work
            print(f"[DATABASE LOOKUP] URL not found, searching by title: {article_title[:50]}...")
            article_obj = NewsArticle.objects.filter(title__icontains=article_title[:50]).first()
        
        if article_obj:
            print(f"[FOUND] Article ID: {article_obj.id}")
            print(f"[FOUND] Article Title: {article_obj.title[:80]}")
            print(f"[FOUND] Existing content length: {len(article_obj.content) if article_obj.content else 0} chars")
            
            # Use whichever is available: summary, content, or title
            base_text = article_obj.summary if article_obj.summary else (article_obj.content if article_obj.content else article_obj.title)
            
            if base_text and len(base_text) > 20:
                # Check if we already have generated full content stored
                if article_obj.content and len(article_obj.content) > 1000:
                    print(f"[CACHED] Using existing full content for: {article_obj.title[:80]}")
                    print(f"[CACHED] Content length: {len(article_obj.content)} chars")
                    
                    return Response({
                        'content': article_obj.content,
                        'success': True,
                        'method': 'cached_content',
                        'note': 'Full article content'
                    })
                
                # Generate comprehensive article using OpenAI
                print(f"[GENERATE] Creating full article for: {article_obj.title[:80]}")
                print(f"[GENERATE] Summary length: {len(base_text)} chars")
                print(f"[GENERATE] Category: {article_obj.category}")
                
                full_article = generate_full_article_with_openai(
                    title=article_obj.title,
                    summary=base_text,
                    category=article_obj.category,
                    source=article_obj.source,
                    publish_time=article_obj.publish_time
                )
                
                if full_article:
                    # Store the generated content for future use
                    article_obj.content = full_article
                    article_obj.save()
                    print(f"[SUCCESS] Generated and saved full article: {len(full_article)} characters")
                    
                    return Response({
                        'content': full_article,
                        'success': True,
                        'method': 'openai_generated',
                        'note': 'Full article content'
                    })
                else:
                    # Fallback to minimal explanation if OpenAI fails
                    print(f"[FALLBACK] OpenAI generation failed, using minimal content")
                    expanded_content = generate_detailed_explanation(
                        base_text,
                        article_obj.title,
                        article_obj.category
                    )
                    
                    return Response({
                        'content': expanded_content,
                        'success': True,
                        'method': 'fallback_explanation',
                        'note': 'Generated comprehensive explanation from available information'
                    })
            else:
                print(f"[WARN] No sufficient text available (summary: {len(article_obj.summary) if article_obj.summary else 0}, content: {len(article_obj.content) if article_obj.content else 0})")
        else:
            print(f"[WARN] Article not found in database for URL: {url} or title: {article_title}")
            
    except Exception as e:
        print(f"[WARN] Could not generate explanation: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print(f"[ERROR] All methods failed to extract content from: {url}")
    return Response({
        'error': 'Could not extract content from the article. The website may have anti-scraping protection.',
        'content': '',
        'success': False
    }, status=status.HTTP_404_NOT_FOUND)


def clean_article_text(text):
    """Clean extracted article text"""
    import re
    
    # Remove multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove image credits and copyright notices
    text = re.sub(r'\(Image credit:.*?\)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Photo by.*?\n', '', text)
    text = re.sub(r'�.*?\n', '', text)
    text = re.sub(r'Image:.*?\n', '', text, flags=re.IGNORECASE)
    
    # Remove social media prompts
    text = re.sub(r'(Share on|Follow us|Subscribe)', '', text, flags=re.IGNORECASE)
    
    # Remove URLs
    text = re.sub(r'http[s]?://\S+', '', text)
    
    # Clean up whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    text = '\n'.join([line.strip() for line in text.split('\n') if line.strip()])
    
    return text.strip()


def generate_full_article_with_openai(title, summary, category, source, publish_time):
    """
    Generate a complete, professional 1500-2000 word news article using OpenAI.
    Returns None if all API attempts fail.
    """
    from django.conf import settings
    import re
    from datetime import datetime
    
    # Clean the summary
    summary = re.sub(r'\[\+\d+\s+chars?\]', '', summary)
    summary = re.sub(r'\.\.\.$', '', summary.strip())
    
    # Format publish time
    try:
        if isinstance(publish_time, str):
            pub_time = datetime.fromisoformat(publish_time.replace('Z', '+00:00'))
        else:
            pub_time = publish_time
        time_str = pub_time.strftime("%B %d, %Y")
    except:
        time_str = "Recently"
    
    # Collect all available API keys
    api_keys = []
    for i in range(1, 6):
        key_name = 'OPENAI_API_KEY' if i == 1 else f'OPENAI_API_KEY_{i}'
        if hasattr(settings, key_name):
            key = getattr(settings, key_name)
            if key:
                api_keys.append(key)
    
    if not api_keys:
        print("[ERROR] No OpenAI API keys available")
        return None
    
    # Create the prompt for article generation
    prompt = f"""Write a complete, professional news article based on the following information:

Title: {title}
Source: {source}
Category: {category}
Date: {time_str}
Summary: {summary}

Write a comprehensive news article (1500-2000 words) that:
- Expands on the summary with relevant context and background
- Provides analysis of why this matters
- Discusses potential implications and future developments
- Uses a neutral, professional journalistic tone
- Flows naturally like a real news report
- Does NOT use headings, bullet points, or labels
- Does NOT mention AI or indicate this is generated content
- Stays focused on the topic without introducing unrelated information

Write the article as continuous paragraphs, starting immediately with the content. Make it informative, engaging, and professionally written."""

    # Try each API key until one works
    for idx, api_key in enumerate(api_keys):
        try:
            print(f"[OPENAI] Attempting article generation with key #{idx + 1}...")
            from openai import OpenAI
            
            client = OpenAI(api_key=api_key, timeout=60.0)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo-16k",  # Use 16k model for longer content
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional news journalist. Write comprehensive, well-researched news articles in a neutral, informative style. Never use headings, labels, or reveal that you are AI."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=2500,
                temperature=0.7,
                presence_penalty=0.3,
                frequency_penalty=0.3
            )
            
            article_content = response.choices[0].message.content.strip()
            
            # Verify we got substantial content
            if len(article_content) < 800:
                print(f"[WARN] Generated article too short ({len(article_content)} chars), trying next key...")
                continue
            
            print(f"[SUCCESS] Generated full article using key #{idx + 1}: {len(article_content)} characters")
            return article_content
            
        except Exception as e:
            error_msg = str(e)
            if "quota" in error_msg.lower() or "insufficient_quota" in error_msg.lower():
                print(f"[WARN] API key #{idx + 1} quota exceeded, trying next key...")
                continue
            elif "context_length" in error_msg.lower():
                print(f"[WARN] Context length exceeded with key #{idx + 1}, trying with shorter prompt...")
                # Try with shorter summary
                try:
                    short_prompt = f"""Write a complete news article (1500-2000 words) about: {title}

Summary: {summary[:500]}

Write professionally without headings or labels. Use neutral journalistic tone."""
                    
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a professional journalist."},
                            {"role": "user", "content": short_prompt}
                        ],
                        max_tokens=2000,
                        temperature=0.7
                    )
                    article_content = response.choices[0].message.content.strip()
                    if len(article_content) >= 800:
                        print(f"[SUCCESS] Generated article with shorter prompt: {len(article_content)} chars")
                        return article_content
                except:
                    pass
                continue
            else:
                print(f"[WARN] API key #{idx + 1} error: {e}")
                continue
    
    print("[ERROR] All OpenAI API keys failed to generate article")
    return None


def generate_detailed_explanation(summary, title, category):
    """
    Return article text when external content can't be fetched.
    Keep only the available summary/content without duplicate headers or filler.
    """
    import re

    summary = re.sub(r'\[\+\d+\s+chars?\]', '', summary or '')
    summary = re.sub(r'\.\.\.$', '', summary.strip())

    return summary


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_streak(request):
    """Calculate user's current day streak based on reading interactions"""
    user_id = str(request.user.id)
    interactions = Interaction.objects.filter(user_id=user_id, action='read').order_by('timestamp')
    if not interactions:
        return Response({'streak_days': 0})

    # Get all unique reading dates
    dates = set()
    for interaction in interactions:
        dates.add(interaction.timestamp.date())
    if not dates:
        return Response({'streak_days': 0})

    # Calculate streak up to today
    today = datetime.utcnow().date()
    streak = 0
    current = today
    while current in dates:
        streak += 1
        current -= timedelta(days=1)
    return Response({'streak_days': streak})


@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def proxy_image(request):
    """Proxy external images through backend to avoid CORS issues"""
    from django.http import StreamingHttpResponse, HttpResponse
    import io
    import urllib.parse
    
    # Handle CORS preflight requests
    if request.method == 'OPTIONS':
        response = HttpResponse()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    # Get URL from query params - use request.GET instead of query_params
    image_url = request.GET.get('url')
    
    if not image_url:
        print("ERROR: Missing url parameter")
        return Response({'error': 'Missing url parameter'}, status=status.HTTP_400_BAD_REQUEST)
    
    print(f"Proxy request for image: {image_url[:80]}")
    
    try:
        # URL decode if needed
        if '%' in image_url:
            image_url = urllib.parse.unquote(image_url)
        
        print(f"Fetching image from: {image_url[:80]}")
        
        # Request with proper headers to avoid 403
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(image_url, headers=headers, timeout=10, verify=False)
        
        print(f"Image fetch status: {response.status_code}")
        
        if response.status_code == 200:
            # Return the image as streaming response with proper CORS headers
            http_response = StreamingHttpResponse(
                io.BytesIO(response.content),
                content_type=response.headers.get('content-type', 'image/jpeg')
            )
            http_response['Access-Control-Allow-Origin'] = '*'
            http_response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
            http_response['Cache-Control'] = 'max-age=86400'
            return http_response
        else:
            print(f"ERROR: Image fetch failed with status {response.status_code}")
            return Response(
                {'error': f'Failed to fetch image: {response.status_code}'},
                status=status.HTTP_502_BAD_GATEWAY
            )
    except Exception as e:
        print(f"Image proxy error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response(
            {'error': f'Image proxy error: {str(e)}'},
            status=status.HTTP_502_BAD_GATEWAY
        )

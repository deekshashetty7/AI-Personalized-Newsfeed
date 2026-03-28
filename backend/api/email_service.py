"""
Email service for sending OTP and other emails
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings


def send_otp_email(email, otp):
    """
    Send OTP to the user's email
    """
    try:
        # Email configuration
        sender_email = getattr(settings, 'EMAIL_HOST_USER', 'noreply@infocred.com')
        sender_password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
        smtp_server = getattr(settings, 'EMAIL_HOST', 'smtp.gmail.com')
        smtp_port = getattr(settings, 'EMAIL_PORT', 587)
        
        # Create message
        message = MIMEMultipart('alternative')
        message['Subject'] = 'InfoCred - Email Verification Code'
        message['From'] = f'InfoCred <{sender_email}>'
        message['To'] = email
        
        # Email body (HTML)
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .content {{
                    background: #f9f9f9;
                    padding: 30px;
                    border-radius: 0 0 10px 10px;
                }}
                .otp-code {{
                    background: white;
                    border: 2px dashed #667eea;
                    padding: 20px;
                    text-align: center;
                    font-size: 32px;
                    font-weight: bold;
                    letter-spacing: 5px;
                    color: #667eea;
                    margin: 20px 0;
                    border-radius: 5px;
                }}
                .info {{
                    background: #e8f4f8;
                    border-left: 4px solid #3498db;
                    padding: 15px;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    color: #666;
                    font-size: 12px;
                    margin-top: 30px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📧 Email Verification</h1>
                    <p>Welcome to InfoCred - Personalized News, Verified Trust</p>
                </div>
                <div class="content">
                    <h2>Hello!</h2>
                    <p>Thank you for registering with InfoCred. To complete your registration, please use the following One-Time Password (OTP):</p>
                    
                    <div class="otp-code">
                        {otp}
                    </div>
                    
                    <div class="info">
                        <strong>⏰ Important:</strong> This OTP is valid for 10 minutes only.
                    </div>
                    
                    <p><strong>Security Tips:</strong></p>
                    <ul>
                        <li>Never share this OTP with anyone</li>
                        <li>InfoCred will never ask for your OTP via phone or email</li>
                        <li>If you didn't request this, please ignore this email</li>
                    </ul>
                    
                    <div class="footer">
                        <p>This is an automated message from InfoCred. Please do not reply to this email.</p>
                        <p>&copy; 2025 InfoCred. All rights reserved.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        text_body = f"""
        InfoCred - Email Verification
        
        Hello!
        
        Thank you for registering with InfoCred. To complete your registration, please use the following OTP:
        
        {otp}
        
        This OTP is valid for 10 minutes only.
        
        Security Tips:
        - Never share this OTP with anyone
        - InfoCred will never ask for your OTP via phone or email
        - If you didn't request this, please ignore this email
        
        ---
        This is an automated message from InfoCred.
        © 2025 InfoCred. All rights reserved.
        """
        
        # Attach both versions
        part1 = MIMEText(text_body, 'plain')
        part2 = MIMEText(html_body, 'html')
        message.attach(part1)
        message.attach(part2)
        
        # If no SMTP credentials configured, print to console (development mode)
        if not sender_password:
            print(f"\n{'='*60}")
            print(f"📧 EMAIL SENDING (DEVELOPMENT MODE)")
            print(f"{'='*60}")
            print(f"To: {email}")
            print(f"Subject: InfoCred - Email Verification Code")
            print(f"OTP: {otp}")
            print(f"Expires: 10 minutes")
            print(f"{'='*60}\n")
            return {
                'success': True,
                'message': 'OTP sent successfully (development mode - check console)',
                'mode': 'development'
            }
        
        # Send email via SMTP
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(message)
        
        print(f"✅ OTP email sent successfully to {email}")
        return {
            'success': True,
            'message': 'OTP sent successfully to your email',
            'mode': 'production'
        }
        
    except Exception as e:
        print(f"❌ Error sending OTP email: {str(e)}")
        # In development, still return success and print OTP
        print(f"\n{'='*60}")
        print(f"📧 EMAIL SENDING FAILED - SHOWING OTP")
        print(f"{'='*60}")
        print(f"To: {email}")
        print(f"OTP: {otp}")
        print(f"Error: {str(e)}")
        print(f"{'='*60}\n")
        
        return {
            'success': True,
            'message': 'OTP generated (check console for code)',
            'mode': 'fallback',
            'error': str(e)
        }


def send_welcome_email(email, name):
    """
    Send welcome email after successful verification
    """
    try:
        sender_email = getattr(settings, 'EMAIL_HOST_USER', 'noreply@infocred.com')
        sender_password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
        smtp_server = getattr(settings, 'EMAIL_HOST', 'smtp.gmail.com')
        smtp_port = getattr(settings, 'EMAIL_PORT', 587)
        
        message = MIMEMultipart('alternative')
        message['Subject'] = 'Welcome to InfoCred!'
        message['From'] = f'InfoCred <{sender_email}>'
        message['To'] = email
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .content {{
                    background: #f9f9f9;
                    padding: 30px;
                    border-radius: 0 0 10px 10px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Welcome to InfoCred!</h1>
                </div>
                <div class="content">
                    <h2>Hello {name}!</h2>
                    <p>Your email has been successfully verified. Welcome to InfoCred - your personalized news platform.</p>
                    <p><strong>What you can do now:</strong></p>
                    <ul>
                        <li>📰 Browse personalized news based on your interests</li>
                        <li>🔍 Search for specific topics and articles</li>
                        <li>⭐ Get AI-powered recommendations</li>
                        <li>📊 View trending and recent news</li>
                    </ul>
                    <p>Happy reading!</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        part = MIMEText(html_body, 'html')
        message.attach(part)
        
        if not sender_password:
            print(f"✅ Welcome email sent (development mode) to {email}")
            return {'success': True}
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(message)
        
        print(f"✅ Welcome email sent to {email}")
        return {'success': True}
        
    except Exception as e:
        print(f"⚠️ Could not send welcome email: {str(e)}")
        return {'success': False, 'error': str(e)}


def send_password_reset_otp(email, otp):
    """
    Send OTP for password reset
    """
    try:
        sender_email = getattr(settings, 'EMAIL_HOST_USER', 'noreply@infocred.com')
        sender_password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
        smtp_server = getattr(settings, 'EMAIL_HOST', 'smtp.gmail.com')
        smtp_port = getattr(settings, 'EMAIL_PORT', 587)
        
        message = MIMEMultipart('alternative')
        message['Subject'] = 'AI NewsFeed - Password Reset OTP'
        message['From'] = f'AI NewsFeed <{sender_email}>'
        message['To'] = email
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .content {{
                    background: #f9f9f9;
                    padding: 30px;
                    border-radius: 0 0 10px 10px;
                }}
                .otp-box {{
                    background: white;
                    border: 2px dashed #667eea;
                    padding: 20px;
                    text-align: center;
                    border-radius: 10px;
                    margin: 20px 0;
                }}
                .otp-code {{
                    font-size: 36px;
                    font-weight: bold;
                    color: #667eea;
                    letter-spacing: 8px;
                    font-family: 'Courier New', monospace;
                }}
                .warning {{
                    background: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Password Reset OTP</h1>
                </div>
                <div class="content">
                    <h2>Hello!</h2>
                    <p>We received a request to reset your AI NewsFeed account password.</p>
                    <p>Use the following One-Time Password (OTP) to reset your password:</p>
                    
                    <div class="otp-box">
                        <div class="otp-code">{otp}</div>
                    </div>
                    
                    <div class="warning">
                        <strong>⏰ Important:</strong> This OTP is valid for 10 minutes only.
                    </div>
                    
                    <p><strong>Security Tips:</strong></p>
                    <ul>
                        <li>If you didn't request this reset, please ignore this email</li>
                        <li>Never share your OTP with anyone</li>
                        <li>AI NewsFeed will never ask for your OTP via phone or chat</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        AI NewsFeed - Password Reset OTP
        
        Hello!
        
        We received a request to reset your AI NewsFeed account password.
        
        Your One-Time Password (OTP):
        {otp}
        
        ⏰ Important: This OTP is valid for 10 minutes only.
        
        Security Tips:
        - If you didn't request this reset, please ignore this email
        - Never share your OTP with anyone
        - AI NewsFeed will never ask for your OTP via phone or chat
        
        Best regards,
        AI NewsFeed Team
        """
        
        part1 = MIMEText(text_body, 'plain')
        part2 = MIMEText(html_body, 'html')
        message.attach(part1)
        message.attach(part2)
        
        # Development mode - print to console
        if not sender_password or sender_password == '':
            print(f"\n{'='*60}")
            print(f"📧 PASSWORD RESET OTP EMAIL (Development Mode)")
            print(f"{'='*60}")
            print(f"To: {email}")
            print(f"Subject: AI NewsFeed - Password Reset OTP")
            print(f"OTP: {otp}")
            print(f"Expires: 10 minutes")
            print(f"{'='*60}\n")
            return {
                'success': True,
                'message': 'OTP sent successfully (development mode - check console)',
                'mode': 'development'
            }
        
        # Send email via SMTP
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(message)
        
        print(f"✅ Password reset OTP email sent successfully to {email}")
        return {
            'success': True,
            'message': 'OTP sent successfully to your email',
            'mode': 'production'
        }
        
    except Exception as e:
        print(f"❌ Error sending password reset OTP email: {str(e)}")
        # In development, still return success and print OTP
        print(f"\n{'='*60}")
        print(f"📧 EMAIL SENDING FAILED - SHOWING OTP")
        print(f"{'='*60}")
        print(f"To: {email}")
        print(f"OTP: {otp}")
        print(f"Error: {str(e)}")
        print(f"{'='*60}\n")
        
        return {
            'success': True,
            'message': 'OTP generated (check console for code)',
            'mode': 'fallback',
            'error': str(e)
        }


def send_password_reset_email(email, reset_link):
    """
    Send password reset email with reset link
    """
    try:
        sender_email = getattr(settings, 'EMAIL_HOST_USER', 'noreply@infocred.com')
        sender_password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
        smtp_server = getattr(settings, 'EMAIL_HOST', 'smtp.gmail.com')
        smtp_port = getattr(settings, 'EMAIL_PORT', 587)
        
        message = MIMEMultipart('alternative')
        message['Subject'] = 'InfoCred - Password Reset Request'
        message['From'] = f'InfoCred <{sender_email}>'
        message['To'] = email
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .content {{
                    background: #f9f9f9;
                    padding: 30px;
                    border-radius: 0 0 10px 10px;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 30px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .warning {{
                    background: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Password Reset Request</h1>
                </div>
                <div class="content">
                    <h2>Hello!</h2>
                    <p>We received a request to reset your InfoCred account password.</p>
                    <p>Click the button below to reset your password:</p>
                    <p style="text-align: center;">
                        <a href="{reset_link}" class="button">Reset Password</a>
                    </p>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; background: #f0f0f0; padding: 10px; border-radius: 5px;">
                        {reset_link}
                    </p>
                    <div class="warning">
                        <strong>⏰ Important:</strong> This link is valid for 1 hour only.
                    </div>
                    <p><strong>Security Tips:</strong></p>
                    <ul>
                        <li>If you didn't request this reset, please ignore this email</li>
                        <li>Never share your password with anyone</li>
                        <li>InfoCred will never ask for your password via email</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        InfoCred - Password Reset Request
        
        Hello!
        
        We received a request to reset your InfoCred account password.
        
        Click or copy the link below to reset your password:
        {reset_link}
        
        ⏰ Important: This link is valid for 1 hour only.
        
        Security Tips:
        - If you didn't request this reset, please ignore this email
        - Never share your password with anyone
        - InfoCred will never ask for your password via email
        
        ---
        This is an automated message from InfoCred.
        © 2025 InfoCred. All rights reserved.
        """
        
        part1 = MIMEText(text_body, 'plain')
        part2 = MIMEText(html_body, 'html')
        message.attach(part1)
        message.attach(part2)
        
        # If no SMTP credentials, print to console (development mode)
        if not sender_password:
            print(f"\n{'='*60}")
            print(f"📧 PASSWORD RESET EMAIL (DEVELOPMENT MODE)")
            print(f"{'='*60}")
            print(f"To: {email}")
            print(f"Reset Link: {reset_link}")
            print(f"{'='*60}\n")
            return {
                'success': True,
                'message': 'Password reset link sent (development mode - check console)',
                'mode': 'development'
            }
        
        # Send email via SMTP
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(message)
        
        print(f"✅ Password reset email sent to {email}")
        return {
            'success': True,
            'message': 'Password reset email sent successfully',
            'mode': 'production'
        }
        
    except Exception as e:
        print(f"❌ Error sending password reset email: {str(e)}")
        print(f"\n{'='*60}")
        print(f"📧 EMAIL SENDING FAILED - SHOWING RESET LINK")
        print(f"{'='*60}")
        print(f"To: {email}")
        print(f"Reset Link: {reset_link}")
        print(f"Error: {str(e)}")
        print(f"{'='*60}\n")
        
        return {
            'success': True,
            'message': 'Reset link generated (check console)',
            'mode': 'fallback',
            'error': str(e)
        }


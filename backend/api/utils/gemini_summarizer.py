"""
AI-powered summary generator with Gemini (primary) and OpenAI (fallback)
Supports multiple API keys with automatic rotation when one fails
"""

import os
from typing import Optional, List

# Try to import Google Generative AI
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    print("[WARN] google-generativeai not installed. Install with: pip install google-generativeai")

# Load API keys from environment variables (safe approach)
GEMINI_API_KEYS = []
if os.getenv('GEMINI_API_KEY'):
    GEMINI_API_KEYS = [os.getenv('GEMINI_API_KEY')]

# OpenAI API keys for fallback when Gemini limits are exceeded
OPENAI_API_KEYS = []
if os.getenv('OPENAI_API_KEY'):
    OPENAI_API_KEYS = [os.getenv('OPENAI_API_KEY')]


def generate_summary_with_openai(title: str, content: str) -> Optional[str]:
    """
    Generate a 5-6 line summary using OpenAI GPT-3.5-turbo
    Automatically tries multiple API keys if one fails
    
    Args:
        title: Article title
        content: Article content to summarize (will be truncated to 3000 chars)
    
    Returns:
        str: Generated summary or None if all keys fail
    """
    try:
        from openai import OpenAI
    except ImportError:
        print("[WARN] openai package not installed. Install with: pip install openai")
        return None
    
    # Truncate content to reasonable length
    content_to_summarize = content[:3000] if len(content) > 3000 else content
    
    # Create the prompt
    prompt = f"""Summarize this news article in exactly 5-6 lines. 

Use a professional, neutral tone without bullet points, headings, or AI-related terminology.
Write it as editorial content that feels natural and human-written.

Title: {title}

Content: {content_to_summarize}

Summary:"""
    
    # Try each API key until one works
    for idx, api_key in enumerate(OPENAI_API_KEYS, 1):
        # Skip empty keys
        if not api_key or len(api_key) < 20:
            continue
            
        try:
            print(f"[OPENAI] Trying API key #{idx}...")
            
            # Initialize OpenAI client
            client = OpenAI(api_key=api_key)
            
            # Generate summary using GPT-3.5-turbo
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional news journalist. Summarize articles concisely in 5-6 lines without using bullet points or revealing that you are AI."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            # Extract the summary
            if response and response.choices:
                summary = response.choices[0].message.content.strip()
                print(f"[SUCCESS] Generated summary with OpenAI key #{idx}")
                print(f"[OPENAI] Summary preview: {summary[:100]}...")
                return summary
                
        except Exception as e:
            error_msg = str(e)
            print(f"[WARN] OpenAI API key #{idx} failed: {error_msg[:100]}")
            
            # Check if it's a quota/rate limit error
            if any(keyword in error_msg.lower() for keyword in ['quota', 'rate', 'limit', 'exhausted', 'exceeded', 'insufficient']):
                print(f"[INFO] Key #{idx} quota/rate limit reached, trying next key...")
                continue
            else:
                # For other errors, still try next key
                print(f"[INFO] Key #{idx} error, trying next key...")
                continue
    
    # All OpenAI keys failed
    print(f"[INFO] All OpenAI API keys failed or unavailable")
    return None


def generate_summary_with_gemini(title: str, content: str) -> Optional[str]:
    """
    Generate a 5-6 line summary using Google Gemini AI
    Automatically tries multiple API keys if one fails
    
    Args:
        title: Article title
        content: Article content to summarize (will be truncated to 3000 chars)
    
    Returns:
        str: Generated summary or None if all keys fail
    """
    
    # Check if genai is available
    if not GENAI_AVAILABLE:
        print("[WARN] google-generativeai not available, skipping Gemini")
        return None
    
    # Truncate content to reasonable length
    content_to_summarize = content[:3000] if len(content) > 3000 else content
    
    # Create the prompt
    prompt = f"""Summarize this news article in exactly 5-6 lines. 
    
Use a professional, neutral tone without bullet points, headings, or AI-related terminology.
Write it as editorial content that feels natural and human-written.

Title: {title}

Content: {content_to_summarize}

Summary:"""
    
    # Try each API key until one works
    for idx, api_key in enumerate(GEMINI_API_KEYS, 1):
        try:
            print(f"[GEMINI] Trying API key #{idx}...")
            
            # Configure Gemini with current API key
            genai.configure(api_key=api_key)
            
            # Try both model names (different APIs use different naming)
            model_names = ['gemini-1.5-flash-latest', 'gemini-1.5-flash', 'gemini-pro']
            
            for model_name in model_names:
                try:
                    model = genai.GenerativeModel(model_name)
                    
                    # Generate summary
                    response = model.generate_content(
                        prompt,
                        generation_config={
                            'temperature': 0.7,
                            'top_p': 0.9,
                            'top_k': 40,
                            'max_output_tokens': 200,
                        }
                    )
                    
                    # Extract the summary
                    if response and response.text:
                        summary = response.text.strip()
                        print(f"[SUCCESS] Generated summary with Gemini key #{idx} using model {model_name}")
                        print(f"[GEMINI] Summary preview: {summary[:100]}...")
                        return summary
                        
                except Exception as model_error:
                    # If model not found, try next model name
                    if '404' in str(model_error) or 'not found' in str(model_error).lower():
                        continue
                    else:
                        raise model_error
                
        except Exception as e:
            error_msg = str(e)
            print(f"[WARN] Gemini API key #{idx} failed: {error_msg[:100]}")
            
            # Check if it's a quota/rate limit error
            if any(keyword in error_msg.lower() for keyword in ['quota', 'rate', 'limit', 'exhausted', 'exceeded']):
                print(f"[INFO] Key #{idx} quota/rate limit reached, trying next key...")
                continue
            else:
                # For other errors, still try next key
                print(f"[INFO] Key #{idx} error, trying next key...")
                continue
    
    # All keys failed
    print(f"[ERROR] All {len(GEMINI_API_KEYS)} Gemini API keys failed")
    return None


def generate_summary_fallback(title: str, content: str) -> str:
    """
    Fallback summary generator using simple extraction with proper formatting
    Used when all AI API keys fail
    
    Args:
        title: Article title
        content: Article content
    
    Returns:
        str: Well-formatted extracted summary from content
    """
    import re
    
    print(f"[FALLBACK] Using local summarization with enhanced formatting")
    
    # Clean content first
    content = content.strip()
    
    # Extract sentences - improved regex to handle various punctuation
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', content)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 30 and not s.startswith('http')]
    
    # Select most important sentences (first 5-6 are usually most informative)
    summary_sentences = []
    
    if len(sentences) >= 3:
        # Take first sentence (lede - usually most important)
        summary_sentences.append(sentences[0])
        
        # Take 2nd and 3rd sentences (context)
        if len(sentences) > 1:
            summary_sentences.append(sentences[1])
        if len(sentences) > 2:
            summary_sentences.append(sentences[2])
        
        # Take one more sentence from middle for context
        mid = len(sentences) // 2
        if mid > 3 and mid < len(sentences):
            summary_sentences.append(sentences[mid])
        
        # Take one sentence near the end for conclusion
        if len(sentences) > 5:
            late_idx = min(len(sentences) - 2, len(sentences) - 1)
            if late_idx > 3 and late_idx < len(sentences):
                summary_sentences.append(sentences[late_idx])
    else:
        # For very short content, take all sentences
        summary_sentences = sentences[:6]
    
    # Create well-formatted summary with proper spacing and punctuation
    if summary_sentences:
        # Join sentences with proper spacing
        summary = ' '.join(summary_sentences[:6])
        
        # Ensure proper sentence endings
        if summary and not summary.endswith(('.', '!', '?')):
            summary += '.'
        
        # Format as a proper paragraph
        summary = summary.replace('..', '.').replace('  ', ' ').strip()
        
        print(f"[FALLBACK] Generated {len(summary_sentences)} sentence summary ({len(summary)} chars)")
        return summary
    
    # Absolute fallback - return first 500 chars of content
    fallback = content[:500].strip()
    if fallback and not fallback.endswith(('.', '!', '?')):
        # Find last sentence boundary
        last_period = max(fallback.rfind('.'), fallback.rfind('!'), fallback.rfind('?'))
        if last_period > 100:
            fallback = fallback[:last_period + 1]
        else:
            fallback += '...'
    
    print(f"[FALLBACK] Using truncated content ({len(fallback)} chars)")
    return fallback


def generate_summary(title: str, content: str) -> str:
    """
    Generate AI-powered summary with automatic failover:
    1. Try Gemini 1.5 Flash (all keys) - FIRST PREFERENCE
    2. Try OpenAI GPT-3.5-turbo (all keys) - FALLBACK
    3. Use local extraction method - LAST RESORT
    
    Args:
        title: Article title
        content: Article content to summarize
    
    Returns:
        str: Generated summary (always returns a summary)
    """
    print("[AI SUMMARY] Starting summarization with Gemini (PRIMARY)...")
    
    # Try Gemini first (primary - user's first preference)
    summary = generate_summary_with_gemini(title, content)
    if summary:
        return summary
    
    # Try OpenAI as fallback
    print("[AI SUMMARY] Gemini exhausted, falling back to OpenAI...")
    summary = generate_summary_with_openai(title, content)
    if summary:
        return summary
    
    # Last resort: use fallback extraction
    print("[AI SUMMARY] All AI services failed, using fallback extraction...")
    return generate_summary_fallback(title, content)


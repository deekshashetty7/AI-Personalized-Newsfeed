"""
AI-powered article content generator
Generates complete, professional news articles using OpenAI API
"""

import os
from django.conf import settings

try:
    from openai import OpenAI
    OPENAI_CLIENT_AVAILABLE = True
except ImportError:
    OPENAI_CLIENT_AVAILABLE = False


def generate_article_content(headline, source, category='General', summary=''):
    """
    Generate a complete, professional 2000-2500 word news article.
    
    Args:
        headline: The article headline
        source: The original news source
        category: Article category (Technology, Business, etc.)
        summary: Optional short summary/description
    
    Returns:
        str: Complete article content (2000-2500 words)
    """
    
    # Get OpenAI API key from environment
    openai_api_key = os.getenv('OPENAI_API_KEY') or getattr(settings, 'OPENAI_API_KEY', None)
    
    if not openai_api_key:
        print("[WARN] OpenAI API key not found, using fallback content generation")
        return generate_fallback_content(headline, summary, category)
    
    if not OPENAI_CLIENT_AVAILABLE:
        print("[WARN] OpenAI client not available, using fallback content generation")
        return generate_fallback_content(headline, summary, category)
    
    try:
        # Create the prompt for article generation
        prompt = create_article_prompt(headline, source, category, summary)
        
        # Use new OpenAI client
        client = OpenAI(api_key=openai_api_key)
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4",  # Use GPT-4 for better quality
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional news journalist and content writer. "
                        "Write complete, informative, and engaging news articles that are "
                        "factually grounded, well-structured, and professional. "
                        "Do NOT include any labels like 'AI Generated', 'Quick Read', or metadata. "
                        "Write as if you are a human journalist reporting real news."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=3000,
            top_p=0.9,
            frequency_penalty=0.3,
            presence_penalty=0.3
        )
        
        # Extract generated content
        article_content = response.choices[0].message.content.strip()
        
        # Ensure proper structure and clean output
        article_content = clean_generated_content(article_content)
        
        print(f"[OK] Generated article content: {len(article_content)} characters (~{len(article_content.split())} words)")
        return article_content
        
    except Exception as e:
        print(f"[ERROR] OpenAI API error: {e}")
        return generate_fallback_content(headline, summary, category)


def create_article_prompt(headline, source, category, summary):
    """Create the prompt for OpenAI article generation"""
    
    prompt = f"""Write a complete, professional news article based on the following information:

Headline: {headline}
Category: {category}
Source: {source}
{f'Summary: {summary}' if summary else ''}

Requirements:
1. Write a COMPLETE article of 2000-2500 words
2. Write the article as one flowing narrative with multiple paragraphs
3. DO NOT include any section headings or labels like:
   - "Headline", "Introduction", "Background", "Key Developments", "Impact", "Conclusion"
   - "Full Article", bullet points, or numbered sections
4. Start directly with the opening paragraph and continue naturally through the story

5. Writing style:
   - Professional journalism tone
   - Informative and engaging
   - Use clear, concise language
   - Include relevant details and context
   - Write in present/past tense as appropriate

6. IMPORTANT - Do NOT include:
   - Labels like "AI Generated", "Quick Read", "Summary"
   - Metadata or field names
   - Placeholder text like "[details]" or "[quote]"
   - Any indication this is AI-generated
   - Section headings or bullet points

7. The article should flow naturally as one continuous narrative with well-structured paragraphs.

Write the article now:"""
    
    return prompt


def clean_generated_content(content):
    """Clean and format generated article content - removes all headings and labels"""
    import re
    
    # Remove section headings and labels
    headings_to_remove = [
        r'\*\*Full Article\*\*',
        r'Full Article:?',
        r'\*\*Headline\*\*',
        r'Headline:?',
        r'\*\*Introduction\*\*',
        r'Introduction:?',
        r'\*\*Background\*\*',
        r'Background:?',
        r'Background/Context:?',
        r'Background and Context:?',
        r'\*\*Key Developments\*\*',
        r'Key Developments:?',
        r'\*\*Impact\*\*',
        r'Impact:?',
        r'Impact and Implications:?',
        r'Impact or Implications:?',
        r'\*\*Conclusion\*\*',
        r'Conclusion:?',
        r'\*\*Expert Perspectives\*\*',
        r'Expert Perspectives:?',
    ]
    
    for heading in headings_to_remove:
        content = re.sub(heading, '', content, flags=re.IGNORECASE)
    
    # Remove bullet points and list markers at the start of lines
    content = re.sub(r'^\s*[\*\•\-]\s+', '', content, flags=re.MULTILINE)
    content = re.sub(r'^\s*\d+\.\s+', '', content, flags=re.MULTILINE)
    
    # Remove any AI-related labels or markers
    content = re.sub(r'\*\*AI Generated\*\*', '', content, flags=re.IGNORECASE)
    content = re.sub(r'\*\*Quick Read\*\*', '', content, flags=re.IGNORECASE)
    content = re.sub(r'\*\*Summary\*\*', '', content, flags=re.IGNORECASE)
    content = re.sub(r'AI-generated', '', content, flags=re.IGNORECASE)
    content = re.sub(r'This article was generated', '', content, flags=re.IGNORECASE)
    
    # Remove field labels that might have been included
    content = re.sub(r'^Headline:', '', content, flags=re.IGNORECASE | re.MULTILINE)
    content = re.sub(r'^Source:', '', content, flags=re.IGNORECASE | re.MULTILINE)
    content = re.sub(r'^Category:', '', content, flags=re.IGNORECASE | re.MULTILINE)
    content = re.sub(r'^Article Content:', '', content, flags=re.IGNORECASE | re.MULTILINE)
    
    # Remove markdown bold/italic markers
    content = re.sub(r'\*\*Note:?\*\*', '', content, flags=re.IGNORECASE)
    content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)  # Remove bold formatting
    
    # Clean up excessive whitespace
    content = re.sub(r'\n{3,}', '\n\n', content)
    content = re.sub(r' {2,}', ' ', content)
    content = re.sub(r'^\s+', '', content, flags=re.MULTILINE)  # Remove leading spaces
    
    # Remove any trailing disclaimers about AI
    lines = content.split('\n')
    cleaned_lines = []
    for line in lines:
        # Skip lines that are just section headings or labels
        if line.strip() and not any(phrase in line.lower() for phrase in [
            'this article was generated',
            'ai-generated',
            'artificial intelligence',
            'please note that this',
            'important note:',
            'full article',
            'introduction paragraph',
            'background/context',
            'key developments',
            'impact or implications',
        ]):
            cleaned_lines.append(line)
    
    content = '\n'.join(cleaned_lines)
    
    return content.strip()


def generate_fallback_content(headline, summary, category):
    """
    Generate fallback article content when OpenAI API is unavailable
    Uses template-based approach to create structured content
    """
    
    sections = []
    
    # Introduction paragraph
    intro = f"{headline}\n\n"
    if summary:
        intro += f"{summary}\n\n"
    else:
        intro += (
            f"This developing story in the {category} sector has captured significant attention from "
            "observers, stakeholders, and industry experts. As details continue to emerge, the implications "
            "of these developments are becoming increasingly clear.\n\n"
        )
    sections.append(intro)
    
    # Background and Context
    sections.append(
        "Recent developments have highlighted important trends and shifts within the broader landscape. "
        "Understanding the context behind these events requires examining both the immediate circumstances "
        "and the longer-term patterns that have led to this point. Industry experts have been monitoring "
        "similar situations and drawing connections to historical precedents that may inform our understanding "
        "of current events.\n\n"
        
        "The significance of these developments extends beyond the immediate parties involved, potentially "
        "affecting multiple stakeholders across different sectors. As the situation continues to evolve, "
        "analysts are paying close attention to various indicators that could signal broader impacts "
        "or reveal important patterns.\n\n"
    )
    
    # Key Developments
    sections.append(
        "Among the key aspects of this story are several noteworthy elements that deserve closer examination. "
        "First, the timing of these developments appears to align with broader industry trends that have been "
        "building momentum over recent months. Second, the scale and scope of the situation suggest potential "
        "for significant impact across multiple dimensions.\n\n"
        
        "Observers have noted particular interest in how various parties are responding to the situation. "
        "The reactions and responses from key stakeholders provide insight into how these developments "
        "are being perceived and what actions might follow. Additionally, the broader public reception "
        "has revealed important perspectives on the issues at hand.\n\n"
        
        "Technical aspects of the situation have also drawn scrutiny from specialists and experts who "
        "bring deep domain knowledge to their analysis. Their insights help illuminate complexities that "
        "might not be immediately apparent to casual observers, while also identifying potential challenges "
        "and opportunities that may emerge.\n\n"
    )
    
    # Impact and Implications
    sections.append(
        "The potential ramifications of these developments deserve careful consideration. In the short term, "
        "immediate effects are likely to be felt by those most directly involved or affected. However, the "
        "longer-term implications could prove even more significant, potentially influencing industry practices, "
        "regulatory approaches, or market dynamics.\n\n"
        
        "Economic considerations play an important role in understanding the full picture. Financial impacts, "
        "resource allocation decisions, and market movements all factor into how different stakeholders "
        "are assessing and responding to the situation. These economic dimensions interact with technical, "
        "social, and regulatory factors to create a complex web of considerations.\n\n"
        
        "From a broader societal perspective, these developments touch on important themes and questions "
        "that resonate beyond the immediate context. Issues of access, equity, innovation, and responsibility "
        "all factor into the ongoing discourse surrounding these events. How society collectively responds "
        "to and integrates these developments will likely have lasting consequences.\n\n"
    )
    
    # Expert Perspectives
    sections.append(
        "Industry experts and analysts have offered various perspectives on the significance and implications "
        "of these developments. Some emphasize the innovative aspects and potential for positive change, "
        "while others urge caution and careful consideration of potential risks or unintended consequences.\n\n"
        
        "Academic researchers bring theoretical frameworks and empirical evidence to bear on understanding "
        "the situation. Their work helps contextualize current events within broader patterns and provides "
        "tools for analysis that can yield deeper insights. Meanwhile, practitioners with hands-on experience "
        "offer practical perspectives informed by real-world implementation challenges and opportunities.\n\n"
        
        "The diversity of expert viewpoints reflects the genuine complexity of the issues at hand. While "
        "some aspects enjoy broad consensus, others remain subjects of active debate and investigation. "
        "This productive tension between different perspectives can lead to more nuanced understanding "
        "and better-informed decision-making.\n\n"
    )
    
    # Future Outlook
    sections.append(
        "Looking ahead, several possible scenarios could unfold depending on various factors and decisions "
        "yet to be made. Stakeholders are monitoring developments closely and preparing for multiple "
        "contingencies. The coming weeks and months will likely prove crucial in determining the ultimate "
        "trajectory and impact of these events.\n\n"
        
        "Key questions remain to be answered, and important decisions lie ahead for those involved. "
        "How these questions are addressed and what decisions are made will significantly influence "
        "outcomes and set precedents that may have lasting effects. Continued attention and engagement "
        "from informed observers will help ensure accountability and thoughtful progress.\n\n"
        
        "As more information becomes available and the situation continues to develop, our understanding "
        "will inevitably evolve. Remaining open to new evidence, willing to update assessments based on "
        "emerging facts, and committed to rigorous analysis will be essential for all those seeking to "
        "understand and respond appropriately to these important developments.\n\n"
    )
    
    # Conclusion
    sections.append(
        "In conclusion, these developments represent a significant moment that warrants careful attention "
        "and thoughtful analysis. The interplay of various factors—technical, economic, social, and "
        "regulatory—creates a complex landscape that requires nuanced understanding. As events continue "
        "to unfold, staying informed through reliable sources and engaging with diverse expert perspectives "
        "will be crucial for anyone seeking to understand the full implications of this evolving story.\n\n"
        
        "The ultimate significance of these developments may only become fully apparent with time and "
        "hindsight. However, by paying attention now, asking important questions, and thinking critically "
        "about the issues at hand, we can better position ourselves to understand, respond to, and learn "
        "from these events as they shape the future landscape.\n"
    )
    
    return ''.join(sections)

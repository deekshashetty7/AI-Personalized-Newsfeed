'use client';

import { useEffect, useState, useRef } from 'react';
import { NewsArticle } from '@/types';
import { X, Calendar, User, Loader2 } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { interactionAPI, newsAPI } from '@/lib/api';

// Helper function to clean HTML and extract text content
const cleanHTMLContent = (html: string): string => {
  if (!html) return '';
  
  // Remove HTML tags but preserve line breaks
  let text = html
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/p>/gi, '\n\n')
    .replace(/<p[^>]*>/gi, '')
    .replace(/<img[^>]*>/gi, '')
    .replace(/<\/?[^>]+(>|$)/g, '')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'");
  
  // Remove image credits in parentheses
  text = text.replace(/\(Image credit:.*?\)/gi, '');
  
  // Remove tracking pixels and empty lines
  text = text.split('\n')
    .filter(line => !line.includes('tracking') && !line.includes('.png') && line.trim().length > 0)
    .join('\n');
  
  return text.trim();
};

interface ArticleModalProps {
  article: NewsArticle | null;
  isOpen: boolean;
  onClose: () => void;
}

export default function ArticleModal({ article, isOpen, onClose }: ArticleModalProps) {
  const [dwellStartTime, setDwellStartTime] = useState<number | null>(null);
  const dwellTimerRef = useRef<NodeJS.Timeout | null>(null);
  const [fullContent, setFullContent] = useState<string>('');
  const [loadingContent, setLoadingContent] = useState(false);
  const [contentError, setContentError] = useState<string>('');

  // Fetch full article content when modal opens or article changes
  useEffect(() => {
    if (isOpen && article && article.url) {
      setLoadingContent(true);
      setContentError('');
      setFullContent('');
      
      console.log('📰 Fetching full content for:', article.title, 'ID:', article._id);
      
      newsAPI.fetchFullContent(article.url, article.title)
        .then(response => {
          if (response.data.content && response.data.content.length > 100) {
            setFullContent(response.data.content);
            console.log('✅ Full content loaded:', response.data.content.length, 'characters', 'Method:', response.data.method);
            
            // Only show error if content is truly unavailable
            if (response.data.method === 'generated_explanation') {
              // Don't show error for generated content - it's still useful information
              setContentError('');
            }
          } else {
            setContentError('Limited content available. Summary shown above.');
          }
        })
        .catch(error => {
          console.error('❌ Error fetching full content:', error);
          const errorMsg = error.response?.data?.error || 'Could not load full article content';
          setContentError(errorMsg);
        })
        .finally(() => {
          setLoadingContent(false);
        });
    } else if (isOpen && article && !article.url) {
      // No URL available - clear content
      setFullContent('');
      setContentError('No article URL available');
    }
  }, [isOpen, article?._id, article?.url, article?.title]);

  // Dwell time tracking
  useEffect(() => {
    if (isOpen && article) {
      // Start tracking time when modal opens
      setDwellStartTime(Date.now());
      
      // Set up periodic tracking (every 10 seconds while viewing)
      dwellTimerRef.current = setInterval(() => {
        if (dwellStartTime) {
          const dwellTime = Math.floor((Date.now() - dwellStartTime) / 1000);
          // Send intermediate dwell time tracking
          if (dwellTime > 0 && dwellTime % 10 === 0) {
            interactionAPI.create({ 
              article_id: article._id, 
              action: 'read',
              dwell_time: dwellTime 
            }).catch(err => console.error('Failed to track dwell time:', err));
          }
        }
      }, 10000); // Track every 10 seconds
    }
    
    return () => {
      // When modal closes, send final dwell time
      if (dwellStartTime && article) {
        const finalDwellTime = Math.floor((Date.now() - dwellStartTime) / 1000);
        if (finalDwellTime > 0) {
          interactionAPI.create({ 
            article_id: article._id, 
            action: 'read',
            dwell_time: finalDwellTime 
          }).catch(err => console.error('Failed to save final dwell time:', err));
        }
      }
      
      // Clear interval
      if (dwellTimerRef.current) {
        clearInterval(dwellTimerRef.current);
        dwellTimerRef.current = null;
      }
      
      setDwellStartTime(null);
    };
  }, [isOpen, article, dwellStartTime]);

  // Close modal on ESC key
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    
    if (isOpen) {
      window.addEventListener('keydown', handleEsc);
      document.body.style.overflow = 'hidden';
    }
    
    return () => {
      window.removeEventListener('keydown', handleEsc);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen || !article) return null;

  // Clean the content and summary
  const cleanSummary = cleanHTMLContent(article.summary || '');
  const cleanContent = cleanHTMLContent(article.content || '');
  const hasStoredContent = cleanContent && cleanContent !== cleanSummary;
  
  // Use fetched full content if available, otherwise fall back to stored content
  const displayContent = fullContent || cleanContent || cleanSummary;

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fadeIn"
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden animate-slideUp"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between z-10">
          <div className="flex items-center gap-3">
            <span className="inline-block bg-gradient-to-r from-primary to-secondary text-white text-xs font-bold px-3 py-1.5 rounded-full shadow-sm">
              {article.category}
            </span>
          </div>
          
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors duration-200"
            aria-label="Close modal"
          >
            <X className="w-5 h-5 text-gray-600" />
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto max-h-[calc(90vh-80px)] px-6 py-6">
          {/* Image */}
          {article.image_url && (
            <div className="relative w-full h-64 md:h-96 rounded-xl overflow-hidden mb-6">
              <img
                src={article.image_url}
                alt={article.title}
                className="w-full h-full object-cover"
                onError={(e) => {
                  const target = e.target as HTMLImageElement;
                  target.src = 'https://via.placeholder.com/800x400?text=News+Image';
                }}
              />
            </div>
          )}

          {/* Title */}
          <h1 className="text-3xl md:text-4xl font-bold text-text mb-4 leading-tight">
            {article.title}
          </h1>

          {/* Meta Information */}
          <div className="flex flex-wrap items-center gap-4 text-sm text-text-secondary mb-6 pb-6 border-b border-gray-200">
            {(article.author || article.source_id) && !article.source?.toLowerCase().includes('reddit') && (
              <div className="flex items-center gap-2">
                <User className="w-4 h-4" />
                <span className="font-medium">
                  {article.author || article.source_id}
                </span>
              </div>
            )}
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4" />
              <span>
                {formatDistanceToNow(new Date(article.publish_time), { addSuffix: true })}
              </span>
            </div>
          </div>

          {/* Summary */}
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-text mb-4">Article Content</h2>
            <div className="text-text-secondary text-lg leading-relaxed space-y-4">
              {cleanSummary && cleanSummary.split('\n').map((paragraph, idx) => (
                paragraph.trim() && (
                  <p key={`summary-${idx}`} className="mb-4">
                    {paragraph}
                  </p>
                )
              ))}
            </div>
          </div>

          {/* Loading Full Content */}
          {loadingContent && (
            <div className="mb-6 pt-6 border-t border-gray-200">
              <div className="flex items-center justify-center gap-3 py-8 text-primary">
                <Loader2 className="w-6 h-6 animate-spin" />
                <span className="text-lg font-medium">Loading full article content...</span>
              </div>
            </div>
          )}

          {/* Full Content - Always show if we have any content */}
          {!loadingContent && displayContent && (
            <div className="mb-6 pt-6 border-t border-gray-200">
              <div className="prose prose-lg max-w-none text-text-secondary leading-relaxed">
                {displayContent.split('\n').map((paragraph, idx) => {
                  const trimmedParagraph = paragraph.trim();
                  
                  if (!trimmedParagraph) return null;
                  
                  // Handle markdown headers
                  if (trimmedParagraph.startsWith('# ')) {
                    return <h1 key={`content-${idx}`} className="text-3xl font-bold text-gray-900 mt-8 mb-4">{trimmedParagraph.substring(2)}</h1>;
                  }
                  if (trimmedParagraph.startsWith('## ')) {
                    return <h2 key={`content-${idx}`} className="text-2xl font-bold text-gray-800 mt-6 mb-3">{trimmedParagraph.substring(3)}</h2>;
                  }
                  if (trimmedParagraph.startsWith('### ')) {
                    return <h3 key={`content-${idx}`} className="text-xl font-semibold text-gray-800 mt-5 mb-2">{trimmedParagraph.substring(4)}</h3>;
                  }
                  
                  // Handle bold text with **
                  if (trimmedParagraph.includes('**')) {
                    const parts = trimmedParagraph.split('**');
                    return (
                      <p key={`content-${idx}`} className="mb-4 text-gray-700 leading-relaxed">
                        {parts.map((part, i) => 
                          i % 2 === 0 ? part : <strong key={i} className="font-semibold text-gray-900">{part}</strong>
                        )}
                      </p>
                    );
                  }
                  
                  // Handle italic text with *
                  if (trimmedParagraph.includes('*') && !trimmedParagraph.startsWith('*')) {
                    const parts = trimmedParagraph.split('*');
                    return (
                      <p key={`content-${idx}`} className="mb-4 text-gray-700 leading-relaxed">
                        {parts.map((part, i) => 
                          i % 2 === 0 ? part : <em key={i} className="italic">{part}</em>
                        )}
                      </p>
                    );
                  }
                  
                  // Handle horizontal rules
                  if (trimmedParagraph === '---') {
                    return <hr key={`content-${idx}`} className="my-6 border-gray-300" />;
                  }
                  
                  // Regular paragraphs
                  return (
                    <p key={`content-${idx}`} className="mb-4 text-gray-700 leading-relaxed text-justify">
                      {trimmedParagraph}
                    </p>
                  );
                })}
              </div>
            </div>
          )}

          {/* Article Metadata */}
          <div className="mt-8 pt-6 border-t border-gray-200">
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-6">
              <div className="text-sm text-gray-600 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-semibold">Category:</span>
                  <span className="bg-white px-3 py-1 rounded-full text-xs font-medium">{article.category}</span>
                </div>
                {article.source_id && !article.source?.toLowerCase().includes('reddit') && (
                  <div className="flex items-center justify-between">
                    <span className="font-semibold">Source:</span>
                    <span className="text-gray-700">{article.source_id}</span>
                  </div>
                )}
                {article.author && (
                  <div className="flex items-center justify-between">
                    <span className="font-semibold">Author:</span>
                    <span className="text-gray-700">{article.author}</span>
                  </div>
                )}
                <div className="flex items-center justify-between">
                  <span className="font-semibold">Published:</span>
                  <span className="text-gray-700">
                    {formatDistanceToNow(new Date(article.publish_time), { addSuffix: true })}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

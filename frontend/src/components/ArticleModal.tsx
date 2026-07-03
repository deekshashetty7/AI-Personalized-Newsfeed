'use client';

import { useEffect, useState, useRef } from 'react';
import { NewsArticle } from '@/types';
import { X, Calendar, User, Loader2 } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { interactionAPI, newsAPI } from '@/lib/api';

const cleanHTMLContent = (html: string): string => {
  if (!html) return '';

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

  text = text.replace(/\(Image credit:.*?\)/gi, '');
  text = text.split('\n')
    .filter(line => !line.includes('tracking') && !line.includes('.png') && line.trim().length > 0)
    .join('\n');

  return text.trim();
};

const pickBestContent = (...candidates: string[]): string => {
  const cleaned = candidates
    .map(cleanHTMLContent)
    .filter(Boolean);

  if (!cleaned.length) return '';
  return cleaned.sort((a, b) => b.length - a.length)[0];
};

const renderParagraph = (paragraph: string, idx: number) => {
  const trimmedParagraph = paragraph.trim();
  if (!trimmedParagraph) return null;

  if (trimmedParagraph.startsWith('# ')) {
    return (
      <h2 key={`content-${idx}`} className="text-2xl font-bold text-gray-900 mt-8 mb-4">
        {trimmedParagraph.substring(2)}
      </h2>
    );
  }
  if (trimmedParagraph.startsWith('## ')) {
    return (
      <h3 key={`content-${idx}`} className="text-xl font-bold text-gray-800 mt-6 mb-3">
        {trimmedParagraph.substring(3)}
      </h3>
    );
  }
  if (trimmedParagraph.startsWith('### ')) {
    return (
      <h4 key={`content-${idx}`} className="text-lg font-semibold text-gray-800 mt-5 mb-2">
        {trimmedParagraph.substring(4)}
      </h4>
    );
  }
  if (trimmedParagraph.includes('**')) {
    const parts = trimmedParagraph.split('**');
    return (
      <p key={`content-${idx}`} className="mb-4 text-gray-700 leading-relaxed text-justify">
        {parts.map((part, i) =>
          i % 2 === 0 ? part : <strong key={i} className="font-semibold text-gray-900">{part}</strong>
        )}
      </p>
    );
  }
  if (trimmedParagraph === '---') {
    return <hr key={`content-${idx}`} className="my-6 border-gray-300" />;
  }

  return (
    <p key={`content-${idx}`} className="mb-4 text-gray-700 leading-relaxed text-justify">
      {trimmedParagraph}
    </p>
  );
};

interface ArticleModalProps {
  article: NewsArticle | null;
  isOpen: boolean;
  onClose: () => void;
}

export default function ArticleModal({ article, isOpen, onClose }: ArticleModalProps) {
  const [dwellStartTime, setDwellStartTime] = useState<number | null>(null);
  const dwellTimerRef = useRef<NodeJS.Timeout | null>(null);
  const [articleBody, setArticleBody] = useState('');
  const [loadingContent, setLoadingContent] = useState(false);

  useEffect(() => {
    if (!isOpen || !article) {
      setArticleBody('');
      setLoadingContent(false);
      return;
    }

    let cancelled = false;
    setLoadingContent(true);
    setArticleBody(pickBestContent(article.content || '', article.summary || ''));

    const loadFullArticle = async () => {
      const candidates: string[] = [article.content || '', article.summary || ''];

      try {
        const detailResponse = await newsAPI.getArticle(article._id);
        candidates.push(detailResponse.data.content || '', detailResponse.data.summary || '');
      } catch {
        // Use existing article data if detail fetch fails
      }

      if (article.url) {
        try {
          const contentResponse = await newsAPI.fetchFullContent(article.url, article.title);
          if (contentResponse.data.content) {
            candidates.push(contentResponse.data.content);
          }
        } catch {
          // Keep database content when content expansion fails
        }
      }

      if (!cancelled) {
        const bestContent = pickBestContent(...candidates);
        setArticleBody(bestContent || 'Full article content is not available.');
        setLoadingContent(false);
      }
    };

    loadFullArticle();

    return () => {
      cancelled = true;
    };
  }, [isOpen, article?._id, article?.url, article?.title, article?.content, article?.summary]);

  useEffect(() => {
    if (isOpen && article) {
      setDwellStartTime(Date.now());

      dwellTimerRef.current = setInterval(() => {
        if (dwellStartTime) {
          const dwellTime = Math.floor((Date.now() - dwellStartTime) / 1000);
          if (dwellTime > 0 && dwellTime % 10 === 0) {
            interactionAPI.create({
              article_id: article._id,
              action: 'read',
              dwell_time: dwellTime
            }).catch(err => console.error('Failed to track dwell time:', err));
          }
        }
      }, 10000);
    }

    return () => {
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

      if (dwellTimerRef.current) {
        clearInterval(dwellTimerRef.current);
        dwellTimerRef.current = null;
      }

      setDwellStartTime(null);
    };
  }, [isOpen, article, dwellStartTime]);

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

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fadeIn"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden animate-slideUp"
        onClick={(e) => e.stopPropagation()}
      >
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

        <div className="overflow-y-auto max-h-[calc(90vh-80px)] px-6 py-6">
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

          <h1 className="text-3xl md:text-4xl font-bold text-text mb-4 leading-tight">
            {article.title}
          </h1>

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

          {loadingContent && !articleBody && (
            <div className="mb-6">
              <div className="flex items-center justify-center gap-3 py-8 text-primary">
                <Loader2 className="w-6 h-6 animate-spin" />
                <span className="text-lg font-medium">Loading full article...</span>
              </div>
            </div>
          )}

          <div className="prose prose-lg max-w-none text-text-secondary leading-relaxed">
            {articleBody.split('\n').map((paragraph, idx) => renderParagraph(paragraph, idx))}
          </div>

          {loadingContent && articleBody && (
            <div className="mt-4 flex items-center gap-2 text-sm text-primary">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Loading more detail...</span>
            </div>
          )}

          <div className="mt-8 pt-6 border-t border-gray-200">
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-6">
              <div className="text-sm text-gray-600 space-y-2">
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

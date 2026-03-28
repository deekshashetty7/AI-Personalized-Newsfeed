'use client';

import { useState, useEffect } from 'react';
import Image from 'next/image';
import { NewsArticle } from '@/types';
import { formatDistanceToNow } from 'date-fns';
import { ThumbsUp, ThumbsDown, MessageCircle, Share2, Bookmark, X, Sparkles, Loader2 } from 'lucide-react';
import CommentSection from './CommentSection';
import { useAuth } from '@/contexts/AuthContext';
import { interactionAPI } from '@/lib/api';

interface NewsCardProps {
  article: NewsArticle;
  onInteraction?: (articleId: string, action: string, commentText?: string) => void;
  showActions?: boolean;
  onReadMore?: (article: NewsArticle) => void;
}

export default function NewsCard({ article, onInteraction, showActions = true, onReadMore }: NewsCardProps) {
  const { user } = useAuth();
  const [liked, setLiked] = useState(article.is_liked || false);
  const [disliked, setDisliked] = useState(article.is_disliked || false);
  const [bookmarked, setBookmarked] = useState(article.is_saved || false);
  const [showCommentsModal, setShowCommentsModal] = useState(false);
  const [imageError, setImageError] = useState(false);
  const [aiSnapshot, setAiSnapshot] = useState<string | null>(null);
  const [loadingSnapshot, setLoadingSnapshot] = useState(false);
  const [snapshotError, setSnapshotError] = useState<string | null>(null);
  const [showSnapshotModal, setShowSnapshotModal] = useState(false);
  const [isProcessingInteraction, setIsProcessingInteraction] = useState(false);

  // Update states when article prop changes (for state restoration)
  useEffect(() => {
    setLiked(article.is_liked || false);
    setDisliked(article.is_disliked || false);
    setBookmarked(article.is_saved || false);
    // Reset AI snapshot when article changes
    setAiSnapshot(null);
    setSnapshotError(null);
  }, [article._id, article.is_liked, article.is_disliked, article.is_saved]);

  // Generate a unique gradient based on article title
  const generateGradient = () => {
    const colors = [
      ['from-blue-400', 'to-blue-600'],
      ['from-purple-400', 'to-purple-600'],
      ['from-green-400', 'to-green-600'],
      ['from-red-400', 'to-red-600'],
      ['from-yellow-400', 'to-yellow-600'],
      ['from-pink-400', 'to-pink-600'],
      ['from-indigo-400', 'to-indigo-600'],
      ['from-teal-400', 'to-teal-600'],
    ];
    const hash = article.title.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
    const [from, to] = colors[hash % colors.length];
    return `bg-gradient-to-br ${from} ${to}`;
  };

  const getInitial = () => {
    return article.title.charAt(0).toUpperCase();
  };

  const requireAuth = (actionName: string) => {
    if (!user) {
      alert(`Please log in to ${actionName}`);
      return false;
    }
    return true;
  };

  const handleAiSnapshot = async (e: React.MouseEvent) => {
    e.stopPropagation();
    
    if (!requireAuth('use AI Snapshot')) return;
    
    // Always generate fresh snapshot - don't use cached version
    // This ensures each article gets its unique summary
    setLoadingSnapshot(true);
    setSnapshotError(null);
    setAiSnapshot(null); // Clear previous snapshot
    setShowSnapshotModal(true);
    
    try {
      console.log('Generating AI snapshot for article:', article._id);
      const response = await interactionAPI.generateAiSnapshot(article._id);
      console.log('Received summary:', response.data.summary.substring(0, 100));
      
      // Check if there's a warning (e.g., OpenAI quota exceeded)
      if (response.data.warning) {
        console.warn('AI Snapshot warning:', response.data.warning);
        setSnapshotError(response.data.warning);
      }
      
      setAiSnapshot(response.data.summary);
    } catch (error: any) {
      console.error('AI Snapshot error:', error);
      const errorMessage = error.response?.data?.error || 'Failed to generate AI summary. Please try again.';
      setSnapshotError(errorMessage);
    } finally {
      setLoadingSnapshot(false);
    }
  };

  const handleAction = (action: string) => {
    if (!requireAuth(`use this feature`)) return;
    
    // Prevent race conditions on rapid clicks
    if (isProcessingInteraction) return;
    
    setIsProcessingInteraction(true);
    
    if (onInteraction) {
      // Optimistic UI update with mutual exclusivity
      if (action === 'like') {
        const newLikedState = !liked;
        setLiked(newLikedState);
        if (newLikedState) {
          setDisliked(false); // Enforce mutual exclusivity
        }
      } else if (action === 'dislike') {
        const newDislikedState = !disliked;
        setDisliked(newDislikedState);
        if (newDislikedState) {
          setLiked(false); // Enforce mutual exclusivity
        }
      } else if (action === 'save') {
        setBookmarked(!bookmarked);
      }
      
      // Call backend
      onInteraction(article._id, action);
      
      // Allow next interaction after a short delay
      setTimeout(() => {
        setIsProcessingInteraction(false);
      }, 300);
    } else {
      setIsProcessingInteraction(false);
    }
  };

  const handleToggleComments = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!requireAuth('comment')) return;
    setShowCommentsModal(!showCommentsModal);
  };

  const handleAddComment = async (commentText: string) => {
    if (!requireAuth('comment')) return;
    if (commentText && commentText.trim() && onInteraction) {
      await onInteraction(article._id, 'comment', commentText);
    }
  };

  const handleCloseModal = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      setShowCommentsModal(false);
    }
  };

  const handleShare = async (e: React.MouseEvent) => {
    e.stopPropagation();
    
    if (!requireAuth('share')) return;
    
    if (onInteraction) {
      onInteraction(article._id, 'share');
    }

    const shareData = {
      title: article.title,
      text: article.summary || article.title,
      url: article.url || window.location.href,
    };

    try {
      if (navigator.share) {
        await navigator.share(shareData);
      } else {
        await navigator.clipboard.writeText(article.url || window.location.href);
        alert('Link copied to clipboard!');
      }
    } catch (err) {
      console.error('Error sharing:', err);
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-md hover:shadow-2xl transition-shadow duration-300 overflow-hidden group cursor-pointer">
      {article.image_url && article.image_url.trim() !== '' && !imageError ? (
        <div 
          className="relative w-full h-56 overflow-hidden"
          onClick={() => onReadMore && onReadMore(article)}
        >
          <Image
            src={article.image_url}
            alt={article.title}
            fill
            className="object-cover group-hover:scale-105 transition-transform duration-500"
            style={{
              objectPosition: 'center'
            }}
            onError={() => {
              console.error('Image failed to load:', article.image_url);
              setImageError(true);
            }}
          />
          
          <div className="absolute top-3 left-3 bg-blue-600 text-white px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider shadow-lg">
              {article.category}
          </div>
        </div>
      ) : (
        <div 
          className={`relative w-full h-56 ${generateGradient()} flex items-center justify-center cursor-pointer group-hover:opacity-90 transition-opacity duration-300`}
          onClick={() => onReadMore && onReadMore(article)}
        >
          <div className="text-white text-8xl font-bold opacity-30">
            {getInitial()}
          </div>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-white text-center px-4">
              <div className="text-5xl mb-2">📰</div>
              <div className="text-sm font-semibold opacity-90 line-clamp-2">
                {article.title}
              </div>
            </div>
          </div>
          <div className="absolute top-3 left-3 bg-white bg-opacity-20 backdrop-blur-sm text-white px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider shadow-lg">
              {article.category}
          </div>
        </div>
      )}

      <div className="p-5">
        <h2 
          onClick={() => onReadMore && onReadMore(article)}
          className="text-xl font-bold text-gray-900 mb-2 line-clamp-2 leading-tight hover:text-blue-600 cursor-pointer transition-colors"
        >
            {article.title}
        </h2>

        <div className="text-xs text-gray-500 mb-3 space-y-1">
          <div className="flex items-center gap-1">
            <span className="font-semibold">Source:</span>
            <span>
              {(() => {
                const source = article.source || article.source_id || 'Unknown Source';
                const author = article.author;
                
                // For Reddit sources, show only "Reddit"
                if (source.toLowerCase().includes('reddit')) {
                  return 'Reddit';
                }
                
                const hasValidAuthor = author && 
                  author.trim() !== '' && 
                  author !== 'Unknown' && 
                  author !== 'null' && 
                  !source.toLowerCase().includes(author.toLowerCase());
                
                if (hasValidAuthor) {
                  return `${source} • by ${article.author}`;
                }
                
                return source;
              })()}
            </span>
          </div>
          <div>
            {(() => {
              try {
                const publishedAt = article.publish_time || article.published_at;
                if (!publishedAt) return 'Just now';
                
                const date = new Date(publishedAt);
                if (isNaN(date.getTime())) return 'Just now';
                
                const timeAgo = formatDistanceToNow(date, { addSuffix: true });
                // Remove "about" from the time string
                return timeAgo.replace('about ', '');
              } catch (error) {
                return 'Just now';
              }
            })()}
          </div>
        </div>

        <p className="text-gray-600 text-sm mb-3 line-clamp-2 leading-relaxed">
          {article.summary}
        </p>

        {/* AI Snapshot Button - Always visible, above interaction buttons */}
        {showActions && (
          <div className="mb-3">
            <button
              onClick={handleAiSnapshot}
              disabled={loadingSnapshot}
              className={`w-full py-2.5 px-4 rounded-xl font-medium text-sm transition-all duration-300 flex items-center justify-center gap-2 ${
                loadingSnapshot
                  ? 'bg-blue-300 text-blue-800 cursor-wait'
                  : 'bg-blue-500 text-white hover:bg-blue-600 hover:shadow-md'
              }`}
              title={!user ? 'Please log in to use AI Snapshot' : 'Generate AI-powered summary'}
            >
              {loadingSnapshot ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Generating AI Summary...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>AI Snapshot</span>
                </>
              )}
            </button>
          </div>
        )}

        {showActions && (
          <div className="flex items-center justify-between gap-0.5 border-t border-gray-100 pt-2">
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleAction('like');
              }}
              disabled={!user}
              className={`flex items-center justify-center px-2 py-2 rounded-lg transition-all duration-200 flex-1 ${
                !user
                  ? 'text-gray-300 cursor-not-allowed'
                  : liked 
                  ? 'bg-green-100 text-green-600' 
                  : 'text-gray-600 hover:bg-green-50 hover:text-green-600'
              }`}
              title={!user ? 'Please log in to like' : 'Like'}
            >
              <ThumbsUp className={`w-4 h-4 ${liked ? 'fill-current' : ''}`} />
            </button>
            
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleAction('dislike');
              }}
              disabled={!user}
              className={`flex items-center justify-center px-2 py-2 rounded-lg transition-all duration-200 flex-1 ${
                !user
                  ? 'text-gray-300 cursor-not-allowed'
                  : disliked 
                  ? 'bg-red-100 text-red-600' 
                  : 'text-gray-600 hover:bg-red-50 hover:text-red-600'
              }`}
              title={!user ? 'Please log in to dislike' : 'Dislike'}
            >
              <ThumbsDown className={`w-4 h-4 ${disliked ? 'fill-current' : ''}`} />
            </button>

            <button
              onClick={handleToggleComments}
              disabled={!user}
              className={`flex items-center justify-center px-2 py-2 rounded-lg transition-all duration-200 flex-1 ${
                !user
                  ? 'text-gray-300 cursor-not-allowed'
                  : showCommentsModal 
                  ? 'bg-blue-100 text-blue-600' 
                  : 'text-gray-600 hover:bg-blue-50 hover:text-blue-600'
              }`}
              title={!user ? 'Please log in to comment' : 'Comment'}
            >
              <MessageCircle className={`w-4 h-4 ${showCommentsModal ? 'fill-current' : ''}`} />
            </button>

            <button
              onClick={handleShare}
              disabled={!user}
              className={`flex items-center justify-center px-2 py-2 rounded-lg transition-all duration-200 flex-1 ${
                !user
                  ? 'text-gray-300 cursor-not-allowed'
                  : 'text-gray-600 hover:bg-purple-50 hover:text-purple-600'
              }`}
              title={!user ? 'Please log in to share' : 'Share'}
            >
              <Share2 className="w-4 h-4" />
            </button>
            
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleAction('save');
              }}
              disabled={!user}
              className={`flex items-center justify-center px-2 py-2 rounded-lg transition-all duration-200 flex-1 ${
                !user
                  ? 'text-gray-300 cursor-not-allowed'
                  : bookmarked 
                  ? 'bg-yellow-100 text-yellow-600' 
                  : 'text-gray-600 hover:bg-yellow-50 hover:text-yellow-600'
              }`}
              title={!user ? 'Please log in to save' : 'Save'}
            >
              <Bookmark className={`w-4 h-4 ${bookmarked ? 'fill-current' : ''}`} />
            </button>
          </div>
        )}
      </div>

      {/* Comments Modal */}
      {showCommentsModal && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4"
          onClick={handleCloseModal}
        >
          <div 
            className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[85vh] overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">{article.title}</h2>
                <p className="text-sm text-gray-500 mt-1">{article.source}</p>
              </div>
              <button
                onClick={() => setShowCommentsModal(false)}
                className="p-2 hover:bg-gray-100 rounded-full transition-colors"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="overflow-y-auto max-h-[calc(85vh-80px)] p-6">
              <CommentSection articleId={article._id} onAddComment={handleAddComment} />
            </div>
          </div>
        </div>
      )}

      {/* AI Snapshot Modal */}
      {showSnapshotModal && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4 animate-fadeIn"
          onClick={() => setShowSnapshotModal(false)}
        >
          <div 
            className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[85vh] overflow-hidden animate-slideUp"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between p-5 border-b border-gray-200 bg-gradient-to-r from-purple-50 to-pink-50">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg">
                  <Sparkles className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-gray-900">AI-Powered Summary</h2>
                </div>
              </div>
              <button
                onClick={() => setShowSnapshotModal(false)}
                className="p-2 hover:bg-white rounded-full transition-colors"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="overflow-y-auto max-h-[calc(85vh-100px)] p-6">
              {/* Article Info */}
              <div className="mb-4 pb-4 border-b border-gray-100">
                <h3 className="text-base font-semibold text-gray-900 mb-1">{article.title}</h3>
                <p className="text-xs text-gray-500">{article.source}</p>
              </div>

              {/* Loading State */}
              {loadingSnapshot && (
                <div className="flex flex-col items-center justify-center py-12">
                  <Loader2 className="w-12 h-12 text-purple-500 animate-spin mb-4" />
                  <p className="text-gray-600 font-medium">Generating AI Summary...</p>
                  <p className="text-sm text-gray-400 mt-1">This may take a few seconds</p>
                </div>
              )}

              {/* Error State */}
              {snapshotError && !loadingSnapshot && (
                <div className="py-8 px-6 bg-red-50 rounded-xl border border-red-200">
                  <div className="flex items-start gap-3">
                    <div className="p-2 bg-red-100 rounded-lg flex-shrink-0">
                      <X className="w-5 h-5 text-red-600" />
                    </div>
                    <div>
                      <h4 className="font-semibold text-red-900 mb-1">Error</h4>
                      <p className="text-sm text-red-700">{snapshotError}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* AI Summary Content */}
              {aiSnapshot && !loadingSnapshot && (
                <div className="prose prose-sm max-w-none">
                  <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl p-6 border border-purple-100">
                    <p className="text-gray-800 leading-relaxed text-base whitespace-pre-wrap">
                      {aiSnapshot}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

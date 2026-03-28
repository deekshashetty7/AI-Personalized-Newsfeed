'use client';

import { useState, useEffect } from 'react';
import { interactionAPI, authAPI } from '@/lib/api';
import Image from 'next/image';

interface Comment {
  _id: string;
  user_id: string;
  username: string;
  profile_photo?: string | null;
  comment_text: string;
  sentiment: number;
  timestamp: string;
}

interface CommentSectionProps {
  articleId: string;
  onAddComment?: (commentText: string) => void;
}

export default function CommentSection({ articleId, onAddComment }: CommentSectionProps) {
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newComment, setNewComment] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [currentUserPhoto, setCurrentUserPhoto] = useState<string | null>(null);

  useEffect(() => {
    fetchComments();
    fetchCurrentUserProfile();
  }, [articleId]);

  const fetchCurrentUserProfile = async () => {
    try {
      const response = await authAPI.getProfile();
      setCurrentUserPhoto(response.data.profile_photo);
    } catch (err) {
      console.error('Error fetching user profile:', err);
    }
  };

  const fetchComments = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await interactionAPI.getArticleComments(articleId);
      setComments(response.data);
    } catch (err: any) {
      console.error('Error fetching comments:', err);
      setError('Failed to load comments');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMs / 3600000);
      const diffDays = Math.floor(diffMs / 86400000);

      if (diffMins < 1) return 'just now';
      if (diffMins < 60) return `${diffMins}m ago`;
      if (diffHours < 24) return `${diffHours}h ago`;
      if (diffDays < 7) return `${diffDays}d ago`;
      
      return date.toLocaleDateString();
    } catch {
      return 'recently';
    }
  };

  const handleSubmitComment = async () => {
    if (!newComment.trim()) return;
    
    setSubmitting(true);
    try {
      if (onAddComment) {
        await onAddComment(newComment);
        setNewComment('');
        await fetchComments();
      }
    } catch (err) {
      console.error('Error submitting comment:', err);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="mt-4 p-4 bg-gray-50 rounded-lg">
        <p className="text-gray-500 text-sm">Loading comments...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mt-4 p-4 bg-red-50 rounded-lg">
        <p className="text-red-500 text-sm">{error}</p>
      </div>
    );
  }

  return (
    <div className="mt-4 border-t border-gray-200 pt-4">
      {/* Comment Input - LinkedIn/Facebook style */}
      <div className="mb-6">
        <div className="flex gap-3">
          <div className="flex-shrink-0">
            {currentUserPhoto ? (
              <div className="w-10 h-10 rounded-full overflow-hidden shadow-sm">
                <Image
                  src={currentUserPhoto}
                  alt="Your profile"
                  width={40}
                  height={40}
                  className="object-cover w-full h-full"
                />
              </div>
            ) : (
              <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center shadow-sm">
                <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                </svg>
              </div>
            )}
          </div>
          <div className="flex-1">
            <div className="relative">
              <textarea
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                placeholder="Add a comment..."
                className="w-full p-3 pr-20 border border-gray-300 rounded-2xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none text-sm placeholder-gray-400 transition-all"
                rows={1}
                disabled={submitting}
                onFocus={(e) => {
                  e.target.rows = 3;
                }}
                onBlur={(e) => {
                  if (!newComment) e.target.rows = 1;
                }}
              />
              {newComment.trim() && (
                <button
                  onClick={handleSubmitComment}
                  disabled={submitting}
                  className="absolute right-2 bottom-2 px-4 py-1.5 bg-blue-600 text-white rounded-full text-sm font-medium hover:bg-blue-700 disabled:bg-blue-300 disabled:cursor-not-allowed transition-colors shadow-sm"
                >
                  {submitting ? '...' : 'Post'}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Comments Header */}
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-gray-700">
          {comments.length === 0 ? 'No comments yet' : `${comments.length} ${comments.length === 1 ? 'comment' : 'comments'}`}
        </h3>
      </div>

      {/* Comments List - Twitter/Instagram style */}
      {comments.length === 0 ? (
        <div className="py-8 text-center">
          <p className="text-gray-400 text-sm">Be the first to share your thoughts</p>
        </div>
      ) : (
        <div className="space-y-4 max-h-[500px] overflow-y-auto pr-2">
          {comments.map((comment) => (
            <div key={comment._id} className="flex gap-3 group">
              <div className="flex-shrink-0">
                {comment.profile_photo ? (
                  <div className="w-9 h-9 rounded-full overflow-hidden shadow-sm">
                    <Image
                      src={comment.profile_photo}
                      alt={comment.username}
                      width={36}
                      height={36}
                      className="object-cover w-full h-full"
                    />
                  </div>
                ) : (
                  <div className="w-9 h-9 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center shadow-sm">
                    <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                    </svg>
                  </div>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="bg-gray-50 rounded-2xl px-4 py-3 hover:bg-gray-100 transition-colors">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-semibold text-gray-900">
                      {comment.username}
                    </span>
                    <span className="text-xs text-gray-500">
                      · {formatDate(comment.timestamp)}
                    </span>
                  </div>
                  <p className="text-sm text-gray-800 leading-relaxed break-words">
                    {comment.comment_text}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

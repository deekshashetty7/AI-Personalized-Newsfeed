'use client';

import { useEffect, useState } from 'react';
import { Brain, BookOpen, TrendingUp, Clock } from 'lucide-react';
import { knowledgeBoxAPI } from '@/lib/api';

interface KnowledgeTopic {
  topic: string;
  article_count: number;
  total_time_spent: number;
  last_read: string;
  importance_score: number;
  subtopics: string[];
  key_entities: string[];
}

interface KnowledgeBoxProps {
  userId?: string;
}

export default function KnowledgeBox({ userId }: KnowledgeBoxProps) {
  const [topics, setTopics] = useState<KnowledgeTopic[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchKnowledgeBox();
  }, [userId]);

  const fetchKnowledgeBox = async () => {
    try {
      const response = await knowledgeBoxAPI.getKnowledgeBox();
      setTopics(response.data.topics || []);
    } catch (error) {
      console.error('Error fetching knowledge box:', error);
      setTopics([]);
    } finally {
      setLoading(false);
    }
  };

  const getTimeAgo = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const days = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
    
    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days} days ago`;
    if (days < 30) return `${Math.floor(days / 7)} weeks ago`;
    return `${Math.floor(days / 30)} months ago`;
  };

  const formatTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    if (minutes < 1) return '<1 min';
    if (minutes < 60) return `${minutes} min`;
    return `${Math.floor(minutes / 60)}h ${minutes % 60}m`;
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg p-6 shadow-sm">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-3/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-20 bg-gray-100 rounded"></div>
            <div className="h-20 bg-gray-100 rounded"></div>
            <div className="h-20 bg-gray-100 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm">
      {/* Header */}
      <div className="p-4 border-b border-gray-100">
        <div className="flex items-center gap-2 mb-1">
          <Brain className="w-5 h-5 text-purple-600" />
          <h2 className="text-xl font-bold text-gray-900">My Knowledge Box</h2>
        </div>
        <p className="text-xs text-gray-500">
          Your personal AI-powered learning library
        </p>
      </div>

      {/* Topics List */}
      <div className="p-4">
        {topics.length === 0 ? (
          // Empty State
          <div className="text-center py-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-purple-50 rounded-full mb-4">
              <BookOpen className="w-8 h-8 text-purple-500" />
            </div>
            <h3 className="text-sm font-semibold text-gray-900 mb-2">
              Start Building Your Knowledge
            </h3>
            <p className="text-xs text-gray-500 max-w-xs mx-auto">
              As you read articles, AI will automatically organize important topics and facts here
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {topics.slice(0, 5).map((topic, index) => (
              <div
                key={index}
                className="border border-gray-100 rounded-lg p-3 hover:border-purple-200 hover:bg-purple-50/30 transition-all cursor-pointer"
              >
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-semibold text-sm text-gray-900 flex-1">
                    {topic.topic}
                  </h3>
                  <div className="flex items-center gap-1 text-xs text-purple-600 bg-purple-50 px-2 py-0.5 rounded-full">
                    <TrendingUp className="w-3 h-3" />
                    {topic.article_count}
                  </div>
                </div>

                {/* Subtopics */}
                {topic.subtopics.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-2">
                    {topic.subtopics.slice(0, 3).map((subtopic, idx) => (
                      <span
                        key={idx}
                        className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded"
                      >
                        {subtopic}
                      </span>
                    ))}
                  </div>
                )}

                {/* Stats */}
                <div className="flex items-center gap-3 text-xs text-gray-500">
                  <div className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {formatTime(topic.total_time_spent)}
                  </div>
                  <span>•</span>
                  <span>{getTimeAgo(topic.last_read)}</span>
                </div>

                {/* Key Entities */}
                {topic.key_entities.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-gray-100">
                    <div className="flex flex-wrap gap-1">
                      {topic.key_entities.slice(0, 4).map((entity, idx) => (
                        <span
                          key={idx}
                          className="text-xs text-purple-600 bg-purple-50 px-2 py-0.5 rounded-full"
                        >
                          {entity}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {topics.length > 5 && (
          <button className="w-full mt-3 text-xs text-purple-600 hover:text-purple-700 font-medium py-2 text-center">
            View All Topics →
          </button>
        )}
      </div>
    </div>
  );
}

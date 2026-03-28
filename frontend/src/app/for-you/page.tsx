'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import Header from '@/components/Header';
import ForYouLayout from '@/components/ForYouLayout';
import LoadingSpinner from '@/components/LoadingSpinner';
import ArticleModal from '@/components/ArticleModal';
import InterestManager from '@/components/InterestManager';
import { newsAPI, authAPI } from '@/lib/api';
import { NewsArticle } from '@/types';
import { Sparkles, Settings, TrendingUp } from 'lucide-react';

export default function ForYouPage() {
  const router = useRouter();
  const { user, loading: authLoading, updateUser } = useAuth();
  
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [recommendedArticles, setRecommendedArticles] = useState<NewsArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedArticle, setSelectedArticle] = useState<NewsArticle | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [articleStartTime, setArticleStartTime] = useState<number | null>(null);
  const [showInterestManager, setShowInterestManager] = useState(false);
  const [isPersonalized, setIsPersonalized] = useState(false);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login');
      return;
    }

    if (user) {
      // Check if user has interests
      if (!user.interests || user.interests.length === 0) {
        setShowInterestManager(true);
      }
      
      fetchArticles();
      fetchRecommendations();
      
      // Silent refresh recommendations every 3 minutes
      const refreshInterval = setInterval(() => {
        fetchRecommendations();
      }, 180000); // 3 minutes
      
      return () => clearInterval(refreshInterval);
    }
  }, [user, authLoading, router]);

  const fetchArticles = async () => {
    try {
      setLoading(true);
      const response = await newsAPI.getArticles();
      const articlesData = response.data || [];
      
      // Sort articles by publish_time (latest first)
      const sortedArticles = articlesData.sort((a: any, b: any) => {
        const dateA = new Date(a.publish_time || a.published_at || 0).getTime();
        const dateB = new Date(b.publish_time || b.published_at || 0).getTime();
        return dateB - dateA;
      });
      
      setArticles(sortedArticles);
    } catch (error) {
      console.error('Error fetching articles:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchRecommendations = async () => {
    try {
      const response = await newsAPI.getRecommendations();
      if (response.data && response.data.articles && response.data.articles.length > 0) {
        setRecommendedArticles(response.data.articles);
        setIsPersonalized(response.data.personalized || false);
      }
    } catch (error) {
      console.error('Error fetching recommendations:', error);
      // Silently fail - will use regular articles
    }
  };

  const handleInterestsUpdate = async (newInterests: string[]) => {
    try {
      await authAPI.updateProfile({ interests: newInterests });
      
      // Update user context
      if (updateUser) {
        updateUser({ ...user!, interests: newInterests });
      }
      
      setShowInterestManager(false);
      
      // Refresh recommendations with new interests
      setTimeout(() => {
        fetchRecommendations();
      }, 500);
    } catch (error) {
      console.error('Error updating interests:', error);
    }
  };

  const handleInteraction = async (articleId: string, action: string) => {
    try {
      await newsAPI.recordInteraction(articleId, action);
      
      // Refresh recommendations after meaningful interactions
      if (['like', 'save', 'share'].includes(action)) {
        setTimeout(() => {
          fetchRecommendations();
        }, 500);
      }
    } catch (error) {
      console.error('Error recording interaction:', error);
    }
  };

  const handleReadMore = (article: NewsArticle) => {
    setSelectedArticle(article);
    setIsModalOpen(true);
    setArticleStartTime(Date.now());
  };

  const handleCloseModal = () => {
    // Calculate dwell time and record interaction
    if (selectedArticle && articleStartTime) {
      const dwellTimeSeconds = Math.floor((Date.now() - articleStartTime) / 1000);
      
      // Record read with dwell time
      newsAPI.recordInteraction(selectedArticle._id, 'read', undefined, dwellTimeSeconds)
        .then(() => {
          // Refresh recommendations after significant engagement (30+ seconds)
          if (dwellTimeSeconds > 30) {
            setTimeout(() => fetchRecommendations(), 500);
          }
        })
        .catch(err => console.error('Error recording dwell time:', err));
    }
    
    setIsModalOpen(false);
    setSelectedArticle(null);
    setArticleStartTime(null);
  };

  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <LoadingSpinner />
      </div>
    );
  }

  const displayArticles = recommendedArticles.length > 0 ? recommendedArticles : articles;

  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      {/* Interest Manager */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {showInterestManager && (
          <div className="mt-6 bg-surface rounded-2xl p-6 border border-border shadow-lg">
            <InterestManager
              userInterests={user?.interests || []}
              onUpdate={handleInterestsUpdate}
            />
          </div>
        )}
      </div>

      <ForYouLayout 
        articles={displayArticles} 
        onArticleClick={handleReadMore}
      />

      {selectedArticle && (
        <ArticleModal
          article={selectedArticle}
          isOpen={isModalOpen}
          onClose={handleCloseModal}
        />
      )}
    </div>
  );
}

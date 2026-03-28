'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { newsAPI, interactionAPI } from '../lib/api';
import Header from '../components/Header';
import NewsCard from '../components/NewsCard';
import LoadingSpinner from '../components/LoadingSpinner';
import ArticleModal from '../components/ArticleModal';

interface Article {
  _id: string;
  title: string;
  summary: string;
  category: string;
  publish_time: string;
  sentiment_score: number;
  image_url: string;
  author: string;
  url: string;
}

export default function PublicHome() {
  const { user } = useAuth();
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [activeCategory, setActiveCategory] = useState('All');
  const [selectedArticle, setSelectedArticle] = useState<Article | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const observerTarget = useRef<HTMLDivElement>(null);

  const categories = ['All', 'Technology', 'Business', 'Health', 'Sports', 'Entertainment', 'Environment', 'Science', 'Politics'];

  const fetchArticles = useCallback(async (category?: string, pageNum: number = 1, append: boolean = false) => {
    try {
      if (append) {
        setLoadingMore(true);
      } else {
        setLoading(true);
      }
      
      const categoryParam = category === 'All' ? undefined : category;
      console.log(`🔍 Fetching articles for category: ${categoryParam || 'all'}, page: ${pageNum}`);
      
      const response = await newsAPI.getArticles({ 
        category: categoryParam,
        unlimited: true,
        page_size: 50,
        page: pageNum
      });
      
      const newArticles = response.data.results || response.data || [];
      console.log(`✅ Received ${newArticles.length} articles from API`);
      
      // Log first few articles before sort
      if (newArticles.length > 0) {
        console.log('📊 Articles BEFORE sort:');
        newArticles.slice(0, 3).forEach((a: any, i: number) => {
          const pubTime = a.publish_time || a.published_at || 'NO TIME';
          console.log(`  ${i + 1}. "${a.title?.substring(0, 50)}..." | publish_time: ${pubTime}`);
        });
      }
      
      // CRITICAL: Always sort by publish_time (latest first) - never trust API ordering
      const sortedArticles = [...newArticles].sort((a: any, b: any) => {
        try {
          const dateA = new Date(a.publish_time || 0).getTime();
          const dateB = new Date(b.publish_time || 0).getTime();
          if (isNaN(dateA)) console.warn('Invalid date for article:', a.title);
          if (isNaN(dateB)) console.warn('Invalid date for article:', b.title);
          return dateB - dateA; // Descending order (latest first = most recent = smallest time difference)
        } catch (e) {
          console.error('Sort error:', e);
          return 0;
        }
      });
      
      // Log first few articles after sort
      if (sortedArticles.length > 0) {
        console.log('📊 Articles AFTER sort:');
        sortedArticles.slice(0, 3).forEach((a: any, i: number) => {
          console.log(`  ${i + 1}. "${a.title?.substring(0, 50)}..." | publish_time: ${a.publish_time}`);
        });
      }
      
      if (sortedArticles.length > 0) {
        const firstTime = new Date(sortedArticles[0].publish_time || 0);
        const lastTime = new Date(sortedArticles[sortedArticles.length - 1].publish_time || 0);
        console.log(`📰 Article timeline: ${firstTime.toISOString()} (first/newest) → ${lastTime.toISOString()} (last/oldest)`);
      }
      
      if (append) {
        // Remove duplicates by checking article IDs and URLs
        setArticles(prev => {
          const existingIds = new Set(prev.map(a => a._id));
          const existingUrls = new Set(prev.map(a => a.url));
          const existingTitles = new Set(prev.map(a => a.title?.toLowerCase().trim()));
          const uniqueNew = sortedArticles.filter(article => 
            !existingIds.has(article._id) && 
            !existingUrls.has(article.url) &&
            !existingTitles.has(article.title?.toLowerCase().trim())
          );
          console.log(`🔍 Filtered ${sortedArticles.length} articles to ${uniqueNew.length} unique ones`);
          
          // If no new unique articles, we've reached the end
          if (uniqueNew.length === 0) {
            setHasMore(false);
          }
          
          // Merge and RE-SORT to maintain order
          const merged = [...prev, ...uniqueNew];
          const finalSorted = merged.sort((a: any, b: any) => {
            const dateA = new Date(a.publish_time || 0).getTime();
            const dateB = new Date(b.publish_time || 0).getTime();
            return dateB - dateA;
          });
          console.log(`✅ Merged and sorted ${finalSorted.length} total articles`);
          return finalSorted;
        });
      } else {
        // Remove duplicates within the initial set by ID, URL, and title
        const uniqueArticles = sortedArticles.filter((article, index, self) =>
          index === self.findIndex((a) => 
            a._id === article._id || 
            a.url === article.url ||
            a.title?.toLowerCase().trim() === article.title?.toLowerCase().trim()
          )
        );
        // FINAL SORT before storing in state
        uniqueArticles.sort((a: any, b: any) => {
          const dateA = new Date(a.publish_time || 0).getTime();
          const dateB = new Date(b.publish_time || 0).getTime();
          return dateB - dateA;
        });
        console.log(`🔍 Filtered ${sortedArticles.length} articles to ${uniqueArticles.length} unique ones`);
        
        // DEBUG: Log the order we're about to set
        console.log(`🔴 ARTICLES TO DISPLAY (in order):`);
        uniqueArticles.slice(0, 5).forEach((a, i) => {
          const time = new Date(a.publish_time || 0);
          console.log(`  ${i+1}. ${a.title?.substring(0, 50)} | Time: ${time.toISOString()}`);
        });
        
        setArticles(uniqueArticles);
        setHasMore(sortedArticles.length >= 50);
      }
      
      return newArticles;
    } catch (error: any) {
      console.error('❌ Error fetching articles:', error);
      console.error('❌ Error response:', error.response?.data);
      
      if (!append) {
        setArticles([]);
      }
      return [];
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, []);

  useEffect(() => {
    setPage(1);
    setHasMore(true);
    fetchArticles(activeCategory, 1, false);
  }, [activeCategory, fetchArticles]);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loadingMore && !loading) {
          const nextPage = page + 1;
          setPage(nextPage);
          fetchArticles(activeCategory, nextPage, true);
        }
      },
      { threshold: 0.1 }
    );

    const currentTarget = observerTarget.current;
    if (currentTarget) {
      observer.observe(currentTarget);
    }

    return () => {
      if (currentTarget) {
        observer.unobserve(currentTarget);
      }
    };
  }, [hasMore, loadingMore, loading, page, activeCategory, fetchArticles]);

  const handleCategoryChange = (category: string) => {
    setActiveCategory(category);
  };

  const handleReadMore = async (article: Article) => {
    setSelectedArticle(article);
    setIsModalOpen(true);
    // ArticleModal component will automatically track the 'read' action
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedArticle(null);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <div className="relative group">
              <img 
                src="/logo.jpg" 
                alt="InfoCred Logo" 
                className="w-24 h-24 rounded-full object-cover shadow-lg transition-all duration-500 ease-in-out group-hover:scale-110 group-hover:rotate-6 group-hover:shadow-2xl animate-pulse-slow"
                style={{
                  animation: 'float 3s ease-in-out infinite, glow 2s ease-in-out infinite alternate'
                }}
              />
              <div className="absolute inset-0 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 opacity-0 group-hover:opacity-20 transition-opacity duration-500 blur-xl"></div>
            </div>
          </div>
          <h1 className="text-3xl md:text-4xl font-bold mb-2 animate-title-entrance" style={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
            letterSpacing: '0.03em',
            textShadow: '0 0 30px rgba(102, 126, 234, 0.3)',
            fontFamily: '"Playfair Display", "Georgia", serif',
            animation: 'title-entrance 1.2s ease-out, gradient-shift 3s ease-in-out infinite'
          }}>
            InfoCred
          </h1>
          <p className="text-lg md:text-xl mb-4 animate-subtitle" style={{
            fontFamily: '"Inter", "Roboto", sans-serif',
            fontWeight: 500,
            background: 'linear-gradient(90deg, #4a5568, #2d3748, #4a5568)',
            backgroundSize: '200% auto',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
            animation: 'subtitle-slide 3s ease-in-out infinite, fade-in 1s ease-out 0.4s both',
            letterSpacing: '0.02em'
          }}>
            {user ? `Welcome back, ${user.name}! Here are your personalized news updates.` : 'Stay informed with the latest news from around the world'}
          </p>
        </div>
        
        <style jsx>{`
          @keyframes float {
            0%, 100% {
              transform: translateY(0px);
            }
            50% {
              transform: translateY(-10px);
            }
          }
          
          @keyframes glow {
            from {
              box-shadow: 0 0 10px rgba(59, 130, 246, 0.5),
                          0 0 20px rgba(59, 130, 246, 0.3),
                          0 0 30px rgba(59, 130, 246, 0.2);
            }
            to {
              box-shadow: 0 0 20px rgba(147, 51, 234, 0.6),
                          0 0 30px rgba(147, 51, 234, 0.4),
                          0 0 40px rgba(147, 51, 234, 0.3);
            }
          }
          
          @keyframes fade-in {
            from {
              opacity: 0;
              transform: translateY(-20px);
            }
            to {
              opacity: 1;
              transform: translateY(0);
            }
          }
          
          @keyframes title-entrance {
            0% {
              opacity: 0;
              transform: translateY(-30px) scale(0.9);
              filter: blur(10px);
            }
            60% {
              transform: translateY(5px) scale(1.02);
            }
            100% {
              opacity: 1;
              transform: translateY(0) scale(1);
              filter: blur(0);
            }
          }
          
          @keyframes gradient-shift {
            0%, 100% {
              filter: hue-rotate(0deg) brightness(1);
            }
            50% {
              filter: hue-rotate(20deg) brightness(1.1);
            }
          }
          
          .animate-title-entrance {
            animation: title-entrance 1.2s ease-out;
          }
          
          .animate-fade-in {
            animation: fade-in 1s ease-out;
          }
          
          .animate-fade-in-delay {
            animation: fade-in 1s ease-out 0.3s both;
          }
          
          @keyframes subtitle-slide {
            0%, 100% {
              background-position: 0% center;
            }
            50% {
              background-position: 100% center;
            }
          }
          
          .animate-subtitle {
            animation: subtitle-slide 3s ease-in-out infinite, fade-in 1s ease-out 0.4s both;
          }
        `}</style>

        {/* Category Filter */}
        <div className="flex flex-wrap justify-center gap-2 mb-8">
          {categories.map((category) => (
            <button
              key={category}
              onClick={() => handleCategoryChange(category)}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                activeCategory === category
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
              }`}
            >
              {category}
            </button>
          ))}
        </div>

        {/* Articles Display */}
        {loading ? (
          <div className="flex justify-center items-center py-12">
            <LoadingSpinner />
            <span className="ml-3 text-gray-600">Loading articles...</span>
          </div>
        ) : articles.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-gray-500 text-lg">
              <p className="mb-4">No articles found for "{activeCategory}"</p>
              <p className="text-sm">Try selecting a different category or refresh the page</p>
              <button 
                onClick={() => fetchArticles(activeCategory)}
                className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Refresh Articles
              </button>
            </div>
          </div>
        ) : (
          <>
            <div className="flex justify-end items-center mb-6">
              <button 
                onClick={() => {
                  setPage(1);
                  setHasMore(true);
                  fetchArticles(activeCategory, 1, false);
                }}
                className="px-4 py-2 text-blue-600 hover:text-blue-800 text-sm font-medium"
              >
                Refresh
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {articles.map((article, displayIndex) => {
                if (displayIndex === 0) {
                  console.log(`🎯 RENDERING GRID - First article:`, article.title?.substring(0, 50), `| Time: ${article.publish_time}`);
                }
                if (displayIndex < 5) {
                  console.log(`  [${displayIndex}] ${article.title?.substring(0, 40)}`);
                }
                return (
                  <div key={article._id}>
                    <NewsCard
                      article={article}
                      showActions={false}
                      onReadMore={handleReadMore}
                    />
                  </div>
                );
              })}
            </div>

            {/* Infinite Scroll Trigger */}
            <div ref={observerTarget} className="text-center mt-12 py-8">
              {loadingMore && (
                <div className="flex justify-center items-center">
                  <LoadingSpinner />
                  <span className="ml-3 text-gray-600">Loading more articles...</span>
                </div>
              )}
            </div>
          </>
        )}
      </main>

      {/* Article Modal */}
      <ArticleModal
        article={selectedArticle}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
      />
    </div>
  );
}

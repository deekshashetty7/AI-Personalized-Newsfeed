'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import Header from '@/components/Header';
import NewsCard from '@/components/NewsCard';
import LoadingSpinner from '@/components/LoadingSpinner';
import ArticleModal from '@/components/ArticleModal';
import { newsAPI, interactionAPI, recommendationAPI } from '@/lib/api';
import { NewsArticle } from '@/types';
import { Sparkles, RefreshCw, Filter, Search, X } from 'lucide-react';

export default function HomePage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [recommendations, setRecommendations] = useState<NewsArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [activeTab, setActiveTab] = useState<string>('all');
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [selectedArticle, setSelectedArticle] = useState<NewsArticle | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [showSubcategoryDropdown, setShowSubcategoryDropdown] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchTimeout, setSearchTimeout] = useState<NodeJS.Timeout | null>(null);
  const observer = useRef<IntersectionObserver | null>(null);

  // Subcategories mapping
  const SUB_INTERESTS: Record<string, string[]> = {
    Technology: ['AI & Machine Learning', 'Cybersecurity', 'Gadgets & Hardware', 'Space Tech', 'Software Development', 'Cloud Computing', 'Blockchain & Crypto', 'Mobile Technology', '5G & Networking', 'Virtual Reality'],
    Business: ['Stock Market', 'Cryptocurrency', 'Startups', 'E-commerce', 'Marketing', 'Finance', 'Real Estate', 'Economics', 'Leadership', 'Entrepreneurship'],
    Sports: ['Football', 'Basketball', 'Cricket', 'Tennis', 'Olympics', 'Fitness', 'Motorsports', 'Golf', 'Esports', 'Extreme Sports'],
    Entertainment: ['Movies', 'TV Shows', 'Music', 'Gaming', 'Celebrity News', 'Fashion', 'Art & Culture', 'Books', 'Theater', 'Streaming'],
    Health: ['Nutrition', 'Mental Health', 'Fitness & Exercise', 'Medical Research', 'Wellness', 'Alternative Medicine', 'Public Health', 'Diet Plans', 'Yoga & Meditation', 'Healthcare Technology'],
    Science: ['Physics', 'Biology', 'Chemistry', 'Astronomy', 'Climate Science', 'Neuroscience', 'Genetics', 'Mathematics', 'Research & Innovation', 'Environmental Science'],
    Environment: ['Climate Change', 'Renewable Energy', 'Conservation', 'Sustainability', 'Wildlife', 'Pollution', 'Ocean Conservation', 'Green Technology', 'Recycling', 'Biodiversity'],
    Politics: ['Elections', 'Policy', 'International Relations', 'Government', 'Activism', 'Political Analysis', 'Legislation', 'Diplomacy', 'Human Rights', 'Political Economy']
  };

  // Get user's interest categories or default categories
  const getUserCategories = () => {
    // Main categories only (no subcategories)
    const mainCategories = ['Technology', 'Business', 'Sports', 'Entertainment', 'Health', 'Science', 'Environment', 'Politics'];
    
    console.log('🔍 getUserCategories called');
    console.log('👤 User object:', user);
    console.log('📋 User interests:', user?.interests);
    console.log('📊 Is Array?', Array.isArray(user?.interests));
    
    if (user && user.interests && Array.isArray(user.interests) && user.interests.length > 0) {
      console.log('✅ User is logged in with interests:', user.interests);
      
      // Extract ONLY main categories from user's interests (filter out subcategories)
      const userMainCategories = [];
      
      user.interests.forEach(interest => {
        console.log('  Checking interest:', interest, 'Type:', typeof interest);
        if (typeof interest === 'string' && interest.trim().length > 0) {
          // Only include if it's a main category
          if (mainCategories.includes(interest) && !userMainCategories.includes(interest)) {
            console.log('    ✓ Added main category:', interest);
            userMainCategories.push(interest);
          } else {
            console.log('    ✗ Skipped (subcategory or duplicate):', interest);
          }
        }
      });
      
      console.log('✅ Final main categories:', userMainCategories);
      
      // Show All + ONLY user's selected main categories (no subcategories)
      if (userMainCategories.length > 0) {
        const result = ['All', ...userMainCategories];
        console.log('🎯 Returning categories:', result);
        return result;
      }
      
      // If user has no main categories selected, show only All
      console.log('⚠️ No main categories found, showing only All');
      return ['All'];
    }
    
    // If no user logged in, show all main categories
    console.log('ℹ️ No user logged in, showing all categories');
    return ['All', ...mainCategories];
  };

  const categories = getUserCategories();
  
  // Get user's selected subcategories for a main category
  const getUserSubcategories = (mainCategory: string): string[] => {
    if (!user || !user.interests || !Array.isArray(user.interests)) {
      console.log('❌ No user or interests for subcategories');
      return [];
    }
    
    const availableSubcategories = SUB_INTERESTS[mainCategory] || [];
    const userSubs = user.interests.filter(interest => 
      availableSubcategories.includes(interest)
    );
    
    console.log(`🔍 Subcategories for ${mainCategory}:`, userSubs);
    console.log(`   Available subcategories:`, availableSubcategories);
    console.log(`   User interests:`, user.interests);
    return userSubs;
  };

  // Toggle subcategory dropdown
  const toggleSubcategoryDropdown = (category: string) => {
    if (category === 'All') return;
    
    if (showSubcategoryDropdown === category) {
      setShowSubcategoryDropdown(null);
    } else {
      setShowSubcategoryDropdown(category);
    }
  };
  
  // Debug: Log categories and user state
  console.log('🎯 Categories to display:', categories);
  console.log('👤 Current user:', user);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (showSubcategoryDropdown) {
        const target = event.target as HTMLElement;
        // Close if clicking outside the category filter section
        if (!target.closest('.category-filter-section')) {
          setShowSubcategoryDropdown(null);
        }
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showSubcategoryDropdown]);

  // Fetch data when component mounts or user changes
  useEffect(() => {
    if (!authLoading) {
      console.log('User state changed, fetching data...', user ? `Logged in as ${user.name}` : 'Not logged in');
      fetchData();
    }
  }, [user, authLoading]);

  const fetchData = async () => {
    setLoading(true);
    try {
      console.log('🚀 Starting fetchData...');
      console.log('👤 User state:', user ? `${user.name} (${user.email})` : 'Not logged in');
      console.log('📂 Selected category:', selectedCategory);
      
      // Always fetch all articles (no category filter) to show all news
      await fetchArticles(undefined); // undefined = all categories
      setLoading(false); // Stop loading spinner once articles are available
      
      // Then fetch recommendations in background (non-blocking)
      const backgroundPromises = [];
      
      if (user) {
        console.log('⭐ User is logged in, fetching recommendations...');
        backgroundPromises.push(fetchRecommendations());
      } else {
        console.log('ℹ️ User not logged in, skipping recommendations');
      }
      
      // Let background requests complete without blocking UI
      Promise.allSettled(backgroundPromises).then(() => {
        console.log('✅ Background data fetched successfully');
      });
      
    } catch (error) {
      console.error('❌ Error fetching data:', error);
      setLoading(false);
    }
  };

  const fetchArticles = async (category?: string, pageNum: number = 1, append: boolean = false, search?: string) => {
    try {
      const categoryParam = category === 'All' ? undefined : category;
      console.log(`🔍 Fetching articles for category: ${categoryParam || 'all'}, page: ${pageNum}, search: ${search || 'none'}`);
      console.log(`📋 Request params:`, { category: categoryParam, search, unlimited: true, page_size: 100 });
      
      const response = await newsAPI.getArticles({ 
        category: categoryParam,
        search: search,
        unlimited: true,
        page_size: 100 
      });
      
      const newArticles = response.data || [];
      console.log(`✅ Received ${newArticles.length} articles`);
      
      // Log first 5 articles to verify order from API
      console.log('📊 First 5 articles from API:');
      newArticles.slice(0, 5).forEach((a: any, i: number) => {
        console.log(`  ${i+1}. [${a.publish_time}] ${a.title?.substring(0, 50)}`);
      });
      
      // Sort by publish_time (latest first)
      const sortedArticles = [...newArticles].sort((a: any, b: any) => {
        const dateA = new Date(a.publish_time || 0).getTime();
        const dateB = new Date(b.publish_time || 0).getTime();
        return dateB - dateA; // Descending order (latest first)
      });
      
      // Log after sorting
      console.log('📊 First 5 articles AFTER sorting:');
      sortedArticles.slice(0, 5).forEach((a: any, i: number) => {
        console.log(`  ${i+1}. [${a.publish_time}] ${a.title?.substring(0, 50)}`);
      });
      
      // Use backend-filtered articles directly (no client-side filtering needed)
      const filteredArticles = sortedArticles;
      console.log(`📂 Using ${filteredArticles.length} articles from backend (category: ${categoryParam || 'all'})`);
      
      if (filteredArticles.length > 0) {
        console.log('📰 Sample article:', filteredArticles[0]);
        
        // Log category distribution
        const categoryCount: Record<string, number> = {};
        filteredArticles.forEach((article: any) => {
          const cat = article.category || 'Unknown';
          categoryCount[cat] = (categoryCount[cat] || 0) + 1;
        });
        console.log('📊 Category distribution:', categoryCount);
        console.log('📊 First 5 articles:', filteredArticles.slice(0, 5).map((a: any) => ({ title: a.title.substring(0, 50), category: a.category })));
      }
      
      if (append) {
        setArticles(prev => {
          // Remove duplicates by checking article IDs and URLs and titles
          const existingIds = new Set(prev.map(a => a._id));
          const existingUrls = new Set(prev.map(a => a.url));
          const existingTitles = new Set(prev.map(a => a.title?.toLowerCase().trim()));
          const uniqueNew = filteredArticles.filter(article => 
            !existingIds.has(article._id) && 
            !existingUrls.has(article.url) &&
            !existingTitles.has(article.title?.toLowerCase().trim())
          );
          console.log(`🔍 Filtered ${filteredArticles.length} articles to ${uniqueNew.length} unique ones (removed ${filteredArticles.length - uniqueNew.length} duplicates)`);
          return [...prev, ...uniqueNew];
        });
      } else {
        // Remove duplicates within the initial set
        const uniqueArticles = filteredArticles.filter((article, index, self) =>
          index === self.findIndex((a) => 
            a._id === article._id || 
            a.url === article.url ||
            a.title?.toLowerCase().trim() === article.title?.toLowerCase().trim()
          )
        );
        console.log(`🔍 Initial load: ${filteredArticles.length} articles filtered to ${uniqueArticles.length} unique ones`);
        setArticles(uniqueArticles);
      }
      
      // Check if there are more articles to load
      // Use the original newArticles length (before sorting/filtering) to determine if more exist
      const receivedFullBatch = newArticles.length >= 100;
      setHasMore(receivedFullBatch);
      console.log(`📊 HasMore set to ${receivedFullBatch} (received ${newArticles.length} articles from API)`);
      
      return filteredArticles;
    } catch (error: any) {
      console.error('❌ Error fetching articles:', error);
      console.error('❌ Error response:', error.response?.data);
      
      if (!append) {
        setArticles([]);
      }
      setHasMore(false);
      return [];
    }
  };

  const fetchRecommendations = async () => {
    if (!user) return; // Skip if not logged in
    try {
      console.log('Fetching recommendations for user:', user.name);
      const response = await recommendationAPI.get();
      console.log(`Received ${response.data.articles?.length || 0} recommendations`);
      setRecommendations(response.data.articles || []);
    } catch (error: any) {
      console.error('Error fetching recommendations:', error);
      console.error('Error details:', error.response?.data);
      setRecommendations([]);
    }
  };



  const handleInteraction = async (articleId: string, action: string, commentText?: string) => {
    if (!user) {
      router.push('/login');
      return;
    }
    try {
      const payload: any = { article_id: articleId, action };
      if (commentText) {
        payload.comment_text = commentText;
      }
      await interactionAPI.create(payload);
      
      // Refresh recommendations after interaction
      if (action === 'like' || action === 'dislike') {
        fetchRecommendations();
      }
    } catch (error) {
      console.error('Error creating interaction:', error);
    }
  };

  const handleCategoryChange = (category: string) => {
    console.log('Category changed to:', category);
    setSelectedCategory(category);
    setActiveTab('all'); // Reset to all tab when changing category
    setPage(1);
    setHasMore(true);
    setSearchQuery(''); // Clear search when changing category
    
    // Both main categories and subcategories are now handled by backend
    // Just pass the category name to the backend
    fetchArticles(category === 'All' ? undefined : category, 1, false);
  };

  const handleTabChange = (tab: string) => {
    console.log('Tab changed to:', tab);
    setActiveTab(tab);
  };

  const handleRefresh = async () => {
    console.log('🔄 Refresh button clicked!');
    console.log('📍 Current category:', selectedCategory);
    console.log('📍 Current search:', searchQuery);
    
    setLoading(true);
    setPage(1);
    setHasMore(true);
    setArticles([]); // Clear current articles
    
    try {
      // Backend now handles both main categories and subcategories
      console.log('🔄 Refreshing category:', selectedCategory);
      const response = await newsAPI.getArticles({ 
        category: selectedCategory === 'All' ? undefined : selectedCategory,
        unlimited: true,
        page_size: 20
      });
      const newArticles = response.data || [];
      // Sort by publish_time (latest first)
      const sorted = [...newArticles].sort((a: any, b: any) => {
        const dateA = new Date(a.publish_time || 0).getTime();
        const dateB = new Date(b.publish_time || 0).getTime();
        return dateB - dateA;
      });
      setArticles(sorted);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (query: string) => {
    setSearchQuery(query);
    
    // Clear previous timeout
    if (searchTimeout) {
      clearTimeout(searchTimeout);
    }
    
    if (query.trim() === '') {
      // If search is cleared, fetch normal articles immediately
      setIsSearching(false);
      await fetchArticles(selectedCategory === 'All' ? undefined : selectedCategory, 1, false);
    } else {
      // Debounce search - wait 500ms after user stops typing
      setIsSearching(true);
      const timeout = setTimeout(async () => {
        console.log('🔍 Searching for:', query);
        await fetchArticles(selectedCategory === 'All' ? undefined : selectedCategory, 1, false, query);
        setIsSearching(false);
      }, 500);
      setSearchTimeout(timeout);
    }
  };

  const clearSearch = () => {
    setSearchQuery('');
    fetchArticles(selectedCategory === 'All' ? undefined : selectedCategory, 1, false);
  };

  // Load more articles when scrolling
  const loadMore = useCallback(async () => {
    if (loadingMore || !hasMore || activeTab !== 'all') {
      console.log('⏭️ Skipping loadMore:', { loadingMore, hasMore, activeTab });
      return;
    }
    
    console.log('📥 Loading more articles, current page:', page);
    setLoadingMore(true);
    const nextPage = page + 1;
    setPage(nextPage);
    
    try {
      await fetchArticles(selectedCategory === 'All' ? undefined : selectedCategory, nextPage, true);
    } catch (error) {
      console.error('❌ Error loading more articles:', error);
    } finally {
      setLoadingMore(false);
    }
  }, [loadingMore, hasMore, page, selectedCategory, activeTab]);

  // Intersection Observer callback
  const lastArticleRef = useCallback((node: HTMLDivElement | null) => {
    if (loadingMore) return;
    
    // Disconnect previous observer
    if (observer.current) {
      observer.current.disconnect();
      observer.current = null;
    }
    
    // Create new observer only if we have a node and should load more
    if (node && hasMore && activeTab === 'all') {
      observer.current = new IntersectionObserver(
        (entries) => {
          if (entries[0].isIntersecting && hasMore && activeTab === 'all' && !loadingMore) {
            console.log('👀 Last article visible, loading more...');
            loadMore();
          }
        },
        { threshold: 0.1 } // Trigger when 10% visible
      );
      
      observer.current.observe(node);
    }
  }, [loadingMore, hasMore, loadMore, activeTab]);

  const handleReadMore = (article: NewsArticle) => {
    setSelectedArticle(article);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedArticle(null);
  };

  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <LoadingSpinner />
      </div>
    );
  }

  // Ensure no duplicates in display by using a final de-duplication step
  const rawDisplayArticles = activeTab === 'recommended' ? articles : articles;
  
  // Final de-duplication: remove any duplicates by ID, URL, or title
  const displayArticles = rawDisplayArticles.filter((article, index, self) => {
    const firstIndex = self.findIndex((a) => 
      a._id === article._id || 
      a.url === article.url ||
      a.title?.toLowerCase().trim() === article.title?.toLowerCase().trim()
    );
    return index === firstIndex;
  });

  // Log if duplicates were found and removed
  if (rawDisplayArticles.length !== displayArticles.length) {
    console.warn(`⚠️ Removed ${rawDisplayArticles.length - displayArticles.length} duplicate articles from display`);
  }

  console.log('🎯 Display state:', {
    activeTab,
    articlesCount: articles.length,
    recommendationsCount: recommendations.length,
    displayArticlesCount: displayArticles.length
  });

  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Top Message */}
        <div className="mb-8 animate-slideUp">
          <div className="flex justify-center mb-4">
            <div className="relative group">
              <img 
                src="/logo.jpg" 
                alt="InfoCred Logo" 
                className="w-20 h-20 rounded-full object-cover shadow-lg transition-all duration-500 ease-in-out group-hover:scale-110 group-hover:rotate-6 group-hover:shadow-2xl"
                style={{
                  animation: 'float 3s ease-in-out infinite, glow 2s ease-in-out infinite alternate'
                }}
              />
              <div className="absolute inset-0 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 opacity-0 group-hover:opacity-20 transition-opacity duration-500 blur-xl"></div>
            </div>
          </div>
          <h1
            className="text-3xl md:text-4xl font-bold text-center mb-2 animate-title-entrance"
            style={{
              fontFamily: '"Playfair Display", "Georgia", serif',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
              letterSpacing: '0.03em',
              textShadow: '0 0 30px rgba(102, 126, 234, 0.3)',
              animation: 'title-entrance 1.2s ease-out, gradient-shift 3s ease-in-out infinite'
            }}
          >
            InfoCred
          </h1>
          <p
            className="text-lg md:text-xl text-center animate-subtitle"
            style={{
              fontFamily: '"Inter", "Roboto", sans-serif',
              fontWeight: 500,
              background: 'linear-gradient(90deg, #4a5568, #2d3748, #4a5568)',
              backgroundSize: '200% auto',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
              animation: 'subtitle-slide 3s ease-in-out infinite, fade-in 1s ease-out 0.4s both',
              letterSpacing: '0.02em'
            }}
          >
            Stay informed with the latest news from around the world...
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
        
        {/* Smart Search Bar */}
        <div className="mb-6">
          <div className="relative max-w-3xl mx-auto">
            <div className="relative group">
              <Search className={`absolute left-4 top-1/2 transform -translate-y-1/2 w-4 h-4 transition-all duration-200 ${isSearching ? 'animate-pulse text-blue-600' : 'text-primary group-hover:scale-110'}`} />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => handleSearch(e.target.value)}
                placeholder="Search by keywords: e.g., 'climate change', 'AI technology', 'sports news'..."
                className="w-full pl-10 pr-10 py-2.5 border-2 border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary text-sm bg-white shadow-sm hover:shadow-md transition-all duration-200 placeholder-gray-400"
                style={{ fontFamily: 'Inter, sans-serif' }}
              />
              {isSearching && (
                <div className="absolute right-12 top-1/2 transform -translate-y-1/2 text-xs text-blue-600 font-medium">
                  Searching...
                </div>
              )}
              {searchQuery && (
                <button
                  onClick={clearSearch}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 w-6 h-6 bg-red-50 hover:bg-red-100 text-red-500 hover:text-red-600 rounded-full flex items-center justify-center transition-all duration-200 hover:scale-110"
                  title="Clear search"
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </div>
            {searchQuery && (
              <div className="mt-2 text-xs text-gray-600 px-2">
                💡 Tip: Search matches keywords in article headlines only. Try: "climate", "technology AI", "sports cricket"
              </div>
            )}
          </div>
        </div>
        
        {/* Category Filter */}
        <div className="bg-white rounded-xl shadow-sm p-4 transition-all duration-300 category-filter-section" style={{ position: 'relative', zIndex: 50, marginBottom: '24px' }}>
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex-1">
              {/* Main Categories Row */}
              <div className="flex items-center gap-2 pb-2 flex-wrap">
                {categories.map((category) => {
                  const userSubcategories = getUserSubcategories(category);
                  const hasSubcategories = category !== 'All' && userSubcategories.length > 0;
                  
                  return (
                    <div key={category} className="relative">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          console.log('🔘 Main category clicked:', category);
                          
                          // Clear articles first to prevent duplicates
                          setArticles([]);
                          
                          // Set selected category and clear search
                          setSelectedCategory(category);
                          setSearchQuery('');
                          setActiveTab('all');
                          setPage(1);
                          setHasMore(true);
                          
                          // Fetch articles for the main category (not search)
                          fetchArticles(category === 'All' ? undefined : category, 1, false);
                          
                          // Open subcategories dropdown if available (keep it open)
                          if (hasSubcategories) {
                            setShowSubcategoryDropdown(category);
                          } else {
                            // Close dropdown when clicking categories without subcategories
                            setShowSubcategoryDropdown(null);
                          }
                        }}
                        className={`px-5 py-2.5 rounded-lg font-semibold text-sm whitespace-nowrap transition-all duration-200 shadow-sm flex items-center gap-1 ${
                          category === selectedCategory && !searchQuery
                            ? 'bg-gradient-to-r from-primary to-secondary text-white shadow-md scale-105'
                            : showSubcategoryDropdown === category
                            ? 'bg-gradient-to-r from-primary to-secondary text-white shadow-md'
                            : 'bg-gray-100 text-text hover:bg-gray-200 hover:shadow'
                        } ${hasSubcategories ? 'cursor-pointer' : ''}`}
                      >
                        <span>{category}</span>
                      </button>
                    </div>
                  );
                })}
              </div>
              
              {/* Subcategories Row - Display below main categories */}
              {categories.map((category) => {
                const userSubcategories = getUserSubcategories(category);
                const hasSubcategories = category !== 'All' && userSubcategories.length > 0;
                const shouldShow = hasSubcategories && showSubcategoryDropdown === category;
                
                if (!shouldShow) return null;
                
                return (
                  <div 
                    key={`sub-${category}`}
                    className="mt-3 pt-3 border-t border-gray-200 animate-fadeIn"
                    style={{ position: 'relative', zIndex: 100 }}
                  >
                    <div className="flex flex-wrap gap-2">
                      {userSubcategories.map((subcategory) => (
                        <button
                          key={subcategory}
                          type="button"
                          onClick={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            console.log('🔥 Subcategory button clicked:', subcategory);
                            console.log('📍 Current category:', selectedCategory);
                            
                            // Clear articles first
                            setArticles([]);
                            
                            // Set the subcategory as selected
                            setSelectedCategory(subcategory);
                            setActiveTab('all');
                            setPage(1);
                            setHasMore(true);
                            
                            // Fetch articles with subcategory as category parameter (backend handles it)
                            fetchArticles(subcategory, 1, false);
                            
                            // Keep dropdown open - don't close it
                          }}
                          onMouseDown={(e) => {
                            console.log('👆 Mouse down on:', subcategory);
                          }}
                          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-150 cursor-pointer hover:scale-105 ${
                            subcategory === selectedCategory
                              ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-md ring-2 ring-blue-300'
                              : 'bg-blue-50 text-blue-700 hover:bg-blue-100 hover:shadow-sm'
                          }`}
                          style={{ pointerEvents: 'auto', userSelect: 'none' }}
                        >
                          {subcategory}
                        </button>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
            
            <div className="flex items-center gap-2">
              <button
                onClick={handleRefresh}
                className="flex items-center space-x-1.5 px-3 py-2 border-2 border-primary text-primary rounded-lg hover:bg-primary hover:text-white transition-all duration-200"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span className="text-xs font-semibold">Refresh</span>
              </button>
            </div>
          </div>
        </div>

        {/* Content Grid */}
        <div className="max-w-full">
          <div className="space-y-6">
            {/* Articles Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {displayArticles.length > 0 ? (
                <>
                  {displayArticles.map((article, index) => {
                    // Attach ref to the last article for infinite scroll
                    const isLastArticle = activeTab === 'all' && index === displayArticles.length - 1;
                    
                    return (
                      <div 
                        key={article._id} 
                        ref={isLastArticle ? lastArticleRef : null}
                      >
                        <NewsCard
                          article={article}
                          onInteraction={user ? handleInteraction : undefined}
                          showActions={user ? true : false}
                          onReadMore={handleReadMore}
                        />
                      </div>
                    );
                  })}
                  
                  {/* Loading indicator for infinite scroll */}
                  {loadingMore && activeTab === 'all' && (
                    <div className="col-span-full flex justify-center py-8">
                      <div className="flex items-center space-x-2 text-primary">
                        <RefreshCw className="w-5 h-5 animate-spin" />
                        <span className="text-sm font-medium">Loading more articles...</span>
                      </div>
                    </div>
                  )}
                  
                  {/* End of articles indicator */}
                  {!hasMore && activeTab === 'all' && displayArticles.length > 0 && (
                    <div className="col-span-full text-center py-8 text-gray-500">
                      <p className="text-sm">You've reached the end of the news feed</p>
                    </div>
                  )}
                </>
              ) : (
                <div className="col-span-full bg-white rounded-xl shadow-sm p-12 text-center">
                  <div className="text-6xl mb-4">📰</div>
                  <p className="text-xl font-semibold text-text mb-2">No articles found</p>
                  <p className="text-text-secondary mb-6">
                    {activeTab === 'recommended' 
                      ? 'Start interacting with articles to get personalized recommendations'
                      : `Try selecting a different ${selectedCategory !== 'All' ? 'category' : 'tab'}`
                    }
                  </p>
                  <button
                    onClick={handleRefresh}
                    className="px-6 py-3 bg-gradient-to-r from-primary to-secondary text-white rounded-lg hover:shadow-lg transition-all duration-200"
                  >
                    Refresh News
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
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

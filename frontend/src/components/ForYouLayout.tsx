'use client';

import { NewsArticle } from '@/types';
import { formatDistanceToNow } from 'date-fns';

interface ForYouLayoutProps {
  articles: NewsArticle[];
  onArticleClick: (article: NewsArticle) => void;
}

export default function ForYouLayout({ articles, onArticleClick }: ForYouLayoutProps) {
  if (!articles || articles.length === 0) return null;

  const getTimeAgo = (publishTime: string) => {
    try {
      const date = new Date(publishTime);
      if (isNaN(date.getTime())) return 'Just now';
      return formatDistanceToNow(date, { addSuffix: true }).replace('about ', '');
    } catch {
      return 'Just now';
    }
  };

  // Helper function to get proper source name
  const getSourceName = (article: NewsArticle) => {
    if (article.source) {
      // For Reddit sources, display only "Reddit"
      if (article.source.toLowerCase().includes('reddit')) {
        return 'Reddit';
      }
      // Capitalize first letter of each word
      return article.source
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
        .join(' ');
    }
    // Fallback to category if source is not available
    if (article.category) {
      return article.category.charAt(0).toUpperCase() + article.category.slice(1).toLowerCase();
    }
    return 'News';
  };

  // Helper to get image URL from either image_url or image field
  const getImageUrl = (article: NewsArticle) => {
    const url = article.image_url || (article as any).image || '';
    // Return empty string if URL is not valid
    if (!url || typeof url !== 'string' || !url.startsWith('http')) {
      return '';
    }
    // Proxy through backend to avoid CORS 403 errors
    // Use full backend URL, not relative path
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
    const proxyUrl = `${backendUrl}/news/proxy-image/?url=${encodeURIComponent(url)}`;
    console.log('🖼️ getImageUrl - Original:', url.substring(0, 60));
    console.log('🖼️ getImageUrl - Backend URL:', backendUrl);
    console.log('🖼️ getImageUrl - Proxy URL:', proxyUrl.substring(0, 100));
    return proxyUrl;
  };

  // Debug log first article
  if (articles.length > 0) {
    console.log('🖼️ First article:', articles[0]);
    console.log('🖼️ Image URL:', articles[0].image_url);
    console.log('🖼️ getImageUrl result:', getImageUrl(articles[0]));
  }

  // Sort articles for different sections
  const sortedByTime = [...articles].sort((a, b) => 
    new Date(b.publish_time || b.published_at).getTime() - new Date(a.publish_time || a.published_at).getTime()
  );
  
  const sortedBySentiment = [...articles].sort((a, b) => 
    (b.sentiment_score || 0) - (a.sentiment_score || 0)
  );

  // Instagram-style personalized recommendations for "AI Picks" section
  const getPersonalizedForYou = () => {
    const recentArticles = sortedByTime.slice(0, 30);
    
    const scoredArticles = recentArticles.map(article => {
      let score = 0;
      
      const hoursSincePublish = (Date.now() - new Date(article.publish_time || article.published_at).getTime()) / (1000 * 60 * 60);
      score += Math.max(0, 10 - hoursSincePublish);
      
      const sentiment = article.sentiment_score || 0;
      if (sentiment > 0.2) {
        score += sentiment * 5;
      } else if (sentiment < -0.5) {
        score += 3;
      }
      
      if (article.image_url) {
        score += 2;
      }
      
      return { article, score };
    });
    
    const sorted = scoredArticles
      .sort((a, b) => b.score - a.score)
      .map(item => item.article);
    
    const topPicks = sorted.slice(0, 8);
    return topPicks.sort(() => Math.random() - 0.5).slice(0, 6);
  };

  const topStories = sortedByTime.slice(0, 6);
  const trendingNews = sortedBySentiment.slice(0, 6);
  const forYouArticles = getPersonalizedForYou();
  const recentNews = sortedByTime.slice(6, 12);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="space-y-8">
        {/* Top Stories Section */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-gray-900">Top stories</h2>
          </div>

          {/* Featured Article */}
          {topStories[0] && (
            <div
              onClick={() => onArticleClick(topStories[0])}
              className="bg-white rounded-lg overflow-hidden shadow-md hover:shadow-xl transition-shadow cursor-pointer mb-4"
            >
              {getImageUrl(topStories[0]) && (
                <div className="w-full h-64 overflow-hidden bg-gray-200 flex items-center justify-center">
                  {(() => {
                    const imgUrl = getImageUrl(topStories[0]);
                    console.log('🎯 Featured image URL:', imgUrl);
                    return (
                      <img
                        src={imgUrl}
                        alt={topStories[0].title}
                        onError={(e) => {
                          console.error('Featured image load error:', e);
                          console.error('Error event:', e.type);
                        }}
                        onLoad={() => console.log('✓ Featured image loaded successfully')}
                        className="w-full h-full object-cover"
                      />
                    );
                  })()}
                </div>
              )}
              <div className="p-4">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs font-medium text-gray-600">{getSourceName(topStories[0])}</span>
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-2 hover:text-blue-600 transition-colors">
                  {topStories[0].title}
                </h3>
                <p className="text-sm text-gray-600">
                  {getTimeAgo(topStories[0].publish_time || topStories[0].published_at)}
                  {topStories[0].author && ` · By ${topStories[0].author}`}
                </p>
              </div>
            </div>
          )}

          {/* Other Top Stories Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {topStories.slice(1).map((article) => (
              <div
                key={article._id}
                onClick={() => onArticleClick(article)}
                className="bg-white rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow cursor-pointer flex gap-3"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-medium text-gray-600">{getSourceName(article)}</span>
                  </div>
                  <h3 className="text-sm font-semibold text-gray-900 mb-1 hover:text-blue-600 transition-colors line-clamp-2">
                    {article.title}
                  </h3>
                  <p className="text-xs text-gray-500">
                    {getTimeAgo(article.publish_time || article.published_at)}
                  </p>
                </div>
                {getImageUrl(article) && (
                  <div className="w-20 h-20 flex-shrink-0 rounded overflow-hidden">
                    <img
                      src={getImageUrl(article)}
                      alt={article.title}
                      className="w-full h-full object-cover"
                    />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="border-t border-gray-200"></div>

        {/* Trending Now Section */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-gray-900">Trending now</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {trendingNews.map((article) => (
              <div
                key={article._id}
                onClick={() => onArticleClick(article)}
                className="bg-white rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow cursor-pointer"
              >
                <div className="flex gap-3">
                  {getImageUrl(article) && (
                    <div className="w-20 h-20 flex-shrink-0 rounded overflow-hidden">
                      <img
                        src={getImageUrl(article)}
                        alt={article.title}
                        crossOrigin="anonymous"
                        className="w-full h-full object-cover"
                      />
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-medium text-gray-600">{getSourceName(article)}</span>
                    </div>
                    <h3 className="text-sm font-semibold text-gray-900 mb-1 hover:text-blue-600 transition-colors line-clamp-2">
                      {article.title}
                    </h3>
                    <p className="text-xs text-gray-500">
                      {getTimeAgo(article.publish_time || article.published_at)}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="border-t border-gray-200"></div>

        {/* AI Picks Section */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-gray-900">AI Picks</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {forYouArticles.map((article) => (
              <div
                key={article._id}
                onClick={() => onArticleClick(article)}
                className="bg-white rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow cursor-pointer"
              >
                <div className="flex gap-3">
                  {getImageUrl(article) && (
                    <div className="w-20 h-20 flex-shrink-0 rounded overflow-hidden">
                      <img
                        src={getImageUrl(article)}
                        alt={article.title}
                        crossOrigin="anonymous"
                        className="w-full h-full object-cover"
                      />
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-medium text-gray-600">{getSourceName(article)}</span>
                    </div>
                    <h3 className="text-sm font-semibold text-gray-900 mb-1 hover:text-blue-600 transition-colors line-clamp-2">
                      {article.title}
                    </h3>
                    <p className="text-xs text-gray-500">
                      {getTimeAgo(article.publish_time || article.published_at)}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="border-t border-gray-200"></div>

        {/* Recent News Section */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-gray-900">Latest news</h2>
          </div>
          <div className="space-y-3">
            {recentNews.map((article) => (
              <div
                key={article._id}
                onClick={() => onArticleClick(article)}
                className="bg-white rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow cursor-pointer flex gap-4"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <div className="w-5 h-5 bg-blue-100 rounded flex items-center justify-center">
                      <span className="text-xs font-bold text-blue-600">{getSourceName(article).charAt(0)}</span>
                    </div>
                    <span className="text-xs font-medium text-gray-600">{getSourceName(article)}</span>
                  </div>
                  <h3 className="text-base font-semibold text-gray-900 mb-1 hover:text-blue-600 transition-colors line-clamp-2">
                    {article.title}
                  </h3>
                  <p className="text-xs text-gray-500">
                    {getTimeAgo(article.publish_time || article.published_at)}
                  </p>
                </div>
                {getImageUrl(article) && (
                  <div className="w-24 h-24 flex-shrink-0 rounded overflow-hidden">
                    <img
                      src={getImageUrl(article)}
                      alt={article.title}
                      crossOrigin="anonymous"
                      className="w-full h-full object-cover"
                    />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

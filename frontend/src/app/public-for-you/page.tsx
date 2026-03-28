'use client';

import { useState, useEffect } from 'react';
import ForYouLayout from '@/components/ForYouLayout';
import { NewsArticle } from '@/types';

export default function PublicForYouPage() {
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchArticles = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/news/');
        if (response.ok) {
          const data = await response.json();
          const articlesData = (data.results || data) as NewsArticle[];
          
          // Sort by publish_time
          const sorted = articlesData.sort((a, b) => {
            const timeA = new Date(a.publish_time || a.published_at || 0).getTime();
            const timeB = new Date(b.publish_time || b.published_at || 0).getTime();
            return timeB - timeA;
          });
          
          setArticles(sorted);
          console.log('✓ Loaded articles:', sorted.length);
          console.log('✓ First article image:', sorted[0]?.image_url);
        }
      } catch (error) {
        console.error('Error fetching articles:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchArticles();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl">Loading articles...</div>
      </div>
    );
  }

  return (
    <div className="bg-gray-50 min-h-screen">
      <div className="max-w-6xl mx-auto px-4 py-8">
        <h1 className="text-4xl font-bold mb-8">For You (Public Test)</h1>
        <ForYouLayout
          articles={articles}
          onArticleClick={(article) => {
            console.log('Article clicked:', article.title);
          }}
        />
      </div>
    </div>
  );
}

'use client';

import { useState, useEffect } from 'react';

interface Article {
  _id: string;
  title: string;
  image_url: string;
  publish_time: string;
}

export default function TestImagesPage() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchArticles = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/news/');
        if (response.ok) {
          const data = await response.json();
          const articlesData = data.results || data;
          setArticles(articlesData.slice(0, 6)); // Get first 6 articles
          console.log('✓ Loaded articles:', articlesData.length);
          console.log('✓ First article:', articlesData[0]);
        }
      } catch (error) {
        console.error('Error fetching articles:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchArticles();
  }, []);

  const getProxyUrl = (imageUrl: string) => {
    const backendUrl = 'http://localhost:8000/api';
    return `${backendUrl}/news/proxy-image/?url=${encodeURIComponent(imageUrl)}`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <h1 className="text-4xl font-bold mb-8 text-gray-900">Image Proxy Test</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {articles.map((article) => (
          <div key={article._id} className="bg-white rounded-lg shadow-md overflow-hidden">
            <div className="w-full h-48 bg-gray-200 overflow-hidden">
              {article.image_url ? (
                <>
                  <img
                    src={getProxyUrl(article.image_url)}
                    alt={article.title}
                    className="w-full h-full object-cover"
                    onLoad={() => console.log('✓ Image loaded:', article._id)}
                    onError={(e) => console.error('✗ Image failed:', article._id, e)}
                  />
                </>
              ) : (
                <div className="w-full h-full flex items-center justify-center text-gray-500">
                  No Image
                </div>
              )}
            </div>
            <div className="p-4">
              <h2 className="font-bold text-gray-900 mb-2 line-clamp-2">
                {article.title}
              </h2>
              <p className="text-xs text-gray-500">
                {new Date(article.publish_time).toLocaleString()}
              </p>
              <p className="text-xs text-gray-400 mt-2 line-clamp-1">
                {article.image_url?.substring(0, 50)}...
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

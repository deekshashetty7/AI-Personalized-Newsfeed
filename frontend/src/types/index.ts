export interface NewsArticle {
  _id: string;
  title: string;
  summary: string;
  content?: string;
  category: string;
  source?: string;
  source_id?: string;
  publish_time: string;
  published_at?: string;
  sentiment_score: number;
  image_url?: string;
  is_spam?: boolean;
  url?: string;
  author?: string;
  is_liked?: boolean;
  is_disliked?: boolean;
  is_saved?: boolean;
}

export interface User {
  _id: string;
  name: string;
  email: string;
  interests: string[];
  profile_photo?: string;
  streak_days: number;
  join_date: string;
}

export interface Interaction {
  _id: string;
  user_id: string;
  article_id: string;
  action: 'like' | 'dislike' | 'comment' | 'share' | 'save' | 'read';
  sentiment: number;
  timestamp: string;
  comment_text?: string;
}

export interface Recommendation {
  _id: string;
  user_id: string;
  article_ids: string[];
  articles: NewsArticle[];
  created_at: string;
  model_version: string;
}

'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import Header from '@/components/Header';
import LoadingSpinner from '@/components/LoadingSpinner';
import NewsCard from '@/components/NewsCard';
import ArticleModal from '@/components/ArticleModal';
import CommentSection from '@/components/CommentSection';
import { authAPI, interactionAPI, newsAPI, streakAPI } from '@/lib/api';
import { User, Mail, Calendar, Heart, Bookmark, CheckCircle, Key, ThumbsUp, MessageCircle, Share2, X, Edit } from 'lucide-react';
import { format } from 'date-fns';

// Extend window type for debugging
declare global {
  interface Window {
    lastGraphDebug?: string;
    lastChartLog?: number;
  }
}

const MAIN_INTERESTS = [
  'Technology', 'Business', 'Sports', 'Entertainment',
  'Health', 'Science', 'Environment', 'Politics'
];

const SUB_INTERESTS: Record<string, string[]> = {
  Technology: [
    'AI & Machine Learning', 'Cybersecurity', 'Gadgets & Hardware', 'Space Tech',
    'Software Development', 'Cloud Computing', 'Blockchain & Crypto', 'Mobile Technology',
    '5G & Networking', 'Virtual Reality'
  ],
  Business: [
    'Stock Market', 'Cryptocurrency', 'Startups', 'E-commerce', 'Marketing',
    'Finance', 'Real Estate', 'Economics', 'Leadership', 'Entrepreneurship'
  ],
  Sports: [
    'Football', 'Basketball', 'Cricket', 'Tennis', 'Olympics',
    'Fitness', 'Motorsports', 'Golf', 'Esports', 'Extreme Sports'
  ],
  Entertainment: [
    'Movies', 'TV Shows', 'Music', 'Gaming', 'Celebrity News',
    'Fashion', 'Art & Culture', 'Books', 'Theater', 'Streaming'
  ],
  Health: [
    'Nutrition', 'Mental Health', 'Fitness & Exercise', 'Medical Research', 'Wellness',
    'Alternative Medicine', 'Public Health', 'Diet Plans', 'Yoga & Meditation', 'Healthcare Technology'
  ],
  Science: [
    'Physics', 'Biology', 'Chemistry', 'Astronomy', 'Climate Science',
    'Neuroscience', 'Genetics', 'Mathematics', 'Research & Innovation', 'Environmental Science'
  ],
  Environment: [
    'Climate Change', 'Renewable Energy', 'Conservation', 'Sustainability', 'Wildlife',
    'Pollution', 'Green Technology', 'Ocean Health', 'Deforestation', 'Recycling'
  ],
  Politics: [
    'Elections', 'Government Policy', 'International Relations', 'Law', 'Human Rights',
    'Immigration', 'Defense', 'Social Issues', 'Political Analysis', 'Activism'
  ]
};

const CATEGORIES = [
  'Technology', 'Business', 'Sports', 'Entertainment',
  'Health', 'Science', 'Environment', 'Politics', 'General'
];

function ProfilePage() {
  const router = useRouter();
  const { user, loading: authLoading, updateUser } = useAuth();
  
  const [editing, setEditing] = useState(false);
  const [editingProfile, setEditingProfile] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    interests: [] as string[],
    profile_photo: undefined as string | undefined,
  });
  const [stats, setStats] = useState({
    likes: 0,
    saved: 0,
    total: 0,
  });
  const [loading, setLoading] = useState(true);
  const [articles, setArticles] = useState<any[]>([]);
  const [loadingArticles, setLoadingArticles] = useState(false);
  const [selectedArticle, setSelectedArticle] = useState<any>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [showSubInterests, setShowSubInterests] = useState(false);
  const [selectedMainCategory, setSelectedMainCategory] = useState<string | null>(null);
  const [tempSubInterests, setTempSubInterests] = useState<string[]>([]);
  const [showPasswordChange, setShowPasswordChange] = useState(false);
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });
  const [passwordError, setPasswordError] = useState('');
  const [changingPassword, setChangingPassword] = useState(false);
  const [expandedCategory, setExpandedCategory] = useState<string | null>(null);
  const [showingSavedArticles, setShowingSavedArticles] = useState(false);
  const [showingRecentlyRead, setShowingRecentlyRead] = useState(false);
  const [articleStates, setArticleStates] = useState<Record<string, { liked: boolean; saved: boolean }>>({});
  const [showCommentModal, setShowCommentModal] = useState<string | null>(null);
  const [streakDays, setStreakDays] = useState<number>(0);
  const [showPersonalizationSettings, setShowPersonalizationSettings] = useState(false);
  const [timeStats, setTimeStats] = useState({
    today: 0,
    thisWeek: 0,
    allTime: 0,
    last7Days: [0, 0, 0, 0, 0, 0, 0]
  });
  const [currentSessionTime, setCurrentSessionTime] = useState<number>(0);
  const personalizationRef = useRef<HTMLDivElement>(null);
  const [showActivityDashboard, setShowActivityDashboard] = useState(false);
  const activityDashboardRef = useRef<HTMLDivElement>(null);
  const recentlyReadRef = useRef<HTMLDivElement>(null);
  const savedArticlesRef = useRef<HTMLDivElement>(null);

  // Helper function to get proper source name
  const getSourceName = (source: string | undefined) => {
    if (!source) return 'News';
    // For Reddit sources, display only "Reddit"
    if (source.toLowerCase().includes('reddit')) {
      return 'Reddit';
    }
    return source;
  };

  // Close activity dashboard when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (activityDashboardRef.current && !activityDashboardRef.current.contains(event.target as Node)) {
        setShowActivityDashboard(false);
      }
    };
    if (showActivityDashboard) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showActivityDashboard]);

  // Close recently read when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (recentlyReadRef.current && !recentlyReadRef.current.contains(event.target as Node)) {
        setShowingRecentlyRead(false);
        if (!showingSavedArticles) {
          fetchPersonalizedArticles();
        }
      }
    };
    if (showingRecentlyRead) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showingRecentlyRead, showingSavedArticles]);

  // Close saved articles when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (savedArticlesRef.current && !savedArticlesRef.current.contains(event.target as Node)) {
        setShowingSavedArticles(false);
        if (!showingRecentlyRead) {
          fetchPersonalizedArticles();
        }
      }
    };
    if (showingSavedArticles) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showingSavedArticles, showingRecentlyRead]);
  // Close personalization settings when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (personalizationRef.current && !personalizationRef.current.contains(event.target as Node)) {
        setShowPersonalizationSettings(false);
      }
    };

    if (showPersonalizationSettings) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showPersonalizationSettings]);

  // Simple time tracking from login to logout
  useEffect(() => {
    if (!user) {
      setCurrentSessionTime(0);
      return;
    }

    const updateSessionTime = () => {
      const startTime = localStorage.getItem('session_start_time');
      if (startTime) {
        const elapsed = Math.floor((Date.now() - parseInt(startTime)) / 1000);
        setCurrentSessionTime(elapsed);
        
        // Log every 30 seconds
        if (elapsed % 30 === 0 && elapsed > 0) {
          console.log('⏱️ Session time:', elapsed, 'seconds =', Math.floor(elapsed / 60), 'minutes');
        }
      }
    };

    updateSessionTime();
    const interval = setInterval(updateSessionTime, 1000);

    return () => clearInterval(interval);
  }, [user]);

  // Periodically refresh user profile and time stats
  useEffect(() => {
    if (!user) return;

    const refreshProfile = async () => {
      try {
        const response = await authAPI.getProfile();
        updateUser(response.data);
      } catch (error) {
        console.error('Failed to refresh profile:', error);
      }
    };

    const refreshTimeStats = async () => {
      try {
        await calculateTimeStats();
        console.log('🔄 Time stats refreshed');
      } catch (error) {
        console.error('Failed to refresh time stats:', error);
      }
    };

    // Refresh profile every 2 minutes
    const profileInterval = setInterval(refreshProfile, 120000);
    // Refresh time stats every 30 seconds for real-time updates
    const statsInterval = setInterval(refreshTimeStats, 30000);

    return () => {
      clearInterval(profileInterval);
      clearInterval(statsInterval);
    };
  }, [user]);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login');
      return;
    }

    if (user) {
      setFormData({
        name: user.name,
        interests: user.interests || [],
        profile_photo: user.profile_photo || undefined,
      });
      setPhotoPreview(user.profile_photo || null);
      fetchStats();
      fetchPersonalizedArticles();
      fetchStreak();
      calculateTimeStats();
    }
  }, [authLoading, user]);

  const calculateTimeStats = async () => {
    try {
      // Fetch real session data from backend
      const sessionResponse = await authAPI.getSessionData();
      const sessionData = sessionResponse.data;
      
      console.log('📊 Session data from backend:', sessionData);
      
      // Get daily activity breakdown
      const dailyActivity = sessionData.daily_activity || {};
      
      // Calculate current session time from login
      const sessionStart = localStorage.getItem('session_start_time');
      let currentSessionSeconds = 0;
      
      if (sessionStart) {
        currentSessionSeconds = Math.floor((Date.now() - parseInt(sessionStart)) / 1000);
      }
      
      const currentSessionMinutes = Math.floor(currentSessionSeconds / 60);
      
      console.log('📊 Current session time:', currentSessionSeconds, 'seconds =', currentSessionMinutes, 'minutes');
      
      // Get today's date
      const now = new Date();
      const todayStr = now.toISOString().split('T')[0];
      
      // Initialize array for last 7 days [Mon, Tue, Wed, Thu, Fri, Sat, Sun]
      const dailyMinutes = [0, 0, 0, 0, 0, 0, 0];
      
      // Get today's day of week (0=Sunday, 1=Monday, ..., 6=Saturday)
      const todayDayOfWeek = now.getDay();
      // Convert to our array index (0=Monday, 6=Sunday)
      const todayIndex = todayDayOfWeek === 0 ? 6 : todayDayOfWeek - 1;
      
      // Fill in the last 7 days
      let weekTotal = 0;
      for (let i = 6; i >= 0; i--) {
        const date = new Date(now);
        date.setDate(date.getDate() - i);
        const dateStr = date.toISOString().split('T')[0];
        const dayOfWeek = date.getDay();
        const dayIndex = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
        
        let minutes = Math.floor((dailyActivity[dateStr] || 0) / 60);
        
        // Add current session time to today
        if (i === 0) {
          minutes += currentSessionMinutes;
        }
        
        dailyMinutes[dayIndex] = minutes;
        weekTotal += minutes;
      }
      
      // Today's total (from backend + current session)
      const todayMinutes = Math.floor((dailyActivity[todayStr] || 0) / 60) + currentSessionMinutes;
      
      // All time from backend + current session (to ensure it's >= this week)
      const allTimeMinutes = Math.floor((sessionData.total_active_time || 0) / 60) + currentSessionMinutes;
      
      // Ensure allTime is at least as much as thisWeek
      const finalAllTime = Math.max(allTimeMinutes, weekTotal);
      
      // Log detailed stats for debugging
      const statsLog = {
        todayMinutes,
        weekMinutes: weekTotal,
        allTimeMinutes: finalAllTime,
        rawAllTime: allTimeMinutes,
        dailyMinutes,
        todayIndex,
        todayName: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][todayIndex],
        currentSessionMinutes,
        totalDailyMinutes: dailyMinutes.reduce((sum, m) => sum + m, 0),
        maxDailyMinutes: Math.max(...dailyMinutes)
      };
      console.log('📊 Time stats calculated:', statsLog);
      
      // Log each day's minutes for clarity
      ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].forEach((day, idx) => {
        if (dailyMinutes[idx] > 0) {
          console.log(`  ${day}: ${dailyMinutes[idx]} minutes${idx === todayIndex ? ' ← TODAY' : ''}`);
        }
      });
      
      setTimeStats({
        today: todayMinutes,
        thisWeek: weekTotal,
        allTime: finalAllTime,
        last7Days: dailyMinutes
      });
    } catch (error) {
      console.error('Error calculating time stats:', error);
      // Use fallback data if API fails
      const allTimeMinutes = user?.active_time ? Math.floor(user.active_time / 60) : 0;
      setTimeStats({
        today: 0,
        thisWeek: 0,
        allTime: allTimeMinutes,
        last7Days: [0, 0, 0, 0, 0, 0, 0]
      });
    }
  };

  const fetchStats = async () => {
    try {
      const [likesRes, savedRes, allRes] = await Promise.all([
        interactionAPI.getUserInteractions('like'),
        interactionAPI.getUserInteractions('save'),
        interactionAPI.getUserInteractions(),
      ]);

      console.log('📊 Saved interactions from backend:', savedRes.data);
      console.log('📊 Total saved interactions:', savedRes.data.length);

      // Count unique saved articles (remove duplicates)
      const uniqueSavedArticles = new Set(savedRes.data.map((interaction: any) => interaction.article_id));
      
      console.log('📊 Unique saved articles:', uniqueSavedArticles.size);
      console.log('📊 Article IDs:', Array.from(uniqueSavedArticles));

      setStats({
        likes: likesRes.data.length,
        saved: uniqueSavedArticles.size,
        total: allRes.data.length,
      });
    } catch (error) {
      console.error('Error fetching stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchPersonalizedArticles = async () => {
    try {
      setLoadingArticles(true);
      const response = await newsAPI.getArticles({
        unlimited: true,
        page_size: 50
      });

      let filteredArticles: any[] = [];
      if (user?.interests && user.interests.length > 0) {
        filteredArticles = response.data.filter((article: any) =>
          user.interests.some((interest: string) =>
            article.category && article.category.toLowerCase() === interest.toLowerCase()
          )
        );
      }

      // If no interests or no matches, show all articles
      const articlesToDisplay = filteredArticles.length > 0 ? filteredArticles : response.data;
      
      // Sort by publish_time (latest first)
      const sortedArticles = articlesToDisplay.sort((a: any, b: any) => {
        const dateA = new Date(a.publish_time || a.published_at || 0).getTime();
        const dateB = new Date(b.publish_time || b.published_at || 0).getTime();
        return dateB - dateA;
      });
      
      setArticles(sortedArticles);
    } catch (error) {
      console.error('Error fetching personalized articles:', error);
    } finally {
      setLoadingArticles(false);
    }
  };

  const fetchRecentlyReadArticles = async () => {
    try {
      console.log('📖 Fetching recently read articles...');
      setLoadingArticles(true);
      setShowingRecentlyRead(true);
      setShowingSavedArticles(false);

      // Get all read interactions (articles that were viewed in modal)
      const readRes = await interactionAPI.getUserInteractions('read');
      console.log('📊 Read interactions received:', readRes.data.length);
      
      // Get unique article IDs (remove duplicates from multiple read sessions)
      const uniqueArticleIds = Array.from(new Set(
        readRes.data.map((interaction: any) => interaction.article_id)
      ));
      
      // Sort by most recent interaction for each article
      const articleLastRead = new Map();
      readRes.data.forEach((interaction: any) => {
        const currentTime = articleLastRead.get(interaction.article_id);
        const newTime = new Date(interaction.timestamp).getTime();
        if (!currentTime || newTime > currentTime) {
          articleLastRead.set(interaction.article_id, newTime);
        }
      });
      
      const readArticleIds = Array.from(articleLastRead.entries())
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .map(([id]) => id);
      
      console.log('📋 Recently read article IDs:', readArticleIds);

      if (readArticleIds.length === 0) {
        console.log('⚠️ No recently read articles found');
        setArticles([]);
        setLoadingArticles(false);
        return;
      }

      // Fetch full article details
      const allArticlesRes = await newsAPI.getArticles({ page_size: 500, unlimited: true });
      const allArticles = allArticlesRes.data.results || allArticlesRes.data || [];
      
      // Filter to only read articles, maintaining order
      const readArticles = readArticleIds
        .map((id: string) => allArticles.find((article: any) => article._id === id))
        .filter((article: any) => article !== undefined)
        .sort((a: any, b: any) => {
          // Sort by publish_time (latest first)
          const dateA = new Date(a.publish_time || a.published_at || 0).getTime();
          const dateB = new Date(b.publish_time || b.published_at || 0).getTime();
          return dateB - dateA;
        });

      setArticles(readArticles);

      // Set article states
      const states: Record<string, { liked: boolean; saved: boolean }> = {};
      readArticles.forEach((article: any) => {
        states[article._id] = { liked: false, saved: false };
      });

      // Check which are liked
      const likesRes = await interactionAPI.getUserInteractions('like');
      const likedArticleIds = likesRes.data.map((interaction: any) => interaction.article_id);
      likedArticleIds.forEach((id: string) => {
        if (states[id]) {
          states[id].liked = true;
        }
      });

      // Check which are saved
      const savedRes = await interactionAPI.getUserInteractions('save');
      const savedArticleIds = savedRes.data.map((interaction: any) => interaction.article_id);
      savedArticleIds.forEach((id: string) => {
        if (states[id]) {
          states[id].saved = true;
        }
      });

      setArticleStates(states);
      setLoadingArticles(false);
    } catch (error) {
      console.error('Error fetching recently read articles:', error);
      setLoadingArticles(false);
    }
  };

  const fetchSavedArticles = async () => {
    try {
      setLoadingArticles(true);
      setShowingSavedArticles(true);
      setShowingRecentlyRead(false);

      // Get saved interactions
      const savedRes = await interactionAPI.getUserInteractions('save');
      // Get unique article IDs only (remove duplicates)
      const savedArticleIds = [...new Set(savedRes.data.map((interaction: any) => interaction.article_id))];
      
      console.log('📊 Fetching saved articles. IDs:', savedArticleIds);
      
      if (savedArticleIds.length === 0) {
        setArticles([]);
        setLoadingArticles(false);
        return;
      }
      
      // Fetch all articles (use large page_size to include old saved articles)
      const response = await newsAPI.getArticles({
        unlimited: true,
        page_size: 1000
      });
      
      console.log('📰 Total articles fetched:', response.data.length);
      
      const savedArticles = response.data.filter((article: any) =>
        savedArticleIds.includes(article._id)
      ).sort((a: any, b: any) => {
        // Sort by publish_time (latest first)
        const dateA = new Date(a.publish_time || a.published_at || 0).getTime();
        const dateB = new Date(b.publish_time || b.published_at || 0).getTime();
        return dateB - dateA;
      });
      
      console.log('✅ Saved articles found:', savedArticles.length);
      
      setArticles(savedArticles);
      
      // Initialize article states (all are saved by default)
      const states: Record<string, { liked: boolean; saved: boolean }> = {};
      savedArticles.forEach((article: any) => {
        states[article._id] = { liked: false, saved: true };
      });
      setArticleStates(states);
      
      // Check for likes
      const likesRes = await interactionAPI.getUserInteractions('like');
      const likedArticleIds = likesRes.data.map((interaction: any) => interaction.article_id);
      likedArticleIds.forEach((id: string) => {
        if (states[id]) {
          states[id].liked = true;
        }
      });
      setArticleStates({...states});
    } catch (error) {
      console.error('Error fetching saved articles:', error);
    } finally {
      setLoadingArticles(false);
    }
  };

  const fetchStreak = async () => {
    try {
      const res = await streakAPI.getUserStreak();
      setStreakDays(res.data.streak_days || 0);
    } catch (error) {
      setStreakDays(0);
    }
  };

  const handleInteraction = async (articleId: string, action: string) => {
    try {
      const currentState = articleStates[articleId];
      const isCurrentlyActive = action === 'like' ? currentState?.liked : currentState?.saved;
      
      if (isCurrentlyActive) {
        // Remove the interaction
        await interactionAPI.remove(articleId, action);
      } else {
        // Add the interaction
        await interactionAPI.recordInteraction(articleId, action);
      }
      
      if (action === 'like') {
        setArticleStates(prev => ({
          ...prev,
          [articleId]: { ...prev[articleId], liked: !prev[articleId]?.liked }
        }));
      } else if (action === 'save') {
        setArticleStates(prev => ({
          ...prev,
          [articleId]: { ...prev[articleId], saved: !prev[articleId]?.saved }
        }));
        // Refresh saved articles list and stats after a delay
        setTimeout(() => {
          fetchSavedArticles();
          fetchStats();
        }, 500);
      }
    } catch (error) {
      console.error('Error recording interaction:', error);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setSaveMessage(null);
      
      console.log('📝 Updating profile with data:', formData);
      
      // Update profile on backend
      const response = await authAPI.updateProfile(formData);
      console.log('✅ Profile updated successfully:', response.data);
      
      // Update local user context with fresh data from server
      updateUser(response.data);
      
      // Show success message
      setSaveMessage({ type: 'success', text: 'Profile updated successfully!' });
      
      // Exit edit mode
      setEditingProfile(false);
      
      // Refresh personalized articles if interests changed
      if (JSON.stringify(formData.interests) !== JSON.stringify(user?.interests)) {
        fetchPersonalizedArticles();
      }
      
      // Clear success message after 3 seconds
      setTimeout(() => setSaveMessage(null), 3000);
      
    } catch (error: any) {
      console.error('❌ Error updating profile:', error);
      console.error('❌ Error response:', error.response?.data);
      
      const errorMessage = error.response?.data?.error || 
                           error.response?.data?.message ||
                           'Failed to update profile. Please try again.';
      
      setSaveMessage({ type: 'error', text: errorMessage });
    } finally {
      setSaving(false);
    }
  };

  const toggleInterest = (interest: string) => {
    setFormData(prev => ({
      ...prev,
      interests: prev.interests.includes(interest)
        ? prev.interests.filter(i => i !== interest)
        : [...prev.interests, interest]
    }));
  };

  const handleMainCategoryClick = async (category: string) => {
    const isSelected = formData.interests.includes(category);
    
    if (isSelected) {
      // Remove the category
      const updatedInterests = formData.interests.filter(i => i !== category);
      setFormData(prev => ({ ...prev, interests: updatedInterests }));
      
      // Immediately save to backend
      try {
        const response = await authAPI.updateProfile({ interests: updatedInterests });
        updateUser(response.data);
        setSaveMessage({ type: 'success', text: `${category} removed successfully!` });
        setTimeout(() => setSaveMessage(null), 3000);
        fetchPersonalizedArticles();
      } catch (error) {
        console.error('Error removing category:', error);
        setSaveMessage({ type: 'error', text: 'Failed to remove category' });
      }
    } else {
      // Show subcategory selection modal
      setSelectedMainCategory(category);
      setTempSubInterests([]);
      setShowSubInterests(true);
    }
  };

  const handleSubInterestToggle = (subInterest: string) => {
    setTempSubInterests(prev => 
      prev.includes(subInterest)
        ? prev.filter(i => i !== subInterest)
        : [...prev, subInterest]
    );
  };

  const handleAddSubInterests = async () => {
    // Add main category and selected sub-interests
    const newInterests = [selectedMainCategory!, ...tempSubInterests];
    const updatedInterests = [...new Set([...formData.interests, ...newInterests])];
    
    setFormData(prev => ({
      ...prev,
      interests: updatedInterests
    }));
    
    // Immediately save to backend
    try {
      const response = await authAPI.updateProfile({ interests: updatedInterests });
      updateUser(response.data);
      setSaveMessage({ 
        type: 'success', 
        text: `${selectedMainCategory} ${tempSubInterests.length > 0 ? `with ${tempSubInterests.length} subcategories` : ''} added successfully!` 
      });
      setTimeout(() => setSaveMessage(null), 3000);
      fetchPersonalizedArticles();
    } catch (error) {
      console.error('Error adding interests:', error);
      setSaveMessage({ type: 'error', text: 'Failed to add interests' });
    }
    
    setShowSubInterests(false);
    setSelectedMainCategory(null);
    setTempSubInterests([]);
  };

  const handleChangePassword = async () => {
    // Validate passwords
    if (!passwordData.currentPassword || !passwordData.newPassword || !passwordData.confirmPassword) {
      setPasswordError('All fields are required');
      return;
    }

    if (passwordData.newPassword.length < 6) {
      setPasswordError('New password must be at least 6 characters');
      return;
    }

    if (passwordData.newPassword !== passwordData.confirmPassword) {
      setPasswordError('New passwords do not match');
      return;
    }

    try {
      setChangingPassword(true);
      setPasswordError('');

      await authAPI.changePassword({
        old_password: passwordData.currentPassword,
        new_password: passwordData.newPassword
      });

      setSaveMessage({ type: 'success', text: 'Password changed successfully!' });
      setShowPasswordChange(false);
      setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' });
      
      setTimeout(() => setSaveMessage(null), 3000);
    } catch (error: any) {
      console.error('Error changing password:', error);
      const errorMessage = error.response?.data?.error || 
                          error.response?.data?.message ||
                          'Failed to change password. Please check your current password.';
      setPasswordError(errorMessage);
    } finally {
      setChangingPassword(false);
    }
  };

  const handlePhotoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Check file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      setSaveMessage({ type: 'error', text: 'Image size should be less than 5MB' });
      return;
    }

    // Check file type
    if (!file.type.startsWith('image/')) {
      setSaveMessage({ type: 'error', text: 'Please upload an image file' });
      return;
    }

    setUploadingPhoto(true);
    
    try {
      // Convert to base64
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64String = reader.result as string;
        setPhotoPreview(base64String);
        setFormData(prev => ({ ...prev, profile_photo: base64String }));
        setUploadingPhoto(false);
      };
      reader.onerror = () => {
        setSaveMessage({ type: 'error', text: 'Failed to read image file' });
        setUploadingPhoto(false);
      };
      reader.readAsDataURL(file);
    } catch (error) {
      console.error('Error uploading photo:', error);
      setSaveMessage({ type: 'error', text: 'Failed to upload photo' });
      setUploadingPhoto(false);
    }
  };

  const handleReadMore = (article: any) => {
    setSelectedArticle(article);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedArticle(null);
  };

  if (authLoading || loading) {
    return <div className="min-h-screen bg-background"><Header /><LoadingSpinner /></div>;
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Profile Header Card */}
        <div className="bg-white rounded-xl shadow-md overflow-hidden mb-8">
          <div className="px-6 sm:px-8 py-8">
            {/* Profile Photo & Info */}
            <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between">
              <div className="flex flex-col sm:flex-row items-center sm:items-start space-y-4 sm:space-y-0 sm:space-x-6">
                {/* Profile Photo */}
                <div className="relative">
                  <div className="w-24 h-24 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center overflow-hidden">
                    {(photoPreview || user?.profile_photo) ? (
                      <img 
                        src={photoPreview || user?.profile_photo} 
                        alt={user?.name}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <User className="w-12 h-12 text-white" />
                    )}
                    {uploadingPhoto && (
                      <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center">
                        <svg className="animate-spin h-6 w-6 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                      </div>
                    )}
                  </div>
                  {editingProfile && (
                    <label className="absolute -bottom-1 -right-1 w-8 h-8 bg-primary rounded-full flex items-center justify-center cursor-pointer hover:bg-primary-dark transition-colors">
                      <input
                        type="file"
                        accept="image/*"
                        onChange={handlePhotoUpload}
                        className="hidden"
                        disabled={uploadingPhoto}
                      />
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-white" viewBox="0 0 20 20" fill="currentColor">
                        <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
                      </svg>
                    </label>
                  )}
                  {!editingProfile && (
                    <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-green-500 rounded-full border-2 border-white"></div>
                  )}
                </div>
                
                {/* User Info */}
                <div className="text-center sm:text-left pb-2">
                  {editingProfile ? (
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="text-3xl font-bold text-text mb-2 border-2 border-primary rounded-lg px-3 py-1 focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                  ) : (
                    <h1 className="text-3xl font-bold text-text mb-2">{user?.name}</h1>
                  )}
                  <div className="flex flex-col sm:flex-row sm:items-center space-y-2 sm:space-y-0 sm:space-x-4 text-sm text-text-secondary">
                    <span className="flex items-center justify-center sm:justify-start">
                      <Mail className="w-4 h-4 mr-2 text-primary" />
                      <span className="font-medium">{user?.email}</span>
                    </span>
                    <span className="hidden sm:inline text-gray-300">•</span>
                    <span className="flex items-center justify-center sm:justify-start">
                      <Calendar className="w-4 h-4 mr-2 text-primary" />
                      <span>Joined {user?.join_date && format(new Date(user.join_date), 'MMM dd, yyyy')}</span>
                    </span>
                  </div>
                  {editingProfile && (
                    <div className="mt-3 flex justify-center sm:justify-start">
                      <button
                        onClick={() => setShowPasswordChange(true)}
                        className="flex items-center px-4 py-2 text-sm text-primary hover:text-secondary transition font-medium"
                      >
                        <Key className="w-4 h-4 mr-2" />
                        Change Password
                      </button>
                    </div>
                  )}
                </div>
              </div>
              
              {/* Edit Button */}
              <div className="mt-4 sm:mt-0">
                {editingProfile ? (
                  <div className="flex space-x-2">
                    <button
                      onClick={handleSave}
                      disabled={saving}
                      className="px-6 py-2.5 bg-gradient-to-r from-primary to-secondary text-white rounded-lg hover:shadow-lg transition-all duration-200 font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                    >
                      {saving ? (
                        <span className="flex items-center">
                          <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          Saving...
                        </span>
                      ) : (
                        'Save'
                      )}
                    </button>
                    <button
                      onClick={() => {
                        setEditingProfile(false);
                        setSaveMessage(null);
                        setPhotoPreview(user?.profile_photo || null);
                        setFormData({
                          name: user?.name || '',
                          interests: user?.interests || [],
                          profile_photo: user?.profile_photo || undefined,
                        });
                      }}
                      disabled={saving}
                      className="px-6 py-2.5 bg-gray-200 text-text rounded-lg hover:bg-gray-300 transition font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Cancel
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => setEditingProfile(true)}
                    className="px-6 py-2.5 bg-gradient-to-r from-primary to-secondary text-white rounded-lg hover:shadow-lg transition-all duration-200 font-medium"
                  >
                    Edit Profile
                  </button>
                )}
              </div>
            </div>

            {/* Save Message */}
            {saveMessage && (
              <div className={`mt-4 p-4 rounded-lg ${
                saveMessage.type === 'success' 
                  ? 'bg-green-50 border border-green-200 text-green-800' 
                  : 'bg-red-50 border border-red-200 text-red-800'
              } animate-slideDown`}>
                <div className="flex items-center">
                  {saveMessage.type === 'success' ? (
                    <CheckCircle className="w-5 h-5 mr-2" />
                  ) : (
                    <span className="mr-2">⚠️</span>
                  )}
                  <span className="font-medium">{saveMessage.text}</span>
                </div>
              </div>
            )}

            {/* Stats Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-4">
              <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg p-2 text-center hover:shadow-md transition">
                <div className="flex items-center justify-center mb-1">
                  <svg className="w-4 h-4 text-orange-500" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 23c-1.38 0-2.63-.56-3.53-1.47-.89-.9-1.43-2.15-1.43-3.53 0-1.38.54-2.63 1.43-3.53L12 11l3.53 3.47c.89.9 1.43 2.15 1.43 3.53 0 1.38-.54 2.63-1.43 3.53-.9.91-2.15 1.47-3.53 1.47zm0-17.5c-1.38 0-2.63-.56-3.53-1.47C7.58 3.13 7.04 1.88 7.04.5c0 1.38.54 2.63 1.43 3.53L12 7.5l3.53-3.47c.89-.9 1.43-2.15 1.43-3.53 0 1.38-.54 2.63-1.43 3.53-.9.91-2.15 1.47-3.53 1.47z" />
                  </svg>
                </div>
                <p className="text-lg font-bold text-orange-700">{streakDays}</p>
                <p className="text-[10px] text-orange-600 font-medium">Day Streak</p>
              </div>
              <div className="bg-gradient-to-br from-red-50 to-red-100 rounded-lg p-2 text-center hover:shadow-md transition">
                <div className="flex items-center justify-center mb-1">
                  <Heart className="w-4 h-4 text-red-500" />
                </div>
                <p className="text-lg font-bold text-red-700">{stats.likes}</p>
                <p className="text-[10px] text-red-600 font-medium">Liked</p>
              </div>
              <div 
                className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-2 text-center hover:shadow-md transition cursor-pointer hover:scale-105"
                onClick={fetchSavedArticles}
              >
                <div className="flex items-center justify-center mb-1">
                  <Bookmark className="w-4 h-4 text-blue-500" />
                </div>
                <p className="text-lg font-bold text-blue-700">{stats.saved}</p>
                <p className="text-[10px] text-blue-600 font-medium">Saved</p>
              </div>
              <div 
                className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-3 text-center hover:shadow-md transition cursor-pointer hover:scale-105"
                onClick={fetchRecentlyReadArticles}
              >
                <div className="flex items-center justify-center mb-2">
                  <span className="text-2xl">📖</span>
                </div>
                <p className="text-xs text-purple-600 font-medium">Recently Read</p>
              </div>
            </div>
          </div>
        </div>

        {/* Recently Read Articles Section */}
        {showingRecentlyRead && (
          <div ref={recentlyReadRef} className="bg-white rounded-xl shadow-md p-4 border border-gray-200 mt-4">
            <div className="flex items-center mb-3">
              <span className="text-xl mr-2">📖</span>
              <h2 className="text-lg font-bold text-text">Recently Read</h2>
            </div>

            {loadingArticles ? (
              <div className="flex justify-center py-8">
                <LoadingSpinner />
              </div>
            ) : articles.length === 0 ? (
              <div className="text-center py-8">
                <span className="text-5xl mb-3 block">📖</span>
                <p className="text-gray-500 text-sm">No reading history yet</p>
                <p className="text-gray-400 text-xs mt-1">Articles you read will appear here</p>
              </div>
            ) : (
              <div className="space-y-3">
                {articles.map((article) => (
                  <div
                    key={article._id}
                    className="flex gap-3 p-3 bg-gray-50 hover:bg-gray-100 rounded-lg transition border border-gray-200"
                  >
                    {article.image && (
                      <img
                        src={article.image}
                        alt={article.title}
                        className="w-24 h-24 object-cover rounded-lg flex-shrink-0 cursor-pointer"
                        onClick={() => {
                          setSelectedArticle(article);
                          setIsModalOpen(true);
                        }}
                      />
                    )}
                    <div className="flex-1 min-w-0">
                      <h3 
                        className="font-semibold text-sm text-gray-900 line-clamp-2 mb-1 cursor-pointer hover:text-primary"
                        onClick={() => {
                          setSelectedArticle(article);
                          setIsModalOpen(true);
                        }}
                      >
                        {article.title}
                      </h3>
                      <p className="text-xs text-gray-600 line-clamp-2 mb-2">
                        {article.description}
                      </p>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 text-xs text-gray-500">
                          <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded">
                            {article.category}
                          </span>
                          <span>{getSourceName(article.source)}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleInteraction(article._id, 'like');
                            }}
                            className={`p-1.5 hover:bg-gray-200 rounded-full transition ${
                              articleStates[article._id]?.liked ? 'bg-red-50' : ''
                            }`}
                            title="Like"
                          >
                            <Heart className={`w-3.5 h-3.5 ${
                              articleStates[article._id]?.liked ? 'text-red-600 fill-current' : 'text-gray-600'
                            }`} />
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleInteraction(article._id, 'save');
                            }}
                            className={`p-1.5 hover:bg-gray-200 rounded-full transition ${
                              articleStates[article._id]?.saved ? 'bg-blue-50' : ''
                            }`}
                            title={articleStates[article._id]?.saved ? 'Unsave' : 'Save'}
                          >
                            <Bookmark className={`w-3.5 h-3.5 ${
                              articleStates[article._id]?.saved ? 'text-blue-600 fill-current' : 'text-gray-600'
                            }`} />
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Saved Articles Section */}
        {showingSavedArticles && (
          <div ref={savedArticlesRef} className="bg-white rounded-xl shadow-md p-4 border border-gray-200 mt-4">
            <div className="flex items-center mb-3">
              <Bookmark className="w-5 h-5 text-blue-600 mr-2" />
              <h2 className="text-lg font-bold text-text">Saved Articles</h2>
            </div>

            {loadingArticles ? (
              <div className="flex justify-center py-8">
                <LoadingSpinner />
              </div>
            ) : articles.length === 0 ? (
              <div className="text-center py-8">
                <Bookmark className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500 text-sm">No saved articles yet</p>
                <p className="text-gray-400 text-xs mt-1">Articles you save will appear here</p>
              </div>
            ) : (
              <div className="space-y-3">
                {articles.map((article) => (
                  <div
                    key={article._id}
                    className="flex gap-3 p-3 bg-gray-50 hover:bg-gray-100 rounded-lg transition border border-gray-200"
                  >
                    {article.image && (
                      <img
                        src={article.image}
                        alt={article.title}
                        className="w-24 h-24 object-cover rounded-lg flex-shrink-0 cursor-pointer"
                        onClick={() => {
                          setSelectedArticle(article);
                          setIsModalOpen(true);
                        }}
                      />
                    )}
                    <div className="flex-1 min-w-0">
                      <h3 
                        className="font-semibold text-sm text-gray-900 line-clamp-2 mb-1 cursor-pointer hover:text-primary"
                        onClick={() => {
                          setSelectedArticle(article);
                          setIsModalOpen(true);
                        }}
                      >
                        {article.title}
                      </h3>
                      <p className="text-xs text-gray-600 line-clamp-2 mb-2">
                        {article.description}
                      </p>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 text-xs text-gray-500">
                          <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded">
                            {article.category}
                          </span>
                          <span>{getSourceName(article.source)}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleInteraction(article._id, 'like');
                            }}
                            className={`p-1.5 hover:bg-gray-200 rounded-full transition ${
                              articleStates[article._id]?.liked ? 'bg-red-50' : ''
                            }`}
                            title="Like"
                          >
                            <ThumbsUp className={`w-3.5 h-3.5 ${
                              articleStates[article._id]?.liked ? 'text-red-600 fill-current' : 'text-gray-600'
                            }`} />
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setShowCommentModal(showCommentModal === article._id ? null : article._id);
                            }}
                            className={`p-1.5 hover:bg-gray-200 rounded-full transition ${
                              showCommentModal === article._id ? 'bg-blue-50' : ''
                            }`}
                            title="Comment"
                          >
                            <MessageCircle className={`w-3.5 h-3.5 ${
                              showCommentModal === article._id ? 'text-blue-600 fill-current' : 'text-gray-600'
                            }`} />
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleInteraction(article._id, 'save');
                            }}
                            className={`p-1.5 hover:bg-gray-200 rounded-full transition ${
                              articleStates[article._id]?.saved ? 'bg-blue-50' : ''
                            }`}
                            title={articleStates[article._id]?.saved ? 'Unsave' : 'Save'}
                          >
                            <Bookmark className={`w-3.5 h-3.5 ${
                              articleStates[article._id]?.saved ? 'text-blue-600 fill-current' : 'text-gray-600'
                            }`} />
                          </button>
                          <button
                            onClick={async (e) => {
                              e.stopPropagation();
                              if (navigator.share) {
                                try {
                                  await navigator.share({
                                    title: article.title,
                                    url: article.url
                                  });
                                } catch (err) {
                                  // User cancelled share
                                }
                              } else {
                                await navigator.clipboard.writeText(article.url);
                                alert('Link copied to clipboard!');
                              }
                              handleInteraction(article._id, 'share');
                            }}
                            className="p-1.5 hover:bg-gray-200 rounded-full transition"
                            title="Share"
                          >
                            <Share2 className="w-3.5 h-3.5 text-gray-600" />
                          </button>
                        </div>
                      </div>
                    </div>
                    
                    {/* Comment Modal for this article */}
                    {showCommentModal === article._id && (
                      <div 
                        className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
                        onClick={() => setShowCommentModal(null)}
                      >
                        <div 
                          className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden"
                          onClick={(e) => e.stopPropagation()}
                        >
                          {/* Modal Header */}
                          <div className="sticky top-0 bg-gradient-to-r from-primary to-secondary text-white px-6 py-4 flex items-center justify-between">
                            <div className="flex-1 min-w-0">
                              <h3 className="font-bold text-lg line-clamp-1">{article.title}</h3>
                              <p className="text-sm text-blue-100 mt-1">{getSourceName(article.source)}</p>
                            </div>
                            <button
                              onClick={() => setShowCommentModal(null)}
                              className="ml-4 p-2 hover:bg-white/20 rounded-full transition"
                            >
                              <X className="w-5 h-5" />
                            </button>
                          </div>
                          
                          {/* Comment Section */}
                          <div className="overflow-y-auto max-h-[calc(80vh-100px)]">
                            <CommentSection 
                              articleId={article._id} 
                              onAddComment={async (commentText: string) => {
                                await interactionAPI.create({
                                  article_id: article._id,
                                  action: 'comment',
                                  comment_text: commentText
                                });
                              }}
                            />
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Personalization Settings */}
        <div ref={personalizationRef} className="bg-gradient-to-br from-white to-blue-50 rounded-2xl shadow-lg p-8 border border-blue-100 mt-6 mb-4">
          <div 
            className="flex items-center cursor-pointer hover:bg-white/50 p-4 rounded-lg transition-all -m-4"
            onClick={() => setShowPersonalizationSettings(!showPersonalizationSettings)}
          >
            <div className="w-10 h-10 bg-gradient-to-r from-primary to-secondary rounded-lg flex items-center justify-center mr-3">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <div className="flex-1">
              <h2 className="text-2xl font-bold text-text">Personalization Settings</h2>
              <p className="text-sm text-text-secondary">Customize your news feed experience</p>
            </div>
          </div>

          {/* Collapsible Content */}
          {showPersonalizationSettings && (
          <div>
          {/* Interests Section */}
          <div className="mb-6 mt-4">
            <label className="block text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-primary to-secondary mb-3">
              Your Interests
            </label>
            <p className="text-text-secondary text-sm mb-4">
              {editing 
                ? 'Click on categories to personalize your news feed'
                : 'Articles are personalized based on these interests'}
            </p>
            
            <div className="flex flex-wrap gap-2">
              {editing ? (
                // Show only main 8 categories when editing
                MAIN_INTERESTS.map((category) => {
                  const isSelected = formData.interests.includes(category);
                  
                  return (
                    <button
                      key={category}
                      onClick={() => handleMainCategoryClick(category)}
                      className={`px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 shadow-sm ${
                        isSelected
                          ? 'bg-gradient-to-r from-primary to-secondary text-white shadow-md scale-105'
                          : 'bg-white text-text border-2 border-gray-200 hover:border-primary hover:scale-105'
                      }`}
                    >
                      {isSelected ? '✓ ' : '+ '}
                      {category}
                    </button>
                  );
                })
              ) : (
                // Show only selected categories when not editing
                (user?.interests || []).length > 0 ? (
                  <div className="flex flex-wrap gap-3">
                    {(() => {
                      const mainCategories = MAIN_INTERESTS;
                      const userInterests = user?.interests || [];
                      
                      // Show only main categories
                      const mainCats = userInterests.filter(interest => mainCategories.includes(interest));
                      
                      // Display main categories only
                      return mainCats.map((category) => {
                        const isMainCategory = mainCategories.includes(category);
                        const categorySubInterests = isMainCategory 
                          ? userInterests.filter(interest => SUB_INTERESTS[category]?.includes(interest))
                          : [];
                        const hasSubcategories = categorySubInterests.length > 0;
                        
                        return (
                          <div key={category} className="relative">
                            <div
                              className="group relative px-4 py-2 rounded-full text-sm font-medium border-2 border-primary text-primary hover:bg-blue-50 cursor-pointer flex items-center gap-1 transition-all"
                              onClick={() => {
                                if (hasSubcategories) {
                                  setExpandedCategory(expandedCategory === category ? null : category);
                                }
                              }}
                            >
                              {category}
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setFormData(prev => ({
                                    ...prev,
                                    interests: prev.interests.filter(i => i !== category)
                                  }));
                                  // Immediately save after removing
                                  const updatedInterests = (user?.interests || []).filter(i => i !== category);
                                  authAPI.updateProfile({ interests: updatedInterests })
                                    .then(response => {
                                      updateUser(response.data);
                                      setSaveMessage({ type: 'success', text: 'Interest removed successfully!' });
                                      setTimeout(() => setSaveMessage(null), 3000);
                                      fetchPersonalizedArticles();
                                    })
                                    .catch(error => {
                                      console.error('Error removing interest:', error);
                                      setSaveMessage({ type: 'error', text: 'Failed to remove interest' });
                                    });
                                }}
                                className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-200 hover:bg-red-600"
                                title="Remove this interest"
                              >
                                <span className="text-white text-xs font-bold">×</span>
                              </button>
                            </div>
                            
                            {/* Subcategory Dropdown */}
                            {hasSubcategories && expandedCategory === category && (
                              <div className="absolute top-full left-0 mt-2 bg-white rounded-lg shadow-xl border-2 border-primary z-50 min-w-[200px] py-2 animate-fadeIn">
                                <div className="px-4 py-2 bg-gradient-to-r from-primary to-secondary">
                                  <p className="text-xs font-bold text-white uppercase tracking-wide">
                                    {category} Subcategories
                                  </p>
                                </div>
                                <div className="py-1 max-h-60 overflow-y-auto">
                                  {categorySubInterests.map((subCat) => (
                                    <div
                                      key={subCat}
                                      className="px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 flex items-center justify-between group"
                                    >
                                      <span>• {subCat}</span>
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          const updatedInterests = (user?.interests || []).filter(i => i !== subCat);
                                          authAPI.updateProfile({ interests: updatedInterests })
                                            .then(response => {
                                              updateUser(response.data);
                                              setSaveMessage({ type: 'success', text: 'Subcategory removed!' });
                                              setTimeout(() => setSaveMessage(null), 3000);
                                              fetchPersonalizedArticles();
                                            })
                                            .catch(error => {
                                              console.error('Error removing subcategory:', error);
                                              setSaveMessage({ type: 'error', text: 'Failed to remove subcategory' });
                                            });
                                        }}
                                        className="w-4 h-4 bg-red-500 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-600"
                                        title="Remove subcategory"
                                      >
                                        <span className="text-white text-xs">×</span>
                                      </button>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        );
                      });
                    })()}
                    <button
                      onClick={() => setEditing(true)}
                      className="px-4 py-2 rounded-full text-sm font-medium bg-gradient-to-r from-primary to-secondary text-white hover:shadow-lg transition-all duration-200 shadow-md"
                    >
                      + Add Category
                    </button>
                  </div>
                ) : (
                  <div className="w-full text-center py-8 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                    <p className="text-gray-500">No interests selected yet</p>
                    <button
                      onClick={() => setEditing(true)}
                      className="mt-2 text-primary hover:underline font-medium"
                    >
                      Add interests
                    </button>
                  </div>
                )
              )}
            </div>
            
            {/* Action Buttons when editing */}
            {editing && (
              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => {
                    setEditing(false);
                    setSaveMessage(null);
                  }}
                  className="px-6 py-2.5 bg-gray-200 text-text rounded-lg hover:bg-gray-300 transition font-medium"
                >
                  Done
                </button>
                <p className="text-sm text-gray-500 flex items-center">
                  <svg className="w-4 h-4 mr-1 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Changes are saved automatically
                </p>
              </div>
            )}
          </div>
          </div>
          )}
        </div>

        {/* Activity Dashboard */}
        <div ref={activityDashboardRef} className="bg-gradient-to-br from-white to-blue-50 rounded-2xl shadow-lg p-8 border border-blue-100 mb-6">
          <div className="cursor-pointer hover:bg-white/50 p-4 rounded-lg transition-all -m-4 flex items-center"
            onClick={() => setShowActivityDashboard(!showActivityDashboard)}>
            <div className="w-10 h-10 bg-gradient-to-r from-primary to-secondary rounded-lg flex items-center justify-center mr-3">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div className="flex-1">
              <span className="text-2xl font-bold text-text">Activity Dashboard</span>
              <p className="text-sm text-text-secondary">Track your reading habits and engagement</p>
              {user?.last_session_update && (
                <p className="text-xs text-gray-500 mt-1">
                  Last updated: {new Date(user.last_session_update).toLocaleString()}
                </p>
              )}
            </div>
          </div>
          {showActivityDashboard && (
            <div>
              {/* Reading Insights */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                {/* Today */}
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-semibold text-gray-700">Today</span>
                <svg className="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              {(() => {
                const minutes = timeStats.today;
                let display, unit;
                if (minutes >= 60) {
                  const hours = (minutes / 60).toFixed(1);
                  display = hours;
                  unit = parseFloat(hours) === 1 ? 'hour' : 'hours';
                } else {
                  display = minutes;
                  unit = minutes === 1 ? 'minute' : 'minutes';
                }
                return (
                  <div>
                    <p className="text-3xl font-bold text-blue-600 mb-1">{display}</p>
                    <p className="text-xs text-gray-600">{unit} read</p>
                    {currentSessionTime > 0 && (
                      <p className="text-[10px] text-blue-500 mt-1 flex items-center gap-1">
                        <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse"></span>
                        Active now
                      </p>
                    )}
                  </div>
                );
              })()}
            </div>

            {/* This Week */}
            <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-semibold text-gray-700">This Week</span>
                <svg className="w-5 h-5 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              {(() => {
                const minutes = timeStats.thisWeek;
                let display, unit;
                if (minutes >= 60) {
                  const hours = (minutes / 60).toFixed(1);
                  display = hours;
                  unit = parseFloat(hours) === 1 ? 'hour' : 'hours';
                } else {
                  display = minutes;
                  unit = minutes === 1 ? 'minute' : 'minutes';
                }
                return (
                  <div>
                    <p className="text-3xl font-bold text-purple-600 mb-1">{display}</p>
                    <p className="text-xs text-gray-600">{unit} read</p>
                  </div>
                );
              })()}
            </div>

            {/* All Time */}
            <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-semibold text-gray-700">All Time</span>
                <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                </svg>
              </div>
              {(() => {
                const minutes = timeStats.allTime;
                let display, unit;
                if (minutes >= 60) {
                  const hours = (minutes / 60).toFixed(1);
                  display = hours;
                  unit = parseFloat(hours) === 1 ? 'hour' : 'hours';
                } else {
                  display = minutes;
                  unit = minutes === 1 ? 'minute' : 'minutes';
                }
                return (
                  <div>
                    <p className="text-3xl font-bold text-green-600 mb-1">{display}</p>
                    <p className="text-xs text-gray-600">{unit} read</p>
                  </div>
                );
              })()}
            </div>
          </div>

          {/* Reading Streak */}

          {/* Daily Reading Chart */}
          <div className="bg-gray-50 rounded-xl p-5 border border-gray-200">
            <p className="text-sm font-bold text-gray-700 mb-4 flex items-center">
              <svg className="w-4 h-4 mr-2 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              Last 7 Days Reading Time
            </p>
            <div className="flex items-end justify-between h-64 space-x-2">
              {(() => {
                // Get today's day of week (0=Monday, 6=Sunday)
                const todayDayOfWeek = new Date().getDay();
                const todayIndex = todayDayOfWeek === 0 ? 6 : todayDayOfWeek - 1;
                
                // timeStats.last7Days already includes current session time from calculateTimeStats()
                const allMinutes = timeStats.last7Days || [0, 0, 0, 0, 0, 0, 0];
                
                const maxMinutes = Math.max(...allMinutes, 60); // Minimum scale of 60 minutes
                
                // Create unique key for React rendering
                const dataKey = allMinutes.join('-');
                
                // Debug log (only log once per minute to avoid spam)
                const currentMinute = Math.floor(Date.now() / 60000);
                if (!window.lastChartLog || window.lastChartLog !== currentMinute) {
                  console.log('📊 Profile Chart:', {
                    todayIndex,
                    day: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][todayIndex],
                    baseLast7Days: timeStats.last7Days,
                    allMinutes,
                    maxMinutes,
                    hasData: allMinutes.some(m => m > 0)
                  });
                  window.lastChartLog = currentMinute;
                }
                
                return ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day, index) => {
                  const minutes = allMinutes[index] || 0;
                  const display = minutes >= 60 ? (minutes / 60).toFixed(1) + 'h' : minutes + 'm';
                  
                  // Calculate height percentage - always show something if there's data
                  let heightPercent = 0;
                  if (minutes > 0) {
                    // Use better scaling - minimum 20% for visibility, up to 100%
                    heightPercent = Math.max(20, Math.min(100, (minutes / maxMinutes) * 100));
                  }
                  
                  // Log each bar for debugging
                  if (minutes > 0) {
                    console.log(`🔵 ${day} bar: ${minutes}min → ${heightPercent.toFixed(1)}% height`);
                  }
                  
                  return (
                    <div 
                      key={`${day}-${index}-${dataKey}`} 
                      className="flex flex-col items-center group relative" 
                      style={{ 
                        flex: 1,
                        height: '100%'
                      }}
                    >
                      <div className="w-full rounded-t-lg relative flex items-end" style={{ height: '256px', position: 'relative' }}>
                        {/* Bar - ALWAYS VISIBLE with bright colors */}
                        <div 
                          className={`w-full rounded-t-lg shadow-lg transform origin-bottom transition-all duration-500 ${
                            minutes > 0 
                              ? 'bg-gradient-to-t from-blue-500 to-blue-400 group-hover:from-blue-600 group-hover:to-blue-500 group-hover:shadow-2xl group-hover:scale-105' 
                              : 'bg-gray-200'
                          } ${index === todayIndex && minutes > 0 ? 'ring-4 ring-blue-300 ring-offset-2' : ''}`}
                          style={{ 
                            height: minutes > 0 ? `${heightPercent}%` : '8px',
                            minHeight: minutes > 0 ? '40px' : '8px',
                            willChange: 'height',
                            position: 'relative'
                          }}
                        >
                          {/* Value display inside bar */}
                          {minutes > 0 && (
                            <div className="absolute inset-0 flex items-center justify-center">
                              <span className="text-white font-bold text-xs drop-shadow-md">{display}</span>
                            </div>
                          )}
                          
                          {/* Tooltip on hover */}
                          {minutes > 0 && (
                            <div className="absolute -top-14 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white text-xs font-medium px-3 py-2 rounded-lg opacity-0 group-hover:opacity-100 group-hover:-translate-y-1 transition-all duration-300 whitespace-nowrap shadow-xl z-10 pointer-events-none">
                              <div className="flex flex-col items-center">
                                <span className="font-bold text-sm">{display}</span>
                                {index === todayIndex && currentSessionTime > 0 && (
                                  <span className="text-green-400 text-[10px] mt-0.5 flex items-center gap-1">
                                    <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse"></span>
                                    LIVE NOW
                                  </span>
                                )}
                              </div>
                              {/* Tooltip arrow */}
                              <div className="absolute -bottom-1 left-1/2 transform -translate-x-1/2 w-2 h-2 bg-gray-900 rotate-45"></div>
                            </div>
                          )}
                          
                          {/* Animated gradient overlay for current day */}
                          {index === todayIndex && minutes > 0 && (
                            <>
                              <div 
                                className="absolute inset-0 bg-gradient-to-t from-transparent via-white to-transparent opacity-20 rounded-t-lg"
                                style={{
                                  animation: 'slideDown 2s ease-in-out infinite'
                                }}
                              ></div>
                              <div className="absolute top-0 left-0 right-0 h-2 bg-yellow-300 opacity-80 rounded-t-lg"></div>
                            </>
                          )}
                        </div>
                      </div>
                      <p className={`text-xs font-semibold mt-3 transition-all duration-300 ${index === todayIndex ? 'text-indigo-600 font-bold scale-110' : 'text-gray-600'}`}>
                        {day}
                        {index === todayIndex && (
                          <span className="ml-1.5 inline-flex">
                            <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                          </span>
                        )}
                      </p>
                    </div>
                  );
                });
              })()}
            </div>
            
            {/* Show message if no activity data */}
            {timeStats.last7Days.every(m => m === 0) && (
              <div className="text-center mt-4 text-gray-500 text-sm">
                <p className="flex items-center justify-center gap-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Start using the app to see your activity
                </p>
              </div>
            )}
          </div>
          </div>
            )}
        </div>
      </main>

      {/* Sub-Interests Modal */}
      {showSubInterests && selectedMainCategory && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="sticky top-0 bg-gradient-to-r from-primary to-secondary text-white p-6 rounded-t-2xl">
              <h3 className="text-2xl font-bold">{selectedMainCategory}</h3>
              <p className="text-sm text-blue-100 mt-1">Select specific topics you're interested in</p>
            </div>
            
            <div className="p-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {SUB_INTERESTS[selectedMainCategory]?.map((subInterest) => {
                  const isSelected = tempSubInterests.includes(subInterest);
                  return (
                    <button
                      key={subInterest}
                      onClick={() => handleSubInterestToggle(subInterest)}
                      className={`p-4 rounded-lg text-left transition-all duration-200 border-2 ${
                        isSelected
                          ? 'bg-gradient-to-r from-primary to-secondary text-white border-primary shadow-lg scale-105'
                          : 'bg-gray-50 text-text border-gray-200 hover:border-primary hover:bg-gray-100'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-medium">{subInterest}</span>
                        {isSelected && (
                          <CheckCircle className="w-5 h-5 flex-shrink-0 ml-2" />
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>

              <div className="flex justify-between items-center mt-6 pt-4 border-t border-gray-200">
                <button
                  onClick={() => {
                    setShowSubInterests(false);
                    setSelectedMainCategory(null);
                    setTempSubInterests([]);
                  }}
                  className="px-6 py-2.5 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition font-medium"
                >
                  Cancel
                </button>
                <div className="flex space-x-3">
                  <button
                    onClick={async () => {
                      // Add only main category without subcategories
                      const updatedInterests = [...new Set([...formData.interests, selectedMainCategory!])];
                      setFormData(prev => ({ ...prev, interests: updatedInterests }));
                      
                      try {
                        const response = await authAPI.updateProfile({ interests: updatedInterests });
                        updateUser(response.data);
                        setSaveMessage({ type: 'success', text: `${selectedMainCategory} added successfully!` });
                        setTimeout(() => setSaveMessage(null), 3000);
                        fetchPersonalizedArticles();
                      } catch (error) {
                        console.error('Error adding category:', error);
                        setSaveMessage({ type: 'error', text: 'Failed to add category' });
                      }
                      
                      setShowSubInterests(false);
                      setSelectedMainCategory(null);
                      setTempSubInterests([]);
                    }}
                    className="px-6 py-2.5 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition font-medium"
                  >
                    Add {selectedMainCategory} Only
                  </button>
                  <button
                    onClick={handleAddSubInterests}
                    disabled={tempSubInterests.length === 0}
                    className="px-6 py-2.5 bg-gradient-to-r from-primary to-secondary text-white rounded-lg hover:shadow-lg transition font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Add with Subcategories ({tempSubInterests.length})
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Change Password Modal */}
      {showPasswordChange && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full">
            <div className="bg-gradient-to-r from-primary to-secondary text-white p-6 rounded-t-2xl">
              <h3 className="text-2xl font-bold">Change Password</h3>
              <p className="text-sm text-blue-100 mt-1">Update your account password</p>
            </div>
            
            <div className="p-6">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Current Password
                  </label>
                  <input
                    type="password"
                    value={passwordData.currentPassword}
                    onChange={(e) => setPasswordData({...passwordData, currentPassword: e.target.value})}
                    className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                    placeholder="Enter current password"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    New Password
                  </label>
                  <input
                    type="password"
                    value={passwordData.newPassword}
                    onChange={(e) => setPasswordData({...passwordData, newPassword: e.target.value})}
                    className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                    placeholder="Enter new password (min 6 characters)"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Confirm New Password
                  </label>
                  <input
                    type="password"
                    value={passwordData.confirmPassword}
                    onChange={(e) => setPasswordData({...passwordData, confirmPassword: e.target.value})}
                    className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                    placeholder="Confirm new password"
                  />
                </div>
                
                {passwordError && (
                  <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg">
                    <p className="text-sm">{passwordError}</p>
                  </div>
                )}
              </div>
              
              <div className="flex space-x-3 mt-6">
                <button
                  onClick={() => {
                    setShowPasswordChange(false);
                    setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' });
                    setPasswordError('');
                  }}
                  disabled={changingPassword}
                  className="flex-1 px-4 py-2.5 bg-gray-200 text-text rounded-lg hover:bg-gray-300 transition font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Cancel
                </button>
                <button
                  onClick={handleChangePassword}
                  disabled={changingPassword}
                  className="flex-1 px-4 py-2.5 bg-gradient-to-r from-primary to-secondary text-white rounded-lg hover:shadow-lg transition font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {changingPassword ? 'Changing...' : 'Change Password'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Article Modal */}
      <ArticleModal
        article={selectedArticle}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
      />
    </div>
  );
}

export default ProfilePage;

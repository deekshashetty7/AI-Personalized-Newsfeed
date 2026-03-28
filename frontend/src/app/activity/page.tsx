'use client';

import { useState, useEffect } from 'react';
import { ChevronLeft, Info, ChevronRight, TrendingUp, Clock, Target, Zap, Calendar } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { authAPI } from '@/lib/api';

interface DayActivity {
  day: string;
  minutes: number;
  date?: string;
}

export default function ActivityDashboard() {
  const router = useRouter();
  const { user } = useAuth();
  const [weekActivity, setWeekActivity] = useState<DayActivity[]>([
    { day: 'Mon', minutes: 0 },
    { day: 'Tue', minutes: 0 },
    { day: 'Wed', minutes: 0 },
    { day: 'Thu', minutes: 0 },
    { day: 'Fri', minutes: 0 },
    { day: 'Sat', minutes: 0 },
    { day: 'Today', minutes: 0 },
  ]);

  const [dailyLimit, setDailyLimit] = useState<number | null>(null);
  const [sleepMode, setSleepMode] = useState(false);
  const [loading, setLoading] = useState(true);
  const [currentSessionMinutes, setCurrentSessionMinutes] = useState(0);
  const [totalMinutes, setTotalMinutes] = useState(0);

  // Fetch user session data
  useEffect(() => {
    if (!user) {
      router.push('/login');
      return;
    }

    const fetchSessionData = async () => {
      try {
        const response = await authAPI.getSessionData();
        const data = response.data;
        
        // Get daily activity from backend
        const dailyActivity = data.daily_activity || {};
        
        // Calculate current session time
        const sessionStart = localStorage.getItem('session_start_time');
        let currentSessionSeconds = 0;
        
        if (sessionStart) {
          currentSessionSeconds = Math.floor((Date.now() - parseInt(sessionStart)) / 1000);
        }
        
        setCurrentSessionMinutes(Math.floor(currentSessionSeconds / 60));
        setTotalMinutes(Math.floor((data.total_active_time || 0) / 60));
        
        // Get dates for last 7 days
        const today = new Date();
        const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        const weekData: DayActivity[] = [];
        
        for (let i = 6; i >= 0; i--) {
          const date = new Date(today);
          date.setDate(date.getDate() - i);
          const dateStr = date.toISOString().split('T')[0];
          const dayName = i === 0 ? 'Today' : days[date.getDay()];
          
          let minutes = Math.floor((dailyActivity[dateStr] || 0) / 60);
          
          // Add current session to today's count
          if (i === 0) {
            minutes += Math.floor(currentSessionSeconds / 60);
          }
          
          weekData.push({ day: dayName, minutes, date: dateStr });
        }
        
        setWeekActivity(weekData);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching session data:', error);
        setLoading(false);
      }
    };

    fetchSessionData();
    
    // Update current session time every minute
    const interval = setInterval(() => {
      const sessionStart = localStorage.getItem('session_start_time');
      if (sessionStart) {
        const currentSessionSeconds = Math.floor((Date.now() - parseInt(sessionStart)) / 1000);
        const currentMinutes = Math.floor(currentSessionSeconds / 60);
        setCurrentSessionMinutes(currentMinutes);
        
        // Update today's activity in the chart
        setWeekActivity(prev => {
          const updated = [...prev];
          if (updated.length > 0) {
            // Get today's base minutes (from backend)
            const todayBase = updated[updated.length - 1].minutes - currentSessionMinutes;
            updated[updated.length - 1].minutes = todayBase + currentMinutes;
          }
          return updated;
        });
      }
    }, 60000); // Update every minute

    return () => clearInterval(interval);
  }, [user, router]);

  // Calculate average and stats
  const averageMinutes = Math.round(
    weekActivity.reduce((sum, day) => sum + day.minutes, 0) / weekActivity.length
  );

  const todayMinutes = weekActivity[weekActivity.length - 1]?.minutes || 0;
  const yesterdayMinutes = weekActivity[weekActivity.length - 2]?.minutes || 0;
  const changePercent = yesterdayMinutes > 0 
    ? Math.round(((todayMinutes - yesterdayMinutes) / yesterdayMinutes) * 100)
    : 0;

  // Format time
  const formatTime = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}m`;
  };

  // Get max value for scaling bars
  const maxMinutes = Math.max(...weekActivity.map(d => d.minutes), 1);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#0a0a0a] via-[#1a1a2e] to-[#0a0a0a] flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0a0a] via-[#1a1a2e] to-[#0a0a0a]">
      {/* Header */}
      <div className="sticky top-0 z-50 backdrop-blur-xl bg-black/30 border-b border-white/10">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <button 
              onClick={() => router.back()}
              className="text-white p-2 hover:bg-white/10 rounded-full transition-colors"
            >
              <ChevronLeft className="w-6 h-6" />
            </button>
            <h1 className="text-white text-xl font-semibold">Activity Dashboard</h1>
            <button className="text-white p-2 hover:bg-white/10 rounded-full transition-colors">
              <Info className="w-6 h-6" />
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          {/* Today's Time */}
          <div className="bg-gradient-to-br from-purple-500/20 to-pink-500/20 backdrop-blur-xl border border-purple-500/20 rounded-2xl p-6">
            <div className="flex items-center gap-3 mb-3">
              <div className="p-2 bg-purple-500/20 rounded-lg">
                <Clock className="w-5 h-5 text-purple-400" />
              </div>
              <span className="text-gray-400 text-sm font-medium">Today</span>
            </div>
            <div className="text-3xl font-bold text-white mb-1">{formatTime(todayMinutes)}</div>
            {changePercent !== 0 && (
              <div className={`flex items-center gap-1 text-sm ${changePercent > 0 ? 'text-green-400' : 'text-red-400'}`}>
                <TrendingUp className={`w-4 h-4 ${changePercent < 0 ? 'rotate-180' : ''}`} />
                <span>{Math.abs(changePercent)}% vs yesterday</span>
              </div>
            )}
          </div>

          {/* Weekly Average */}
          <div className="bg-gradient-to-br from-blue-500/20 to-cyan-500/20 backdrop-blur-xl border border-blue-500/20 rounded-2xl p-6">
            <div className="flex items-center gap-3 mb-3">
              <div className="p-2 bg-blue-500/20 rounded-lg">
                <TrendingUp className="w-5 h-5 text-blue-400" />
              </div>
              <span className="text-gray-400 text-sm font-medium">Daily Avg</span>
            </div>
            <div className="text-3xl font-bold text-white mb-1">{formatTime(averageMinutes)}</div>
            <div className="text-sm text-gray-400">Last 7 days</div>
          </div>

          {/* Total Time */}
          <div className="bg-gradient-to-br from-green-500/20 to-emerald-500/20 backdrop-blur-xl border border-green-500/20 rounded-2xl p-6">
            <div className="flex items-center gap-3 mb-3">
              <div className="p-2 bg-green-500/20 rounded-lg">
                <Zap className="w-5 h-5 text-green-400" />
              </div>
              <span className="text-gray-400 text-sm font-medium">Total Time</span>
            </div>
            <div className="text-3xl font-bold text-white mb-1">{formatTime(totalMinutes)}</div>
            <div className="text-sm text-gray-400">All time</div>
          </div>

          {/* Current Session */}
          <div className="bg-gradient-to-br from-orange-500/20 to-red-500/20 backdrop-blur-xl border border-orange-500/20 rounded-2xl p-6">
            <div className="flex items-center gap-3 mb-3">
              <div className="p-2 bg-orange-500/20 rounded-lg">
                <Target className="w-5 h-5 text-orange-400" />
              </div>
              <span className="text-gray-400 text-sm font-medium">Session</span>
            </div>
            <div className="text-3xl font-bold text-white mb-1">{formatTime(currentSessionMinutes)}</div>
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-sm text-gray-400">Live</span>
            </div>
          </div>
        </div>

        {/* Activity Chart */}
        <div className="bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl p-8 mb-6">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-2xl font-bold text-white mb-2">Weekly Activity</h2>
              <p className="text-gray-400">Track your reading habits and engagement</p>
            </div>
            <div className="flex items-center gap-2 px-4 py-2 bg-white/5 rounded-lg border border-white/10">
              <Calendar className="w-4 h-4 text-gray-400" />
              <span className="text-gray-400 text-sm">Last 7 days</span>
            </div>
          </div>

          {/* Bar Chart */}
          <div className="mb-8">
            <div className="flex items-end justify-between h-64 gap-3">
              {weekActivity.map((day, index) => {
                const heightPercentage = maxMinutes > 0 ? (day.minutes / maxMinutes) * 100 : 0;
                const isToday = day.day === 'Today';
                
                return (
                  <div key={index} className="flex-1 flex flex-col items-center gap-3 group">
                    <div className="w-full flex items-end justify-center relative" style={{ height: '100%' }}>
                      {/* Bar */}
                      <div
                        className={`w-full rounded-lg transition-all duration-300 hover:opacity-80 cursor-pointer relative ${
                          isToday 
                            ? 'bg-[#d946ef]' 
                            : 'bg-[#d946ef]'
                        }`}
                        style={{ height: `${Math.max(heightPercentage, 8)}%` }}
                      >
                        {/* Tooltip on hover */}
                        <div className="absolute -top-14 left-1/2 transform -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
                          <div className="bg-gray-900 backdrop-blur-xl border border-gray-700 rounded-lg px-3 py-2 whitespace-nowrap shadow-xl">
                            <div className="text-white font-semibold text-sm">{formatTime(day.minutes)}</div>
                            {day.date && (
                              <div className="text-gray-400 text-xs">{day.date}</div>
                            )}
                          </div>
                          <div className="w-2 h-2 bg-gray-900 border-r border-b border-gray-700 transform rotate-45 mx-auto -mt-1"></div>
                        </div>
                      </div>
                    </div>
                    
                    {/* Day Label */}
                    <div className="text-center">
                      <span className={`text-sm font-medium ${
                        isToday ? 'text-white font-bold' : 'text-gray-400'
                      }`}>
                        {day.day}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Management Options */}
        <div className="space-y-4">
          <h3 className="text-2xl font-bold text-white mb-6">Manage Your Time</h3>
          
          {/* Daily Limit */}
          <div 
            className="bg-black/40 backdrop-blur-xl border border-white/10 hover:border-white/20 rounded-xl p-6 cursor-pointer transition-all group"
            onClick={() => {/* Handle daily limit setting */}}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-blue-500/20 rounded-xl group-hover:bg-blue-500/30 transition-colors">
                  <Target className="w-6 h-6 text-blue-400" />
                </div>
                <div>
                  <h4 className="text-white text-lg font-semibold mb-1">Daily Limit</h4>
                  <p className="text-gray-400 text-sm">Set a daily time goal</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-gray-400 text-lg font-medium">
                  {dailyLimit ? formatTime(dailyLimit) : 'Off'}
                </span>
                <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-white transition-colors" />
              </div>
            </div>
          </div>

          {/* Sleep Mode */}
          <div 
            className="bg-black/40 backdrop-blur-xl border border-white/10 hover:border-white/20 rounded-xl p-6 cursor-pointer transition-all group"
            onClick={() => {/* Handle sleep mode setting */}}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-purple-500/20 rounded-xl group-hover:bg-purple-500/30 transition-colors">
                  <Clock className="w-6 h-6 text-purple-400" />
                </div>
                <div>
                  <h4 className="text-white text-lg font-semibold mb-1">Sleep Mode</h4>
                  <p className="text-gray-400 text-sm">Schedule quiet hours</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-gray-400 text-lg font-medium">
                  {sleepMode ? 'On' : 'Off'}
                </span>
                <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-white transition-colors" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

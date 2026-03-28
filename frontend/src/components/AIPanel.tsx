'use client';

import { Sparkles, TrendingUp, Clock, BarChart3, Brain, Target, Zap, BookOpen } from 'lucide-react';

interface AIPanelProps {
  recommendations?: number;
  trending?: number;
  readingStreak?: number;
}

export default function AIPanel({ recommendations = 0, trending = 0, readingStreak = 0 }: AIPanelProps) {
  const engagementScore = Math.min(100, (recommendations * 2 + readingStreak * 5));
  const weeklyProgress = Math.min(100, (readingStreak / 7) * 100);

  return (
    <div className="space-y-6">
      {/* Main AI Panel */}
      <div className="card p-6 sticky top-20">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-text flex items-center">
            <div className="p-2 bg-gradient-to-br from-primary to-secondary rounded-lg mr-3">
              <Brain className="w-5 h-5 text-white" />
            </div>
            AI Insights
          </h2>
          <div className="flex items-center text-xs text-text-tertiary bg-hover px-2 py-1 rounded-full">
            <Zap className="w-3 h-3 mr-1" />
            Live
          </div>
        </div>

        <div className="space-y-4">
          {/* Personalization Score */}
          <div className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-100">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-semibold text-text flex items-center">
                <Target className="w-4 h-4 text-blue-600 mr-2" />
                Personalization
              </span>
              <span className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded-full font-medium">
                {engagementScore}%
              </span>
            </div>
            <div className="w-full bg-blue-100 rounded-full h-2 mb-2">
              <div 
                className="bg-gradient-to-r from-blue-500 to-indigo-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${engagementScore}%` }}
              ></div>
            </div>
            <p className="text-xs text-text-secondary">AI learning your preferences</p>
          </div>

          {/* Recommendations */}
          <div className="p-4 bg-gradient-to-r from-emerald-50 to-teal-50 rounded-xl border border-emerald-100">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-semibold text-text flex items-center">
                <Sparkles className="w-4 h-4 text-emerald-600 mr-2" />
                AI Picks
              </span>
              <div className="text-right">
                <p className="text-2xl font-bold text-emerald-600">{recommendations}</p>
              </div>
            </div>
            <p className="text-xs text-text-secondary">Curated articles matching your interests</p>
          </div>

          {/* Trending */}
          <div className="p-4 bg-gradient-to-r from-pink-50 to-rose-50 rounded-xl border border-pink-100">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-semibold text-text flex items-center">
                <TrendingUp className="w-4 h-4 text-pink-600 mr-2" />
                Trending
              </span>
              <div className="text-right">
                <p className="text-2xl font-bold text-pink-600">{trending}</p>
              </div>
            </div>
            <p className="text-xs text-text-secondary">Most popular articles right now</p>
          </div>

          {/* Reading Streak */}
          <div className="p-4 bg-gradient-to-r from-amber-50 to-orange-50 rounded-xl border border-amber-100">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-semibold text-text flex items-center">
                <Clock className="w-4 h-4 text-amber-600 mr-2" />
                Reading Streak
              </span>
              <div className="text-right">
                <p className="text-2xl font-bold text-amber-600">{readingStreak}</p>
                <p className="text-xs text-text-tertiary">days</p>
              </div>
            </div>
            <div className="w-full bg-amber-100 rounded-full h-2 mb-2">
              <div 
                className="bg-gradient-to-r from-amber-500 to-orange-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${weeklyProgress}%` }}
              ></div>
            </div>
            <p className="text-xs text-text-secondary">
              {readingStreak >= 7 ? '🔥 On fire! Keep it up!' : `${7 - readingStreak} days to weekly goal`}
            </p>
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="card p-5">
        <h3 className="text-lg font-semibold text-text mb-4 flex items-center">
          <BarChart3 className="w-5 h-5 text-primary mr-2" />
          Quick Stats
        </h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center p-3 bg-hover rounded-lg">
            <BookOpen className="w-6 h-6 text-primary mx-auto mb-2" />
            <p className="text-lg font-bold text-text">24</p>
            <p className="text-xs text-text-secondary">Articles Read</p>
          </div>
          <div className="text-center p-3 bg-hover rounded-lg">
            <Sparkles className="w-6 h-6 text-secondary mx-auto mb-2" />
            <p className="text-lg font-bold text-text">95%</p>
            <p className="text-xs text-text-secondary">Match Rate</p>
          </div>
        </div>
      </div>

      {/* AI Tips */}
      <div className="card p-5">
        <h3 className="text-lg font-semibold text-text mb-4 flex items-center">
          <Brain className="w-5 h-5 text-primary mr-2" />
          Smart Tips
        </h3>
        <div className="space-y-3">
          <div className="flex items-start space-x-3 p-3 bg-blue-50 rounded-lg">
            <div className="w-2 h-2 bg-primary rounded-full mt-2 flex-shrink-0"></div>
            <div>
              <p className="text-sm font-medium text-text">Interact more</p>
              <p className="text-xs text-text-secondary">Like and save articles to improve AI recommendations</p>
            </div>
          </div>
          <div className="flex items-start space-x-3 p-3 bg-green-50 rounded-lg">
            <div className="w-2 h-2 bg-success rounded-full mt-2 flex-shrink-0"></div>
            <div>
              <p className="text-sm font-medium text-text">Update interests</p>
              <p className="text-xs text-text-secondary">Keep your profile current for better content</p>
            </div>
          </div>
          <div className="flex items-start space-x-3 p-3 bg-purple-50 rounded-lg">
            <div className="w-2 h-2 bg-purple-600 rounded-full mt-2 flex-shrink-0"></div>
            <div>
              <p className="text-sm font-medium text-text">Daily reading</p>
              <p className="text-xs text-text-secondary">Maintain your streak for the best experience</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

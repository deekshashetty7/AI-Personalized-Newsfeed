'use client';

import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { Newspaper, User, LogOut, Home, Search, Menu, Sparkles } from 'lucide-react';
import { useState } from 'react';

export default function Header() {
  const { user, logout } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <header className="bg-surface shadow-soft border-b border-border sticky top-0 z-50 backdrop-blur-lg bg-surface/95">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href={user ? '/home' : '/'} className="flex items-center space-x-3 group">
            <img 
              src="/logo.jpg" 
              alt="InfoCred Logo" 
              className="w-12 h-12 rounded-full object-cover shadow-md group-hover:shadow-lg transition-all duration-200"
            />
            <div className="flex flex-col">
              <span className="text-xl font-bold text-text group-hover:text-primary transition-colors duration-200">
                InfoCred
              </span>
              <span className="text-[10px] text-text-tertiary hidden sm:block">
                Personalized News, Verified Trust
              </span>
            </div>
          </Link>

          {/* Navigation */}
          <nav className="hidden md:flex items-center space-x-2 ml-auto">
            {user ? (
              <>
                <Link
                  href="/home"
                  className="flex items-center space-x-2 px-4 py-2 rounded-lg text-text-secondary hover:bg-hover hover:text-primary transition-all duration-200"
                >
                  <Home className="w-5 h-5" />
                  <span className="font-medium">Home</span>
                </Link>
                <Link
                  href="/for-you"
                  className="flex items-center space-x-2 px-4 py-2 rounded-lg text-text-secondary hover:bg-hover hover:text-primary transition-all duration-200"
                >
                  <Sparkles className="w-5 h-5" />
                  <span className="font-medium">For You</span>
                </Link>
                <div className="w-px h-6 bg-border mx-2"></div>
                <Link
                  href="/profile"
                  className="flex items-center space-x-2 px-4 py-2 rounded-lg text-text-secondary hover:bg-hover hover:text-primary transition-all duration-200"
                >
                  <div className="w-8 h-8 bg-gradient-to-br from-primary to-secondary rounded-full flex items-center justify-center text-white font-semibold text-sm overflow-hidden">
                    {user.profile_photo ? (
                      <img 
                        src={user.profile_photo} 
                        alt={user.name}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      user.name?.charAt(0).toUpperCase()
                    )}
                  </div>
                </Link>
                <button
                  onClick={logout}
                  className="flex items-center space-x-2 px-4 py-2 rounded-lg text-text-secondary hover:bg-red-50 hover:text-error transition-all duration-200"
                >
                  <LogOut className="w-5 h-5" />
                  <span className="font-medium">Logout</span>
                </button>
              </>
            ) : (
              <>
                <Link
                  href="/login"
                  className="px-4 py-2 rounded-lg font-medium text-text-secondary hover:bg-hover hover:text-primary transition-all duration-200"
                >
                  Login
                </Link>
                <Link
                  href="/register"
                  className="px-6 py-2.5 bg-gradient-to-r from-primary to-secondary text-white font-semibold rounded-lg hover:shadow-medium transition-all duration-200 transform hover:scale-105"
                >
                  Sign Up
                </Link>
              </>
            )}
          </nav>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="md:hidden p-2 rounded-lg text-text-secondary hover:bg-hover transition-all duration-200"
          >
            <Menu className="w-6 h-6" />
          </button>
        </div>

        {/* Mobile Menu */}
        {isMenuOpen && (
          <div className="md:hidden py-4 border-t border-border bg-surface">
            <nav className="space-y-2">
              {user ? (
                <>
                  <Link
                    href="/home"
                    className="flex items-center space-x-3 px-4 py-3 rounded-lg text-text hover:bg-hover transition-all duration-200"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    <Home className="w-5 h-5 text-primary" />
                    <span className="font-medium">Home</span>
                  </Link>
                  <Link
                    href="/for-you"
                    className="flex items-center space-x-3 px-4 py-3 rounded-lg text-text hover:bg-hover transition-all duration-200"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    <Sparkles className="w-5 h-5 text-primary" />
                    <span className="font-medium">For You</span>
                  </Link>
                  <Link
                    href="/profile"
                    className="flex items-center space-x-3 px-4 py-3 rounded-lg text-text hover:bg-hover transition-all duration-200"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    <div className="w-8 h-8 bg-gradient-to-br from-primary to-secondary rounded-full flex items-center justify-center text-white font-semibold text-sm overflow-hidden">
                      {user.profile_photo ? (
                        <img 
                          src={user.profile_photo} 
                          alt={user.name}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <User className="w-5 h-5 text-white" />
                      )}
                    </div>
                    <span className="font-medium">Profile</span>
                  </Link>
                  <button
                    onClick={() => {
                      logout();
                      setIsMenuOpen(false);
                    }}
                    className="flex items-center space-x-3 px-4 py-3 rounded-lg text-error hover:bg-red-50 transition-all duration-200 w-full text-left"
                  >
                    <LogOut className="w-5 h-5" />
                    <span className="font-medium">Logout</span>
                  </button>
                </>
              ) : (
                <>
                  <Link
                    href="/login"
                    className="block px-4 py-3 rounded-lg text-text hover:bg-hover transition-all duration-200 font-medium"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    Login
                  </Link>
                  <Link
                    href="/register"
                    className="block px-4 py-3 bg-gradient-to-r from-primary to-secondary text-white font-semibold rounded-lg transition-all duration-200"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    Sign Up
                  </Link>
                </>
              )}
            </nav>
          </div>
        )}
      </div>
    </header>
  );
}

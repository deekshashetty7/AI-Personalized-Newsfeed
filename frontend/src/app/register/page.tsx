'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { authAPI } from '@/lib/api';
import { User, Mail, Lock, AlertCircle, CheckCircle, X, Smartphone, Briefcase, Heart, TrendingUp, Tv, Atom, Globe, Users } from 'lucide-react';

const MAIN_INTERESTS = [
  { name: 'Technology', icon: Smartphone, color: 'from-blue-500 to-cyan-500' },
  { name: 'Business', icon: Briefcase, color: 'from-green-500 to-emerald-500' },
  { name: 'Sports', icon: TrendingUp, color: 'from-orange-500 to-red-500' },
  { name: 'Entertainment', icon: Tv, color: 'from-purple-500 to-pink-500' },
  { name: 'Health', icon: Heart, color: 'from-red-500 to-rose-500' },
  { name: 'Science', icon: Atom, color: 'from-indigo-500 to-blue-500' },
  { name: 'Environment', icon: Globe, color: 'from-teal-500 to-green-500' },
  { name: 'Politics', icon: Users, color: 'from-gray-600 to-gray-800' },
];

const SUB_INTERESTS: Record<string, string[]> = {
  Technology: [
    'AI & Machine Learning',
    'Cybersecurity',
    'Gadgets & Hardware',
    'Space Tech',
    'Software Development',
    'Cloud Computing',
    'Blockchain & Crypto',
    'Mobile Technology',
    '5G & Networking',
    'Virtual Reality'
  ],
  Business: [
    'Stock Market',
    'Cryptocurrency',
    'Startups',
    'E-commerce',
    'Marketing',
    'Finance',
    'Real Estate',
    'Economics',
    'Leadership',
    'Entrepreneurship'
  ],
  Sports: [
    'Football',
    'Basketball',
    'Cricket',
    'Tennis',
    'Olympics',
    'Fitness',
    'Motorsports',
    'Golf',
    'Esports',
    'Extreme Sports'
  ],
  Entertainment: [
    'Movies',
    'TV Shows',
    'Music',
    'Gaming',
    'Celebrity News',
    'Fashion',
    'Art & Culture',
    'Books',
    'Theater',
    'Streaming'
  ],
  Health: [
    'Nutrition',
    'Mental Health',
    'Fitness & Exercise',
    'Medical Research',
    'Wellness',
    'Alternative Medicine',
    'Public Health',
    'Diet Plans',
    'Yoga & Meditation',
    'Healthcare Technology'
  ],
  Science: [
    'Physics',
    'Biology',
    'Chemistry',
    'Astronomy',
    'Climate Science',
    'Neuroscience',
    'Genetics',
    'Mathematics',
    'Research & Innovation',
    'Environmental Science'
  ],
  Environment: [
    'Climate Change',
    'Renewable Energy',
    'Conservation',
    'Sustainability',
    'Wildlife',
    'Pollution',
    'Green Technology',
    'Ocean Health',
    'Deforestation',
    'Recycling'
  ],
  Politics: [
    'Elections',
    'Government Policy',
    'International Relations',
    'Law & Justice',
    'Human Rights',
    'Immigration',
    'Defense & Security',
    'Social Issues',
    'Political Analysis',
    'Activism'
  ],
};

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuth();
  
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirm_password: '',
    interests: [] as string[],
  });
  const [otp, setOtp] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedMainInterest, setSelectedMainInterest] = useState<string | null>(null);
  const [tempSubInterests, setTempSubInterests] = useState<string[]>([]);
  const [otpSent, setOtpSent] = useState(false);
  const [otpVerified, setOtpVerified] = useState(false);
  const [sendingOtp, setSendingOtp] = useState(false);
  const [verifyingOtp, setVerifyingOtp] = useState(false);
  const [resendTimer, setResendTimer] = useState(0);
  const [passwordRequirements, setPasswordRequirements] = useState({
    length: false,
    uppercase: false,
    lowercase: false,
    number: false,
    special: false,
  });

  // Check password requirements
  const checkPasswordRequirements = (password: string) => {
    setPasswordRequirements({
      length: password.length >= 8,
      uppercase: /[A-Z]/.test(password),
      lowercase: /[a-z]/.test(password),
      number: /[0-9]/.test(password),
      special: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password),
    });
  };

  // Timer for resend OTP
  useEffect(() => {
    if (resendTimer > 0) {
      const timer = setTimeout(() => setResendTimer(resendTimer - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [resendTimer]);

  const handleSendOTP = async () => {
    if (!formData.email || !formData.email.includes('@')) {
      setError('Please enter a valid email address');
      return;
    }

    setSendingOtp(true);
    setError('');
    
    try {
      console.log('📧 Sending OTP to:', formData.email);
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/auth/send-otp/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: formData.email }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to send OTP');
      }

      console.log('✅ OTP sent successfully');
      setOtpSent(true);
      setResendTimer(60);
      setError('');
    } catch (err: any) {
      console.error('❌ Send OTP error:', err);
      setError(err.message || 'Failed to send OTP');
    } finally {
      setSendingOtp(false);
    }
  };

  const handleVerifyOTP = async () => {
    if (!otp || otp.length !== 6) {
      setError('Please enter the 6-digit OTP');
      return;
    }

    setVerifyingOtp(true);
    setError('');
    
    try {
      console.log('🔍 Verifying OTP for:', formData.email, 'OTP:', otp);
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/auth/verify-otp/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: formData.email, otp: otp.toString() }),
      });

      const data = await response.json();
      console.log('📥 Response:', data);

      if (!response.ok) {
        throw new Error(data.error || 'Invalid OTP');
      }

      console.log('✅ OTP verified successfully');
      setOtpVerified(true);
      setError('');
    } catch (err: any) {
      console.error('❌ Verify OTP error:', err);
      setError(err.message || 'Invalid OTP');
    } finally {
      setVerifyingOtp(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!otpVerified) {
      setError('Please verify your email with OTP first');
      return;
    }

    if (formData.password !== formData.confirm_password) {
      setError('Passwords do not match');
      return;
    }

    // Validate password requirements
    if (!passwordRequirements.length) {
      setError('Password must be at least 8 characters');
      return;
    }
    if (!passwordRequirements.uppercase) {
      setError('Password must contain at least 1 uppercase letter');
      return;
    }
    if (!passwordRequirements.lowercase) {
      setError('Password must contain at least 1 lowercase letter');
      return;
    }
    if (!passwordRequirements.number) {
      setError('Password must contain at least 1 number');
      return;
    }
    if (!passwordRequirements.special) {
      setError('Password must contain at least 1 special character');
      return;
    }

    setLoading(true);

    try {
      console.log('📝 Registering user with data:', {
        name: formData.name,
        email: formData.email,
        interests: formData.interests,
        interestsCount: formData.interests.length
      });
      await register(formData);
      console.log('✅ Registration successful, redirecting to home');
      router.push('/home');
    } catch (err: any) {
      console.error('Registration error:', err);
      const errorMessage = err.response?.data?.error || err.message || 'Registration failed. Please try again.';
      setError(typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage));
    } finally {
      setLoading(false);
    }
  };

  const openSubInterestsModal = (mainInterest: string) => {
    setSelectedMainInterest(mainInterest);
    // Get currently selected sub-interests for this main interest
    const existingSubInterests = formData.interests.filter(interest => 
      SUB_INTERESTS[mainInterest]?.includes(interest)
    );
    setTempSubInterests(existingSubInterests);
  };

  const toggleSubInterest = (subInterest: string) => {
    setTempSubInterests(prev =>
      prev.includes(subInterest)
        ? prev.filter(i => i !== subInterest)
        : [...prev, subInterest]
    );
  };

  const saveSubInterests = () => {
    if (!selectedMainInterest) return;
    
    // Remove old sub-interests from this main category
    const otherInterests = formData.interests.filter(interest => 
      !SUB_INTERESTS[selectedMainInterest]?.includes(interest)
    );
    
    // Add the main interest if not already there
    const mainInterestIncluded = otherInterests.includes(selectedMainInterest);
    
    // Combine: other interests + main interest (if not there) + selected sub-interests
    const newInterests = [
      ...otherInterests,
      ...(mainInterestIncluded ? [] : [selectedMainInterest]),
      ...tempSubInterests
    ];
    
    setFormData(prev => ({
      ...prev,
      interests: newInterests
    }));
    
    closeModal();
  };

  const closeModal = () => {
    setSelectedMainInterest(null);
    setTempSubInterests([]);
  };

  const getSelectedSubInterestsCount = (mainInterest: string) => {
    return formData.interests.filter(interest => 
      SUB_INTERESTS[mainInterest]?.includes(interest)
    ).length;
  };

  const isMainInterestSelected = (mainInterest: string) => {
    const count = getSelectedSubInterestsCount(mainInterest);
    return count > 0 || formData.interests.includes(mainInterest);
  };

  return (
    <div className="min-h-screen bg-background py-12 px-4">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-text mb-2">Create Account</h2>
          <p className="text-text-secondary">Join InfoCred and get personalized news</p>
        </div>

        {/* Form Card */}
        <div className="bg-white rounded-lg shadow-md p-8">
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start">
              <AlertCircle className="w-5 h-5 text-red-600 mr-2 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Name */}
            <div>
              <label htmlFor="name" className="block text-sm font-semibold text-gray-700 mb-2 tracking-wide uppercase">
                Full Name
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-secondary" />
                <input
                  id="name"
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full pl-10 pr-4 py-3 border border-border-color rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="John Doe"
                />
              </div>
            </div>

            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-semibold text-gray-700 mb-2 tracking-wide uppercase">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-secondary" />
                <input
                  id="email"
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) => {
                    setFormData({ ...formData, email: e.target.value });
                    setOtpSent(false);
                    setOtpVerified(false);
                    setOtp('');
                  }}
                  className="w-full pl-10 pr-28 py-3 border border-border-color rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="you@example.com"
                  disabled={otpVerified}
                />
                {!otpVerified && (
                  <button
                    type="button"
                    onClick={otpSent ? handleSendOTP : handleSendOTP}
                    disabled={sendingOtp || !formData.email || resendTimer > 0}
                    className="absolute right-2 top-1/2 -translate-y-1/2 px-3 py-1.5 text-xs font-medium bg-primary text-white rounded hover:bg-opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {sendingOtp ? 'Sending...' : resendTimer > 0 ? `${resendTimer}s` : otpSent ? 'Resend' : 'Send OTP'}
                  </button>
                )}
                {otpVerified && (
                  <CheckCircle className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-green-500" />
                )}
              </div>
              {otpVerified && (
                <p className="mt-1 text-sm text-green-600">✓ Email verified successfully</p>
              )}
            </div>

            {/* OTP Field - shown after OTP is sent */}
            {otpSent && !otpVerified && (
              <div>
                <label htmlFor="otp" className="block text-sm font-semibold text-gray-700 mb-2 tracking-wide uppercase">
                  Verification Code
                </label>
                <div className="relative">
                  <input
                    id="otp"
                    type="text"
                    maxLength={6}
                    required
                    value={otp}
                    onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                    className="w-full pl-4 pr-28 py-3 text-center text-2xl font-mono tracking-widest border border-border-color rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                    placeholder="000000"
                  />
                  <button
                    type="button"
                    onClick={handleVerifyOTP}
                    disabled={verifyingOtp || otp.length !== 6}
                    className="absolute right-2 top-1/2 -translate-y-1/2 px-3 py-1.5 text-xs font-medium bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {verifyingOtp ? 'Verifying...' : 'Verify'}
                  </button>
                </div>
                <p className="mt-1 text-sm text-gray-500">Enter the 6-digit code sent to your email</p>
              </div>
            )}

            {/* Password */}
            <div>
              <label htmlFor="password" className="block text-sm font-semibold text-gray-700 mb-2 tracking-wide uppercase">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-secondary" />
                <input
                  id="password"
                  type="password"
                  required
                  value={formData.password}
                  onChange={(e) => {
                    setFormData({ ...formData, password: e.target.value });
                    checkPasswordRequirements(e.target.value);
                  }}
                  className="w-full pl-10 pr-4 py-3 border border-border-color rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="••••••••"
                />
              </div>
              
              {/* Password Requirements Indicator */}
              {formData.password && (
                <div className="mt-3 p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <p className="text-sm font-semibold text-gray-700 mb-2">Password Requirements:</p>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      {passwordRequirements.length ? (
                        <CheckCircle className="w-4 h-4 text-green-600" />
                      ) : (
                        <X className="w-4 h-4 text-red-500" />
                      )}
                      <span className={`text-sm ${
                        passwordRequirements.length ? 'text-green-600' : 'text-red-500'
                      }`}>
                        At least 8 characters
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      {passwordRequirements.uppercase ? (
                        <CheckCircle className="w-4 h-4 text-green-600" />
                      ) : (
                        <X className="w-4 h-4 text-red-500" />
                      )}
                      <span className={`text-sm ${
                        passwordRequirements.uppercase ? 'text-green-600' : 'text-red-500'
                      }`}>
                        At least 1 uppercase letter (A-Z)
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      {passwordRequirements.lowercase ? (
                        <CheckCircle className="w-4 h-4 text-green-600" />
                      ) : (
                        <X className="w-4 h-4 text-red-500" />
                      )}
                      <span className={`text-sm ${
                        passwordRequirements.lowercase ? 'text-green-600' : 'text-red-500'
                      }`}>
                        At least 1 lowercase letter (a-z)
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      {passwordRequirements.number ? (
                        <CheckCircle className="w-4 h-4 text-green-600" />
                      ) : (
                        <X className="w-4 h-4 text-red-500" />
                      )}
                      <span className={`text-sm ${
                        passwordRequirements.number ? 'text-green-600' : 'text-red-500'
                      }`}>
                        At least 1 number (0-9)
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      {passwordRequirements.special ? (
                        <CheckCircle className="w-4 h-4 text-green-600" />
                      ) : (
                        <X className="w-4 h-4 text-red-500" />
                      )}
                      <span className={`text-sm ${
                        passwordRequirements.special ? 'text-green-600' : 'text-red-500'
                      }`}>
                        At least 1 special character (!@#$%^&*...)
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Confirm Password */}
            <div>
              <label htmlFor="confirm_password" className="block text-sm font-semibold text-gray-700 mb-2 tracking-wide uppercase">
                Confirm Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-secondary" />
                <input
                  id="confirm_password"
                  type="password"
                  required
                  value={formData.confirm_password}
                  onChange={(e) => setFormData({ ...formData, confirm_password: e.target.value })}
                  className="w-full pl-10 pr-4 py-3 border border-border-color rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="••••••••"
                />
              </div>
            </div>

              {/* SELECT Your Interests */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2 tracking-wide uppercase">
                  Select Your Interests
                </label>
                <p className="text-sm text-text-secondary mb-4">Choose topics you'd like to see in your personalized feed</p>
                
                {/* Main Interest Cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                  {MAIN_INTERESTS.map(({ name, color }) => (
                    <button
                      key={name}
                      type="button"
                      onClick={() => openSubInterestsModal(name)}
                      className={`relative p-4 rounded-lg border-2 transition-all duration-300 hover:shadow-lg ${
                        isMainInterestSelected(name)
                          ? `bg-gradient-to-br ${color} text-white border-transparent shadow-md`
                          : 'bg-white text-gray-700 border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <p className="text-sm font-medium text-center">{name}</p>
                      {getSelectedSubInterestsCount(name) > 0 && (
                        <span className="absolute top-2 right-2 bg-white text-gray-800 text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
                          {getSelectedSubInterestsCount(name)}
                        </span>
                      )}
                    </button>
                  ))}
                </div>

              {/* Selected Interests Summary */}
              {formData.interests.length > 0 && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <p className="text-sm font-semibold text-blue-900 mb-3">Your Selected Interests:</p>
                  <div className="space-y-3">
                    {MAIN_INTERESTS.map((mainCategory, index) => {
                      // Get all selected interests for this main category
                      const mainSelected = formData.interests.includes(mainCategory.name);
                      const subSelected = SUB_INTERESTS[mainCategory.name]?.filter(sub => 
                        formData.interests.includes(sub)
                      ) || [];
                      
                      // Only show if main category or any subcategory is selected
                      if (!mainSelected && subSelected.length === 0) return null;
                      
                      return (
                        <div key={mainCategory.name} className="text-sm">
                          {/* Main category with serial number */}
                          <div className="flex items-start gap-2">
                            <span className="font-semibold text-blue-900 min-w-[20px]">{index + 1}.</span>
                            <div className="flex-1">
                              <span className="font-semibold text-blue-900">{mainCategory.name}</span>
                              {mainSelected && (
                                <CheckCircle className="inline-block w-3 h-3 ml-1 text-green-600" />
                              )}
                              
                              {/* Subcategories with bullet points */}
                              {subSelected.length > 0 && (
                                <div className="mt-1 ml-4 space-y-1">
                                  {subSelected.map((subInterest) => (
                                    <div key={subInterest} className="flex items-center gap-2 text-blue-800">
                                      <span className="text-blue-600">•</span>
                                      <span className="text-xs">{subInterest}</span>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading || !otpVerified}
              className="w-full bg-gradient-to-r from-primary to-secondary text-white py-3 rounded-lg font-semibold hover:shadow-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Creating Account...' : 'Create Account'}
            </button>
          </form>

          {/* Footer */}
          <div className="mt-6 text-center">
            <p className="text-text-secondary text-sm">
              Already have an account?{' '}
              <Link href="/login" className="text-primary font-medium hover:underline">
                Sign in
              </Link>
            </p>
          </div>
        </div>

        {/* Back to Home */}
        <div className="mt-6 text-center">
          <Link href="/" className="text-text-secondary text-sm hover:text-primary transition">
            ← Back to Home
          </Link>
        </div>
      </div>

      {/* Sub-Interests Modal */}
      {selectedMainInterest && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn"
          onClick={closeModal}
        >
          <div 
            className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden animate-slideUp"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="bg-gradient-to-r from-primary to-secondary text-white px-6 py-4 flex items-center justify-between">
              <h3 className="text-xl font-bold">{selectedMainInterest} Topics</h3>
              <button
                onClick={closeModal}
                className="p-1 hover:bg-white/20 rounded-full transition"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 overflow-y-auto max-h-[calc(80vh-140px)]">
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {SUB_INTERESTS[selectedMainInterest]?.map((subInterest) => (
                  <button
                    key={subInterest}
                    type="button"
                    onClick={() => toggleSubInterest(subInterest)}
                    className={`px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 text-left ${
                      tempSubInterests.includes(subInterest)
                        ? 'bg-gradient-to-r from-primary to-secondary text-white shadow-md ring-2 ring-blue-300'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200 hover:shadow-sm'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      {tempSubInterests.includes(subInterest) && (
                        <CheckCircle className="w-4 h-4 flex-shrink-0" />
                      )}
                      <span className="line-clamp-2">{subInterest}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Modal Footer */}
            <div className="border-t border-gray-200 px-6 py-4 flex items-center justify-between bg-gray-50">
              <p className="text-sm text-gray-600">
                {tempSubInterests.length} topic{tempSubInterests.length !== 1 ? 's' : ''} selected
              </p>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={closeModal}
                  className="px-4 py-2 text-gray-700 hover:bg-gray-200 rounded-lg transition"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={saveSubInterests}
                  className="px-6 py-2 bg-gradient-to-r from-primary to-secondary text-white rounded-lg font-semibold hover:shadow-lg transition"
                >
                  Save
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

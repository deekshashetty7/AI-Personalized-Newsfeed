'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function ClearSessionPage() {
  const router = useRouter();

  useEffect(() => {
    // Clear all tokens
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    
    // Show message
    alert('Session cleared! You can now log in again with the fixed system.');
    
    // Redirect to login
    router.push('/login');
  }, [router]);

  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="text-center">
        <div className="text-4xl mb-4">🔄</div>
        <h1 className="text-2xl font-bold mb-2">Clearing Session...</h1>
        <p className="text-text-secondary">Please wait while we clear your session.</p>
      </div>
    </div>
  );
}

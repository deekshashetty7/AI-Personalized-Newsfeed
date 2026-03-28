'use client';

export default function SimplePage() {
  return (
    <div style={{ padding: '50px', background: '#f0f0f0', minHeight: '100vh' }}>
      <h1 style={{ fontSize: '48px', color: '#333', marginBottom: '20px' }}>InfoCred News</h1>
      <p style={{ fontSize: '24px', color: '#666' }}>The application is running!</p>
      <div style={{ marginTop: '30px', padding: '20px', background: 'white', borderRadius: '8px' }}>
        <h2>Server Status:</h2>
        <ul style={{ fontSize: '18px', lineHeight: '2' }}>
          <li>✅ Frontend: Running on port 3000</li>
          <li>✅ Backend: Running on port 8000</li>
        </ul>
      </div>
      <div style={{ marginTop: '20px' }}>
        <a href="/test" style={{ color: 'blue', fontSize: '18px' }}>Go to Test Page</a>
      </div>
    </div>
  );
}

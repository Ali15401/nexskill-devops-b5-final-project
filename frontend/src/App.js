import React, { useState, useEffect } from 'react';
import './App.css';

// --- KEY CHANGE 1 ---
// We only need ONE API endpoint: the public address of our Load Balancer.
// All requests will go to this single address.
// The `|| 'http://localhost:3000'` part is a fallback for local testing.
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://http://project-alb-985816287.us-east-1.elb.amazonaws.com;

function App() {
  const [url, setUrl] = useState('');
  const [shortUrl, setShortUrl] = useState('');
  const [links, setLinks] = useState([]);
  const [analytics, setAnalytics] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchLinks();
    fetchAnalytics();
  }, []);

  const fetchLinks = async () => {
    try {
      // Use the single API_BASE_URL
      const response = await fetch(`${API_BASE_URL}/api/links`);
      const data = await response.json();
      setLinks(data);
    } catch (err) {
      console.error('Error fetching links:', err);
    }
  };

  const fetchAnalytics = async () => {
    try {
      // Use the single API_BASE_URL, even for analytics
      // The Load Balancer will route this to the correct service based on its rules.
      const response = await fetch(`${API_BASE_URL}/api/analytics`);
      const data = await response.json();
      setAnalytics(data);
    } catch (err) {
      console.error('Error fetching analytics:', err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setShortUrl('');
    try {
      // Use the single API_BASE_URL
      const response = await fetch(`${API_BASE_URL}/api/shorten`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });
      const data = await response.json();
      
      if (response.ok) {
        // --- KEY CHANGE 2 ---
        // Create a full, correct URL without double slashes.
        // The backend returns a relative path like "/xyz", so we combine it
        // with the base URL to make a complete, clickable link.
        setShortUrl(new URL(data.short_url, API_BASE_URL).href);
        setUrl('');
        fetchLinks();
      } else {
        setError(data.error || 'Failed to shorten URL');
      }
    } catch (err) {
      setError('Failed to connect to server');
    }
  };

  const getClickCount = (shortCode) => {
    const analytic = analytics.find(a => a.short_code === shortCode);
    return analytic ? analytic.clicks : 0;
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>URL Shortener</h1>
      </header>
      <main className="container">
        <section className="create-section">
          <h2>Create Short URL</h2>
          <form onSubmit={handleSubmit}>
            <input
              type="url"
              placeholder="Enter your long URL"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              required
            />
            <button type="submit">Shorten</button>
          </form>
          
          {error && <div className="error">{error}</div>}
          
          {shortUrl && (
            <div className="result">
              <p>Short URL created:</p>
              <a href={shortUrl} target="_blank" rel="noopener noreferrer">
                {shortUrl}
              </a>
            </div>
          )}
        </section>

        <section className="links-section">
          <h2>All Links</h2>
          <table>
            <thead>
              <tr>
                <th>Short Code</th>
                <th>Original URL</th>
                <th>Clicks</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {links.map((link) => (
                <tr key={link.short_code}>
                  <td>
                    {/* --- KEY CHANGE 3 --- */}
                    {/* Also use the robust URL constructor here for consistency. */}
                    <a href={new URL(link.short_code, API_BASE_URL).href} target="_blank" rel="noopener noreferrer">
                      {link.short_code}
                    </a>
                  </td>
                  <td className="url-cell">{link.original_url}</td>
                  <td>{getClickCount(link.short_code)}</td>
                  <td>{new Date(link.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </main>
    </div>
  );
}

export default App;

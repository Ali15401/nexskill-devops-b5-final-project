import React, { useState, useEffect } from 'react';
import './App.css';

// --- KEY CHANGE ---
// This variable will be set to "/api" during the Docker build.
// For local testing, it can fall back to the direct backend URL.
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "http://localhost:5001";

function App() {
  const [url, setUrl] = useState('');
  const [shortUrl, setShortUrl] = useState('');
  const [links, setLinks] = useState([]);
  const [analytics, setAnalytics] = useState({ total_links: 0, total_clicks: 0 }); // Default state
  const [error, setError] = useState('');

  useEffect(() => {
    fetchLinks();
    fetchAnalytics();
  }, []);

  const fetchLinks = async () => {
    try {
      // CORRECTED: The path is now just "/links". API_BASE_URL will add the "/api" prefix.
      const response = await fetch(`${API_BASE_URL}/links`);
      const data = await response.json();
      setLinks(data.links || []); // Ensure we have an array even on error
    } catch (err) {
      console.error('Error fetching links:', err);
      setError('Failed to fetch links.');
    }
  };

  const fetchAnalytics = async () => {
    try {
      // CORRECTED: The path is now just "/analytics".
      const response = await fetch(`${API_BASE_URL}/analytics`);
      const data = await response.json();
      setAnalytics(data);
    } catch (err) {
      console.error('Error fetching analytics:', err);
      setError('Failed to fetch analytics.');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setShortUrl('');
    try {
      // CORRECTED: The path is now just "/shorten".
      const response = await fetch(`${API_BASE_URL}/shorten`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });
      const data = await response.json();
      
      if (response.ok) {
        // Construct the full clickable URL relative to the window's origin.
        setShortUrl(new URL(data.short_url, window.location.origin).href);
        setUrl('');
        fetchLinks();
        fetchAnalytics();
      } else {
        setError(data.error || 'Failed to shorten URL');
      }
    } catch (err) {
      setError('Failed to connect to server');
    }
  };

  const getClickCount = (shortCode) => {
    // This function will not work correctly with the current analytics format.
    // It is kept for completeness but would need to be updated if you implement click tracking per link.
    return 'N/A';
  };

  // --- This is the complete rendering logic from your original file ---
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
                    <a href={new URL(link.short_code, window.location.origin).href} target="_blank" rel="noopener noreferrer">
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

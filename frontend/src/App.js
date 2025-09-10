import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [pasteUrl, setPasteUrl] = useState('');
  const [error, setError] = useState('');
  const [viewMode, setViewMode] = useState('create');
  const [currentPaste, setCurrentPaste] = useState(null);

  useEffect(() => {
    // Check if we're viewing a paste based on URL
    const pathParts = window.location.pathname.split('/');
    const pasteId = pathParts[pathParts.length - 1];
    
    if (pasteId && pasteId !== '') {
      fetchPaste(pasteId);
    }
  }, []);

  const fetchPaste = async (pasteId) => {
    try {
      setLoading(true);
      const response = await fetch(`http://localhost:5000/api/paste/${pasteId}`);
      if (!response.ok) {
        throw new Error('Paste not found');
      }
      const data = await response.json();
      setCurrentPaste(data);
      setViewMode('view');
    } catch (err) {
      setError('Failed to fetch paste');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!content.trim()) {
      setError('Please enter some content');
      return;
    }

    try {
      setLoading(true);
      const response = await fetch('http://localhost:5000/api/paste', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ content }),
      });

      if (!response.ok) {
        throw new Error('Failed to create paste');
      }

      const data = await response.json();
      setPasteUrl(window.location.origin + data.url);
      setViewMode('created');
    } catch (err) {
      setError('Failed to create paste');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const createNewPaste = () => {
    setContent('');
    setPasteUrl('');
    setError('');
    setViewMode('create');
    window.history.pushState({}, '', '/');
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(pasteUrl);
  };

  if (viewMode === 'view' && currentPaste) {
    return (
      <div className="container">
        <h1>DPaste Clone</h1>
        <div className="paste-actions">
          <button onClick={createNewPaste} className="btn">
            New Paste
          </button>
        </div>
        <div className="paste-container">
          <pre>{currentPaste.content}</pre>
          <div className="paste-meta">
            <p>Created: {new Date(currentPaste.created_at).toLocaleString()}</p>
            <p>Expires: {new Date(currentPaste.expires_at).toLocaleString()}</p>
            <button 
              onClick={() => {
                navigator.clipboard.writeText(window.location.href);
                alert('Link copied to clipboard!');
              }}
              className="btn"
            >
              Copy Link
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (viewMode === 'created') {
    return (
      <div className="container">
        <h1>DPaste Clone</h1>
        <div className="success-message">
          <h2>Paste created successfully!</h2>
          <div className="paste-url">
            <input type="text" value={pasteUrl} readOnly />
            <button onClick={copyToClipboard} className="btn">
              Copy
            </button>
          </div>
          <div className="actions">
            <button onClick={createNewPaste} className="btn">
              Create Another Paste
            </button>
            <a href={pasteUrl} className="btn">
              View Paste
            </a>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <h1>DPaste Clone</h1>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Paste your text here..."
            rows={15}
            disabled={loading}
          />
        </div>
        {error && <div className="error">{error}</div>}
        <button type="submit" className="btn" disabled={loading}>
          {loading ? 'Creating...' : 'Create Paste'}
        </button>
      </form>
    </div>
  );
}

export default App;

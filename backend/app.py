from flask import Flask, request, jsonify, redirect, render_template_string
from flask_cors import CORS
from dotenv import load_dotenv
import shortuuid
import os
from datetime import datetime, timedelta, timezone

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 1048576))  # 1MB default

# Configure CORS
cors_origins = os.getenv('CORS_ORIGINS', 'https://dpaste-clone-rwab.vercel.app/').split(',')
print(f"CORS allowed origins: {cors_origins}")

CORS(
    app,
    resources={
        r"/api/*": {
            "origins": cors_origins,
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type"],
            "supports_credentials": True
        }
    },
    supports_credentials=True
)

# Add CORS headers to all responses
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', ','.join(cors_origins))
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# In-memory storage (replace with a database in production)
pastes = {}

# Simple HTML template for viewing pastes
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>DPaste Clone - {{ paste_id }}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9f9f9;
        }
        h1 { 
            color: #2c3e50;
            margin-top: 0;
            padding-bottom: 10px;
            border-bottom: 2px solid #eee;
        }
        .paste-container {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .paste-header {
            background: #2c3e50;
            color: white;
            padding: 10px 15px;
            font-size: 0.9em;
        }
        .paste-id {
            font-family: monospace;
            font-weight: bold;
        }
        .paste-meta {
            background: #f5f7fa;
            padding: 12px 15px;
            font-size: 0.85em;
            color: #666;
            border-bottom: 1px solid #eee;
        }
        .meta-item {
            margin: 5px 0;
            display: flex;
        }
        .meta-label {
            font-weight: 600;
            min-width: 100px;
            color: #444;
        }
        pre {
            margin: 0;
            padding: 15px;
            overflow-x: auto;
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            font-size: 14px;
            line-height: 1.5;
            background: #f8f9fa;
            border-left: 3px solid #4285f4;
        }
        code {
            font-family: inherit;
        }
        .copy-btn {
            background: #4285f4;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.8em;
            margin-left: 10px;
            vertical-align: middle;
        }
        .copy-btn:hover {
            background: #3367d6;
        }
        @media (max-width: 600px) {
            body {
                padding: 10px;
            }
            .meta-item {
                flex-direction: column;
            }
            .meta-label {
                margin-bottom: 2px;
            }
        }
    </style>
</head>
<body>
    <div class="paste-container">
        <div class="paste-header">
            DPaste Clone - <span class="paste-id">{{ paste_id }}</span>
            <button class="copy-btn" onclick="copyToClipboard()">Copy</button>
        </div>
        <div class="paste-meta">
            <div class="meta-item">
                <span class="meta-label">Created:</span>
                <span class="meta-value">{{ created_at }}</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">Expires in:</span>
                <span class="meta-value">{{ expires_in }}</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">Expires at:</span>
                <span class="meta-value">{{ expires_at }}</span>
            </div>
        </div>
        <pre><code>{{ content }}</code></pre>
    </div>

    <script>
        function copyToClipboard() {
            const code = document.querySelector('code');
            const range = document.createRange();
            range.selectNode(code);
            window.getSelection().removeAllRanges();
            window.getSelection().addRange(range);
            document.execCommand('copy');
            window.getSelection().removeAllRanges();
            
            const button = document.querySelector('.copy-btn');
            const originalText = button.textContent;
            button.textContent = 'Copied!';
            button.style.background = '#0f9d58';
            
            setTimeout(() => {
                button.textContent = originalText;
                button.style.background = '#4285f4';
            }, 2000);
        }
    </script>
</body>
</html>
"""

@app.route('/api/paste', methods=['POST'])
def create_paste():
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
            
        data = request.get_json() or {}
        content = data.get('content')
        
        if content is None:
            return jsonify({'error': 'Content is required'}), 400
            
        if not isinstance(content, str) or not content.strip():
            return jsonify({'error': 'Content must be a non-empty string'}), 400
            
        max_length = int(os.getenv('MAX_CONTENT_LENGTH', 1048576))
        if len(content) > max_length:
            return jsonify({
                'error': f'Content too large. Maximum size is {max_length} characters',
                'max_size': max_length,
                'current_size': len(content)
            }), 413  # Payload Too Large
        
        paste_id = shortuuid.uuid()
        created_at = datetime.now(timezone.utc)
        expires_at = created_at + timedelta(days=int(os.getenv('DEFAULT_EXPIRY_DAYS', 7)))
        
        pastes[paste_id] = {
            'content': content,
            'created_at': created_at.isoformat(),
            'expires_at': expires_at.isoformat()
        }
    
        return jsonify({
            'id': paste_id,
            'url': f'/p/{paste_id}',
            'expires_at': expires_at.isoformat()
        }), 201
        
    except Exception as e:
        app.logger.error(f'Error creating paste: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/paste/<paste_id>', methods=['GET'])
def get_paste(paste_id):
    try:
        paste = pastes.get(paste_id)
        if not paste:
            return jsonify({
                'error': 'Paste not found',
                'id': paste_id
            }), 404
        
        # Check if paste has expired
        expires_at = datetime.fromisoformat(paste['expires_at'].replace('Z', '+00:00'))
        if datetime.now(timezone.utc) > expires_at:
            # Remove expired paste
            pastes.pop(paste_id, None)
            return jsonify({
                'error': 'Paste has expired',
                'id': paste_id,
                'expired_at': paste['expires_at']
            }), 410  # Gone
        
        return jsonify({
            'id': paste_id,
            'content': paste['content'],
            'created_at': paste['created_at'],
            'expires_at': paste['expires_at'],
            'expires_in_seconds': int((expires_at - datetime.now(timezone.utc)).total_seconds())
        })
        
    except Exception as e:
        app.logger.error(f'Error retrieving paste {paste_id}: {str(e)}')
        return jsonify({
            'error': 'Failed to retrieve paste',
            'id': paste_id
        }), 500

@app.route('/p/<paste_id>')
def view_paste(paste_id):
    try:
        # Reuse the get_paste logic but return HTML
        response = get_paste(paste_id)
        
        if response.status_code != 200:
            error_data = response.get_json()
            error_msg = error_data.get('error', 'An error occurred')
            return f'<h1>Error: {error_msg}</h1>', response.status_code
        
        paste = response.get_json()
        
        return render_template_string(
            HTML_TEMPLATE,
            paste_id=paste_id,
            content=paste['content'],
            created_at=paste['created_at'],
            expires_at=paste['expires_at'],
            expires_in=format_timedelta(timedelta(seconds=paste.get('expires_in_seconds', 0)))
        )
        
    except Exception as e:
        app.logger.error(f'Error rendering paste {paste_id}: {str(e)}')
        return '<h1>Error: Failed to load paste</h1>', 500

def format_timedelta(delta):
    """Format timedelta into a human-readable string"""
    seconds = int(delta.total_seconds())
    periods = [
        ('day', 86400),
        ('hour', 3600),
        ('minute', 60),
        ('second', 1)
    ]
    
    parts = []
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            if period_value > 0:
                plural = 's' if period_value > 1 else ''
                parts.append(f'{period_value} {period_name}{plural}')
    
    return ', '.join(parts) if parts else 'less than a second'

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render sets PORT
    app.run(host="0.0.0.0", port=port)
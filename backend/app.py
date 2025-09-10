from flask import Flask, request, jsonify, redirect, render_template_string
from flask_cors import CORS
import shortuuid
import os
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# In-memory storage (replace with a database in production)
pastes = {}

# Simple HTML template for viewing pastes
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>DPaste Clone - {{ paste_id }}</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        pre { background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }
        .info { color: #666; font-size: 0.9em; margin-bottom: 20px; }
    </style>
</head>
<body>
    <h1>DPaste Clone</h1>
    <div class="info">
        <strong>Created at:</strong> {{ created_at }}<br>
        <strong>Expires at:</strong> {{ expires_at }}
    </div>
    <pre><code>{{ content }}</code></pre>
</body>
</html>
"""

@app.route('/api/paste', methods=['POST'])
def create_paste():
    data = request.json
    content = data.get('content')
    
    if not content:
        return jsonify({'error': 'Content is required'}), 400
    
    paste_id = shortuuid.uuid()
    created_at = datetime.utcnow()
    expires_at = created_at + timedelta(days=7)  # Default expiration: 7 days
    
    pastes[paste_id] = {
        'content': content,
        'created_at': created_at.isoformat(),
        'expires_at': expires_at.isoformat()
    }
    
    return jsonify({
        'id': paste_id,
        'url': f'/p/{paste_id}'
    }), 201

@app.route('/api/paste/<paste_id>', methods=['GET'])
def get_paste(paste_id):
    paste = pastes.get(paste_id)
    if not paste:
        return jsonify({'error': 'Paste not found'}), 404
    
    return jsonify({
        'id': paste_id,
        'content': paste['content'],
        'created_at': paste['created_at'],
        'expires_at': paste['expires_at']
    })

@app.route('/p/<paste_id>')
def view_paste(paste_id):
    paste = pastes.get(paste_id)
    if not paste:
        return 'Paste not found', 404
    
    return render_template_string(
        HTML_TEMPLATE,
        paste_id=paste_id,
        content=paste['content'],
        created_at=paste['created_at'],
        expires_at=paste['expires_at']
    )

if __name__ == '__main__':
    app.run(debug=True)

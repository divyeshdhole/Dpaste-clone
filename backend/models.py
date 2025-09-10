from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
import os
from . import app

# Initialize SQLAlchemy
db = SQLAlchemy()

class Paste(db.Model):
    """Paste model for storing paste data"""
    __tablename__ = 'pastes'
    
    id = db.Column(db.String(22), primary_key=True)  # Using shortuuid
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime, nullable=False)
    
    def to_dict(self):
        """Convert paste object to dictionary"""
        return {
            'id': self.id,
            'content': self.content,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat()
        }

def init_db():
    """Initialize the database"""
    # Ensure the instance directory exists
    os.makedirs(app.instance_path, exist_ok=True)
    
    # Configure SQLite database
    db_path = os.path.join(app.instance_path, 'dpaste.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize the database
    db.init_app(app)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return db

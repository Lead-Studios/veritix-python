"""
Database migration script to add feedback tables
Run this script to add the feedback functionality to existing databases
"""

from sqlalchemy import create_engine, text
from app.config import settings

def run_migration():
    """Run the feedback tables migration"""
    
    engine = create_engine(settings.DATABASE_URL)
    
    # SQL to create the chat_feedback table
    create_feedback_table_sql = """
    CREATE TABLE IF NOT EXISTS chat_feedback (
        id SERIAL PRIMARY KEY,
        session_id INTEGER NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        rating INTEGER CHECK (rating >= 1 AND rating <= 5),
        thumbs_rating BOOLEAN,
        feedback_text TEXT,
        feedback_tags TEXT,
        agent_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
        resolution_helpful BOOLEAN,
        response_time_rating INTEGER CHECK (response_time_rating >= 1 AND response_time_rating <= 5),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    
    # Create indexes for better performance
    create_indexes_sql = """
    CREATE INDEX IF NOT EXISTS idx_chat_feedback_session_id ON chat_feedback(session_id);
    CREATE INDEX IF NOT EXISTS idx_chat_feedback_user_id ON chat_feedback(user_id);
    CREATE INDEX IF NOT EXISTS idx_chat_feedback_agent_id ON chat_feedback(agent_id);
    CREATE INDEX IF NOT EXISTS idx_chat_feedback_created_at ON chat_feedback(created_at);
    CREATE INDEX IF NOT EXISTS idx_chat_feedback_rating ON chat_feedback(rating);
    """
    
    try:
        with engine.connect() as connection:
            # Create the table
            connection.execute(text(create_feedback_table_sql))
            print("✅ Created chat_feedback table")
            
            # Create indexes
            connection.execute(text(create_indexes_sql))
            print("✅ Created indexes for chat_feedback table")
            
            # Commit the transaction
            connection.commit()
            print("✅ Migration completed successfully")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    print("🚀 Running feedback tables migration...")
    run_migration()
    print("🎉 Migration completed!")

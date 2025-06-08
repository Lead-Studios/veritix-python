import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from datetime import datetime, timedelta

from ..models import ChatFeedback, ChatSession, User
from ..schemas import FeedbackCreate, FeedbackUpdate, FeedbackStats
from ..websocket_manager import manager

class FeedbackService:
    def __init__(self, db: Session):
        self.db = db

    def create_feedback(
        self, 
        session_id: int, 
        user_id: int, 
        feedback_data: FeedbackCreate
    ) -> Optional[ChatFeedback]:
        """Create feedback for a chat session"""
        
        # Check if session exists
        session = self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            return None
        
        # Check if feedback already exists for this session
        existing_feedback = self.db.query(ChatFeedback).filter(
            ChatFeedback.session_id == session_id,
            ChatFeedback.user_id == user_id
        ).first()
        
        if existing_feedback:
            return None  # Feedback already exists
        
        # Find the agent who handled the session (last agent to send a message)
        agent_id = None
        if session.messages:
            # Get the last agent message
            agent_message = self.db.query(ChatSession).join(ChatSession.messages).join(
                User, User.id == ChatSession.user_id
            ).filter(
                ChatSession.id == session_id,
                User.role.in_(["agent", "admin"])
            ).first()
            
            if agent_message:
                agent_id = agent_message.user_id
        
        # Create feedback
        db_feedback = ChatFeedback(
            session_id=session_id,
            user_id=user_id,
            agent_id=agent_id,
            rating=feedback_data.rating,
            thumbs_rating=feedback_data.thumbs_rating,
            feedback_text=feedback_data.feedback_text,
            feedback_tags=json.dumps(feedback_data.feedback_tags) if feedback_data.feedback_tags else None,
            resolution_helpful=feedback_data.resolution_helpful,
            response_time_rating=feedback_data.response_time_rating
        )
        
        self.db.add(db_feedback)
        self.db.commit()
        self.db.refresh(db_feedback)
        
        return db_feedback

    def update_feedback(
        self, 
        feedback_id: int, 
        user_id: int, 
        feedback_data: FeedbackUpdate
    ) -> Optional[ChatFeedback]:
        """Update existing feedback"""
        
        feedback = self.db.query(ChatFeedback).filter(
            ChatFeedback.id == feedback_id,
            ChatFeedback.user_id == user_id
        ).first()
        
        if not feedback:
            return None
        
        # Update fields
        if feedback_data.rating is not None:
            feedback.rating = feedback_data.rating
        if feedback_data.thumbs_rating is not None:
            feedback.thumbs_rating = feedback_data.thumbs_rating
        if feedback_data.feedback_text is not None:
            feedback.feedback_text = feedback_data.feedback_text
        if feedback_data.feedback_tags is not None:
            feedback.feedback_tags = json.dumps(feedback_data.feedback_tags)
        if feedback_data.resolution_helpful is not None:
            feedback.resolution_helpful = feedback_data.resolution_helpful
        if feedback_data.response_time_rating is not None:
            feedback.response_time_rating = feedback_data.response_time_rating
        
        self.db.commit()
        self.db.refresh(feedback)
        
        return feedback

    def get_session_feedback(self, session_id: int) -> Optional[ChatFeedback]:
        """Get feedback for a specific session"""
        return self.db.query(ChatFeedback).filter(
            ChatFeedback.session_id == session_id
        ).first()

    def get_user_feedback_history(self, user_id: int, limit: int = 50) -> List[ChatFeedback]:
        """Get feedback history for a user"""
        return self.db.query(ChatFeedback).filter(
            ChatFeedback.user_id == user_id
        ).order_by(desc(ChatFeedback.created_at)).limit(limit).all()

    def get_agent_feedback(self, agent_id: int, limit: int = 50) -> List[ChatFeedback]:
        """Get feedback for a specific agent"""
        return self.db.query(ChatFeedback).filter(
            ChatFeedback.agent_id == agent_id
        ).order_by(desc(ChatFeedback.created_at)).limit(limit).all()

    def get_feedback_stats(self, days: int = 30) -> FeedbackStats:
        """Get feedback statistics for the last N days"""
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Base query for the time period
        base_query = self.db.query(ChatFeedback).filter(
            ChatFeedback.created_at >= start_date
        )
        
        # Total feedback count
        total_feedback = base_query.count()
        
        if total_feedback == 0:
            return FeedbackStats(
                total_feedback=0,
                average_rating=None,
                thumbs_up_percentage=None,
                resolution_helpful_percentage=None,
                average_response_time_rating=None,
                common_tags=[]
            )
        
        # Average rating (1-5 scale)
        avg_rating_result = base_query.filter(
            ChatFeedback.rating.isnot(None)
        ).with_entities(func.avg(ChatFeedback.rating)).scalar()
        
        # Thumbs up percentage
        thumbs_up_count = base_query.filter(
            ChatFeedback.thumbs_rating == True
        ).count()
        thumbs_total = base_query.filter(
            ChatFeedback.thumbs_rating.isnot(None)
        ).count()
        thumbs_up_percentage = (thumbs_up_count / thumbs_total * 100) if thumbs_total > 0 else None
        
        # Resolution helpful percentage
        helpful_count = base_query.filter(
            ChatFeedback.resolution_helpful == True
        ).count()
        helpful_total = base_query.filter(
            ChatFeedback.resolution_helpful.isnot(None)
        ).count()
        helpful_percentage = (helpful_count / helpful_total * 100) if helpful_total > 0 else None
        
        # Average response time rating
        avg_response_time = base_query.filter(
            ChatFeedback.response_time_rating.isnot(None)
        ).with_entities(func.avg(ChatFeedback.response_time_rating)).scalar()
        
        # Common tags
        common_tags = self._get_common_tags(base_query)
        
        return FeedbackStats(
            total_feedback=total_feedback,
            average_rating=round(avg_rating_result, 2) if avg_rating_result else None,
            thumbs_up_percentage=round(thumbs_up_percentage, 2) if thumbs_up_percentage else None,
            resolution_helpful_percentage=round(helpful_percentage, 2) if helpful_percentage else None,
            average_response_time_rating=round(avg_response_time, 2) if avg_response_time else None,
            common_tags=common_tags
        )

    def _get_common_tags(self, base_query) -> List[Dict[str, Any]]:
        """Get most common feedback tags"""
        
        feedback_with_tags = base_query.filter(
            ChatFeedback.feedback_tags.isnot(None)
        ).all()
        
        tag_counts = {}
        
        for feedback in feedback_with_tags:
            if feedback.feedback_tags:
                try:
                    tags = json.loads(feedback.feedback_tags)
                    for tag in tags:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
                except json.JSONDecodeError:
                    continue
        
        # Sort by count and return top 10
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return [
            {"tag": tag, "count": count, "percentage": round(count / len(feedback_with_tags) * 100, 2)}
            for tag, count in sorted_tags
        ]

    def get_agent_performance(self, agent_id: int, days: int = 30) -> Dict[str, Any]:
        """Get performance metrics for a specific agent"""
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        agent_feedback = self.db.query(ChatFeedback).filter(
            ChatFeedback.agent_id == agent_id,
            ChatFeedback.created_at >= start_date
        )
        
        total_feedback = agent_feedback.count()
        
        if total_feedback == 0:
            return {
                "agent_id": agent_id,
                "total_feedback": 0,
                "average_rating": None,
                "thumbs_up_percentage": None,
                "resolution_helpful_percentage": None,
                "average_response_time_rating": None
            }
        
        # Calculate metrics
        avg_rating = agent_feedback.filter(
            ChatFeedback.rating.isnot(None)
        ).with_entities(func.avg(ChatFeedback.rating)).scalar()
        
        thumbs_up_count = agent_feedback.filter(
            ChatFeedback.thumbs_rating == True
        ).count()
        thumbs_total = agent_feedback.filter(
            ChatFeedback.thumbs_rating.isnot(None)
        ).count()
        thumbs_up_percentage = (thumbs_up_count / thumbs_total * 100) if thumbs_total > 0 else None
        
        helpful_count = agent_feedback.filter(
            ChatFeedback.resolution_helpful == True
        ).count()
        helpful_total = agent_feedback.filter(
            ChatFeedback.resolution_helpful.isnot(None)
        ).count()
        helpful_percentage = (helpful_count / helpful_total * 100) if helpful_total > 0 else None
        
        avg_response_time = agent_feedback.filter(
            ChatFeedback.response_time_rating.isnot(None)
        ).with_entities(func.avg(ChatFeedback.response_time_rating)).scalar()
        
        return {
            "agent_id": agent_id,
            "total_feedback": total_feedback,
            "average_rating": round(avg_rating, 2) if avg_rating else None,
            "thumbs_up_percentage": round(thumbs_up_percentage, 2) if thumbs_up_percentage else None,
            "resolution_helpful_percentage": round(helpful_percentage, 2) if helpful_percentage else None,
            "average_response_time_rating": round(avg_response_time, 2) if avg_response_time else None
        }

    async def request_feedback(self, session_id: str):
        """Send feedback request to session participants"""
        
        # Get session from database
        session = self.db.query(ChatSession).filter(
            ChatSession.session_id == session_id
        ).first()
        
        if not session:
            return False
        
        # Check if feedback already exists
        existing_feedback = self.db.query(ChatFeedback).filter(
            ChatFeedback.session_id == session.id
        ).first()
        
        if existing_feedback:
            return False  # Feedback already collected
        
        # Send feedback request via WebSocket
        feedback_request = {
            "type": "feedback_request",
            "data": {
                "session_id": session_id,
                "message": "How was your chat experience? Please rate your session.",
                "feedback_options": {
                    "rating_scale": {"min": 1, "max": 5, "label": "Overall Experience"},
                    "thumbs_rating": {"label": "Was this helpful?"},
                    "resolution_helpful": {"label": "Did we resolve your issue?"},
                    "response_time_rating": {"min": 1, "max": 5, "label": "Response Time"},
                    "predefined_tags": [
                        "Quick Response", "Helpful Agent", "Clear Communication",
                        "Problem Solved", "Professional Service", "Friendly Support",
                        "Technical Expertise", "Patient Assistance"
                    ]
                }
            }
        }
        
        await manager.broadcast_to_session(session_id, feedback_request)
        return True

    def get_predefined_tags(self) -> List[str]:
        """Get list of predefined feedback tags"""
        return [
            "Quick Response", "Helpful Agent", "Clear Communication",
            "Problem Solved", "Professional Service", "Friendly Support",
            "Technical Expertise", "Patient Assistance", "Knowledgeable",
            "Courteous", "Efficient", "Understanding", "Thorough",
            "Responsive", "Accurate Information", "Good Follow-up"
        ]

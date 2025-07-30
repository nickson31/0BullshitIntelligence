"""
Chat API Router for 0BullshitIntelligence.
Handles real-time chat conversations with Gemini AI and session-based memory.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.chat import ChatMessage, ChatResponse
from app.models.user import UserContext, ProjectData
from app.ai_systems.judge_system import judge_system
from app.ai_systems.anti_spam import anti_spam_system
from app.ai_systems.language_detection import language_detection_system
from app.ai_systems.librarian import librarian_bot
import google.generativeai as genai

router = APIRouter()
logger = get_logger(__name__)
settings = get_settings()

# Configure Gemini
genai.configure(api_key=settings.gemini_api_key)
model = genai.GenerativeModel(settings.gemini_model)


def get_session_context(session_id: Optional[str] = None) -> UserContext:
    """Get or create session context for anonymous users"""
    if not session_id:
        session_id = str(uuid4())
    
    return UserContext(
        user_id=session_id,
        plan="free",
        language="spanish",
        credits=200,
        daily_credits_used=0,
        onboarding_completed=False,
        projects=[],
        features=["chat", "basic_search"],
        session_data={"session_id": session_id}
    )


@router.post("/message", response_model=ChatResponse)
async def send_message(
    message: ChatMessage,
    session_id: Optional[str] = None
):
    """Send a message and get AI response"""
    
    try:
        # Get session context (anonymous)
        user_context = get_session_context(session_id)
        conversation_id = message.conversation_id or str(uuid4())
        
        logger.info("Processing chat message",
                   session_id=user_context.user_id,
                   conversation_id=conversation_id,
                   message_length=len(message.content))
        
        # 1. Anti-spam check
        spam_result = await anti_spam_system.analyze_message(
            message.content, conversation_id, user_context.session_data
        )
        
        if spam_result.is_spam:
            # Generate clever anti-spam response
            spam_response = await anti_spam_system.generate_clever_response(
                spam_result, user_context.language, user_context.session_data
            )
            
            return ChatResponse(
                message_id=str(uuid4()),
                conversation_id=conversation_id,
                content=spam_response,
                role="assistant",
                metadata={
                    "spam_detected": True,
                    "spam_score": spam_result.spam_score
                }
            )
        
        # 2. Language detection
        language_detection = await language_detection_system.detect_language(
            message.content, conversation_id, user_context.session_data
        )
        
        # 3. Judge system - determine intent
        judge_decision = await judge_system.analyze_message(
            message.content, conversation_id, user_context.session_data
        )
        
        # 4. Generate response with Gemini
        ai_response = await generate_ai_response(
            message.content, conversation_id, user_context, judge_decision
        )
        
        # 5. Librarian - extract and store project data
        librarian_result = await librarian_bot.process_conversation_update(
            user_context.user_id,
            conversation_id, 
            message.content,
            ai_response,
            user_context.session_data.get('project_data')
        )
        
        # Update session data with new project info
        user_context.session_data['project_data'] = librarian_result['project_data']
        user_context.session_data['completeness_score'] = librarian_result['completeness_score']
        
        logger.info("Chat message processed successfully",
                   session_id=user_context.user_id,
                   conversation_id=conversation_id,
                   intent=judge_decision.detected_intent,
                   completeness_score=librarian_result['completeness_score'])
        
        return ChatResponse(
            message_id=str(uuid4()),
            conversation_id=conversation_id,
            content=ai_response,
            role="assistant",
            metadata={
                "intent": judge_decision.detected_intent,
                "language": language_detection.detected_language,
                "confidence": judge_decision.confidence_score,
                "completeness_score": librarian_result['completeness_score'],
                "extracted_fields": librarian_result['extracted_fields']
            }
        )
        
    except Exception as e:
        logger.error("Chat message processing failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to process message")


async def generate_ai_response(
    user_message: str, 
    conversation_id: str, 
    user_context: UserContext,
    judge_decision: Any
) -> str:
    """Generate AI response using Gemini"""
    
    try:
        # Build context-aware prompt
        context_info = ""
        project_data = user_context.session_data.get('project_data')
        if project_data:
            context_info = f"""
Context about user's project:
- Categories: {project_data.get('categories', [])}
- Stage: {project_data.get('stage', 'unknown')}
- Problem solved: {project_data.get('problem_solved', '')}
- Business model: {project_data.get('business_model', '')}
"""
        
        # Create intelligent prompt based on intent
        if judge_decision.detected_intent == "search_investors":
            prompt = f"""You are a Y-Combinator mentor helping entrepreneurs find investors.

User message: "{user_message}"
{context_info}

The user wants to find investors. Provide specific, actionable advice about:
1. What stage they should be at for investor search
2. What metrics they need to prepare
3. Types of investors to target based on their business
4. How to approach investors effectively

Be direct, practical, and encouraging. Respond in Spanish if the user wrote in Spanish.
"""
        elif judge_decision.detected_intent == "search_companies":
            prompt = f"""You are a business mentor helping entrepreneurs find B2B services and partners.

User message: "{user_message}"
{context_info}

The user is looking for companies/services. Help them:
1. Identify what type of service they really need
2. Key criteria to evaluate providers
3. Questions to ask potential partners
4. Red flags to avoid

Be practical and specific. Respond in Spanish if the user wrote in Spanish.
"""
        else:
            prompt = f"""You are a brilliant Y-Combinator mentor with deep startup experience.

User message: "{user_message}"
{context_info}

Provide expert startup advice that is:
- Direct and actionable
- Based on real experience
- Focused on execution over theory
- Encouraging but realistic

If they mention their business, ask insightful follow-up questions to understand their needs better.
Respond in Spanish if the user wrote in Spanish, English if they wrote in English.
"""
        
        # Generate response with Gemini
        response = model.generate_content(prompt)
        return response.text.strip()
        
    except Exception as e:
        logger.error("AI response generation failed", error=str(e))
        return "Lo siento, hubo un problema técnico. ¿Podrías intentar de nuevo? / Sorry, there was a technical issue. Could you try again?"


@router.get("/conversations/{conversation_id}/history")
async def get_conversation_history(
    conversation_id: str,
    session_id: Optional[str] = None
):
    """Get conversation history"""
    
    try:
        user_context = get_session_context(session_id)
        
        # For now, return empty history - would integrate with database
        return {
            "conversation_id": conversation_id,
            "messages": [],
            "project_data": user_context.session_data.get('project_data', {}),
            "completeness_score": user_context.session_data.get('completeness_score', 0.0)
        }
        
    except Exception as e:
        logger.error("Failed to get conversation history", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve conversation history")


@router.get("/session/{session_id}/analytics")
async def get_session_analytics(session_id: str):
    """Get analytics for a session"""
    
    try:
        user_context = get_session_context(session_id)
        
        # Return basic analytics - would integrate with database
        return {
            "session_id": session_id,
            "total_conversations": 1,
            "total_messages": 0,
            "project_data": user_context.session_data.get('project_data', {}),
            "completeness_score": user_context.session_data.get('completeness_score', 0.0),
            "last_activity": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get session analytics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics")


@router.post("/session/create")
async def create_session():
    """Create a new anonymous session"""
    
    try:
        session_id = str(uuid4())
        user_context = get_session_context(session_id)
        
        logger.info("New session created", session_id=session_id)
        
        return {
            "session_id": session_id,
            "message": "Session created successfully",
            "features": user_context.features
        }
        
    except Exception as e:
        logger.error("Failed to create session", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create session")
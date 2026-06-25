from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import json
import asyncio

from app.database import get_db
from app.models import User, LLMModel, AIConversation, AIMessage, LLMUsage, AIPromptTemplate
from app.auth import get_current_user, require_admin
from app.services.llm_service import LLMService
from app.services.activity_log import log_activity

router = APIRouter(prefix="/api/v1/llm", tags=["LLM Integration"])

# Schemas
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model_id: Optional[str] = None
    conversation_id: Optional[int] = None
    stream: bool = False
    temperature: float = 0.7
    system_prompt: Optional[str] = None
    template_name: Optional[str] = None
    use_tools: bool = False

class ConversationCreate(BaseModel):
    title: Optional[str] = None
    model_id: Optional[str] = None
    system_prompt: Optional[str] = None

class TemplateCreate(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    system_prompt: str
    user_prompt_template: Optional[str] = None
    variables: Optional[List[str]] = None
    category: str = "general"
    model_id: Optional[str] = None

class ModelUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None

# ==================== MODELS ====================

@router.get("/models")
async def list_models(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all configured LLM models."""
    models = db.query(LLMModel).all()

    # Also fetch available models from Ollama
    service = LLMService(db)
    available = await service.get_available_models()
    available_ids = {m["name"] for m in available}

    result = []
    for model in models:
        result.append({
            "id": model.id,
            "name": model.name,
            "provider": model.provider,
            "model_id": model.model_id,
            "display_name": model.display_name,
            "description": model.description,
            "parameters": model.parameters,
            "is_active": model.is_active,
            "is_default": model.is_default,
            "supports_streaming": model.supports_streaming,
            "supports_tools": model.supports_tools,
            "context_window": model.context_window,
            "is_available": model.model_id in available_ids,
            "created_at": model.created_at.isoformat() if model.created_at else None
        })

    return {"models": result, "available_from_provider": available}

@router.get("/models/{model_id}")
def get_model(
    model_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific model details."""
    model = db.query(LLMModel).filter(LLMModel.model_id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model

@router.put("/models/{model_id}")
def update_model(
    model_id: str,
    data: ModelUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update model configuration. Admin only."""
    model = db.query(LLMModel).filter(LLMModel.model_id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    if data.is_default and data.is_default != model.is_default:
        # Unset other defaults
        db.query(LLMModel).filter(LLMModel.is_default == True).update({"is_default": False})

    for key, value in data.dict(exclude_unset=True).items():
        setattr(model, key, value)

    db.commit()
    db.refresh(model)
    log_activity(db, user_id=current_user.id, action="llm_model_updated", entity_type="llm_model", entity_id=model.id)
    return model

@router.post("/models/{model_id}/pull")
async def pull_model(
    model_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Pull a model from Ollama. Admin only."""
    service = LLMService(db)
    try:
        import httpx
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{service.ollama_base}/api/pull",
                json={"name": model_id, "stream": False}
            )
            if response.status_code == 200:
                return {"status": "success", "message": f"Model {model_id} pulled successfully"}
            return {"status": "error", "message": f"Failed to pull model: {response.text}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/models/{model_id}")
def delete_model(
    model_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete a model configuration. Admin only."""
    model = db.query(LLMModel).filter(LLMModel.model_id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    db.delete(model)
    db.commit()
    return {"message": "Model deleted"}

# ==================== CHAT ====================

@router.post("/chat")
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a chat message to the LLM."""
    service = LLMService(db)

    # Get or create conversation
    conversation = None
    if request.conversation_id:
        conversation = db.query(AIConversation).filter(
            AIConversation.id == request.conversation_id,
            AIConversation.user_id == current_user.id
        ).first()

    if not conversation:
        model_id = request.model_id or service.default_model
        system_prompt = request.system_prompt

        if request.template_name and not system_prompt:
            template = db.query(AIPromptTemplate).filter(
                AIPromptTemplate.name == request.template_name,
                AIPromptTemplate.is_active == True
            ).first()
            if template:
                system_prompt = template.system_prompt
                if template.model_id:
                    model_id = template.model_id

        if not system_prompt:
            system_prompt = service.build_system_prompt()

        conversation = AIConversation(
            user_id=current_user.id,
            title=request.messages[0].content[:50] if request.messages else "New Chat",
            model_id=model_id,
            system_prompt=system_prompt
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    # Prepare messages
    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    # Add previous conversation messages for context
    if conversation:
        prev_messages = db.query(AIMessage).filter(
            AIMessage.conversation_id == conversation.id
        ).order_by(AIMessage.created_at).all()

        for msg in prev_messages:
            messages.insert(0, {"role": msg.role, "content": msg.content})

    # Save user message
    user_msg = AIMessage(
        conversation_id=conversation.id,
        role="user",
        content=request.messages[-1].content if request.messages else ""
    )
    db.add(user_msg)
    db.commit()

    # Get tools if requested
    tools = None
    if request.use_tools:
        tools = service.TOOLS

    # Call LLM
    result = await service.chat(
        messages=messages,
        model_id=conversation.model_id,
        temperature=request.temperature,
        tools=tools,
        system_prompt=conversation.system_prompt
    )

    # Log usage
    service.log_usage(
        user_id=current_user.id,
        model_id=conversation.model_id,
        conversation_id=conversation.id,
        prompt_tokens=result.get("prompt_tokens", 0),
        completion_tokens=result.get("completion_tokens", 0),
        latency_ms=result.get("latency_ms", 0),
        endpoint="chat",
        success=result.get("success", False),
        error_message=result.get("error")
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])

    # Handle tool calls
    if result.get("tool_calls"):
        tool_results = []
        for tool_call in result["tool_calls"]:
            tool_name = tool_call.get("function", {}).get("name")
            arguments = json.loads(tool_call.get("function", {}).get("arguments", "{}"))
            tool_result = await service.execute_tool(tool_name, arguments)
            tool_results.append({"tool": tool_name, "result": tool_result})

        # Add tool results to messages and call again
        messages.append({"role": "assistant", "content": result["content"], "tool_calls": result["tool_calls"]})
        for tr in tool_results:
            messages.append({"role": "tool", "content": json.dumps(tr["result"]), "name": tr["tool"]})

        # Second call with tool results
        result = await service.chat(
            messages=messages,
            model_id=conversation.model_id,
            temperature=request.temperature,
            system_prompt=conversation.system_prompt
        )

    # Save assistant message
    assistant_msg = AIMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=result["content"],
        model_id=result["model"],
        tokens_used=result.get("total_tokens"),
        latency_ms=result.get("latency_ms")
    )
    db.add(assistant_msg)
    db.commit()

    # Update conversation
    conversation.updated_at = datetime.utcnow()
    db.commit()

    log_activity(db, user_id=current_user.id, action="ai_chat", entity_type="ai_conversation", entity_id=conversation.id)

    return {
        "conversation_id": conversation.id,
        "message": {
            "role": "assistant",
            "content": result["content"],
            "model": result["model"],
            "tokens_used": result.get("total_tokens"),
            "latency_ms": result.get("latency_ms")
        },
        "tool_results": tool_results if 'tool_results' in dir() else None
    }

@router.post("/chat/stream")
async def stream_chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Stream chat response from LLM."""
    service = LLMService(db)

    model_id = request.model_id or service.default_model
    system_prompt = request.system_prompt or service.build_system_prompt()

    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    async def event_generator():
        full_content = ""
        start_time = datetime.utcnow()

        async for chunk in service.stream_chat(
            messages=messages,
            model_id=model_id,
            temperature=request.temperature,
            system_prompt=system_prompt
        ):
            data = json.loads(chunk)
            if data.get("type") == "content":
                full_content += data.get("content", "")
                yield f"data: {json.dumps({'type': 'content', 'content': data.get('content', '')})}\n\n"
            elif data.get("type") == "done":
                # Save to conversation
                conversation = AIConversation(
                    user_id=current_user.id,
                    title=messages[0]["content"][:50] if messages else "Stream Chat",
                    model_id=model_id,
                    system_prompt=system_prompt
                )
                db.add(conversation)
                db.commit()
                db.refresh(conversation)

                # Save messages
                for msg in messages:
                    db.add(AIMessage(conversation_id=conversation.id, role=msg["role"], content=msg["content"]))
                db.add(AIMessage(
                    conversation_id=conversation.id,
                    role="assistant",
                    content=full_content,
                    model_id=model_id
                ))
                db.commit()

                # Log usage
                service.log_usage(
                    user_id=current_user.id,
                    model_id=model_id,
                    conversation_id=conversation.id,
                    prompt_tokens=data.get("prompt_tokens", 0),
                    completion_tokens=data.get("completion_tokens", 0),
                    total_tokens=data.get("total_tokens", 0),
                    endpoint="chat_stream",
                    success=True
                )

                yield f"data: {json.dumps({'type': 'done', 'conversation_id': conversation.id, 'total_tokens': data.get('total_tokens', 0)})}\n\n"
            elif data.get("type") == "error":
                yield f"data: {json.dumps({'type': 'error', 'error': data.get('error')})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

# ==================== CONVERSATIONS ====================

@router.get("/conversations")
def list_conversations(
    archived: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List user's AI conversations."""
    conversations = db.query(AIConversation).filter(
        AIConversation.user_id == current_user.id,
        AIConversation.is_archived == archived
    ).order_by(AIConversation.updated_at.desc()).all()

    return [
        {
            "id": c.id,
            "title": c.title,
            "model_id": c.model_id,
            "message_count": len(c.messages),
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None
        }
        for c in conversations
    ]

@router.get("/conversations/{conversation_id}")
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get conversation with messages."""
    conversation = db.query(AIConversation).filter(
        AIConversation.id == conversation_id,
        AIConversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {
        "id": conversation.id,
        "title": conversation.title,
        "model_id": conversation.model_id,
        "system_prompt": conversation.system_prompt,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "model_id": m.model_id,
                "tokens_used": m.tokens_used,
                "created_at": m.created_at.isoformat() if m.created_at else None
            }
            for m in conversation.messages
        ],
        "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
        "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None
    }

@router.post("/conversations")
def create_conversation(
    data: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new conversation."""
    service = LLMService(db)
    model_id = data.model_id or service.default_model
    system_prompt = data.system_prompt or service.build_system_prompt()

    conversation = AIConversation(
        user_id=current_user.id,
        title=data.title or "New Conversation",
        model_id=model_id,
        system_prompt=system_prompt
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation

@router.put("/conversations/{conversation_id}/archive")
def archive_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Archive a conversation."""
    conversation = db.query(AIConversation).filter(
        AIConversation.id == conversation_id,
        AIConversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation.is_archived = True
    db.commit()
    return {"message": "Conversation archived"}

@router.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a conversation."""
    conversation = db.query(AIConversation).filter(
        AIConversation.id == conversation_id,
        AIConversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    db.delete(conversation)
    db.commit()
    return {"message": "Conversation deleted"}

# ==================== TEMPLATES ====================

@router.get("/templates")
def list_templates(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List AI prompt templates."""
    query = db.query(AIPromptTemplate).filter(AIPromptTemplate.is_active == True)
    if category:
        query = query.filter(AIPromptTemplate.category == category)
    return query.all()

@router.get("/templates/{template_name}")
def get_template(
    template_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific template."""
    template = db.query(AIPromptTemplate).filter(
        AIPromptTemplate.name == template_name,
        AIPromptTemplate.is_active == True
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template

@router.post("/templates")
def create_template(
    data: TemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a new prompt template. Admin only."""
    existing = db.query(AIPromptTemplate).filter(AIPromptTemplate.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Template name already exists")

    template = AIPromptTemplate(**data.dict(), created_by=current_user.id)
    db.add(template)
    db.commit()
    db.refresh(template)
    log_activity(db, user_id=current_user.id, action="template_created", entity_type="ai_template", entity_id=template.id)
    return template

@router.delete("/templates/{template_id}")
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete a template. Admin only."""
    template = db.query(AIPromptTemplate).filter(AIPromptTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    db.delete(template)
    db.commit()
    return {"message": "Template deleted"}

# ==================== ANALYTICS ====================

@router.get("/analytics/usage")
def get_usage_analytics(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get LLM usage analytics."""
    from datetime import datetime, timedelta
    from sqlalchemy import func

    start_date = datetime.utcnow() - timedelta(days=days)

    # Total usage
    total = db.query(LLMUsage).filter(LLMUsage.created_at >= start_date).count()
    total_tokens = db.query(func.sum(LLMUsage.total_tokens)).filter(LLMUsage.created_at >= start_date).scalar() or 0
    total_prompt = db.query(func.sum(LLMUsage.prompt_tokens)).filter(LLMUsage.created_at >= start_date).scalar() or 0
    total_completion = db.query(func.sum(LLMUsage.completion_tokens)).filter(LLMUsage.created_at >= start_date).scalar() or 0
    avg_latency = db.query(func.avg(LLMUsage.latency_ms)).filter(LLMUsage.created_at >= start_date).scalar() or 0

    # By model
    by_model = db.query(
        LLMUsage.model_id,
        func.count(LLMUsage.id).label("count"),
        func.sum(LLMUsage.total_tokens).label("tokens"),
        func.avg(LLMUsage.latency_ms).label("avg_latency")
    ).filter(LLMUsage.created_at >= start_date).group_by(LLMUsage.model_id).all()

    # By day
    by_day = db.query(
        func.date(LLMUsage.created_at).label("date"),
        func.count(LLMUsage.id).label("count"),
        func.sum(LLMUsage.total_tokens).label("tokens")
    ).filter(LLMUsage.created_at >= start_date).group_by(func.date(LLMUsage.created_at)).order_by("date").all()

    # By endpoint
    by_endpoint = db.query(
        LLMUsage.endpoint,
        func.count(LLMUsage.id).label("count"),
        func.sum(LLMUsage.total_tokens).label("tokens")
    ).filter(LLMUsage.created_at >= start_date).group_by(LLMUsage.endpoint).all()

    # Error rate
    errors = db.query(LLMUsage).filter(
        LLMUsage.created_at >= start_date,
        LLMUsage.success == False
    ).count()

    return {
        "period_days": days,
        "total_requests": total,
        "total_tokens": int(total_tokens),
        "prompt_tokens": int(total_prompt),
        "completion_tokens": int(total_completion),
        "avg_latency_ms": round(float(avg_latency), 2) if avg_latency else 0,
        "error_rate": (errors / total * 100) if total > 0 else 0,
        "by_model": [
            {"model": m.model_id, "requests": m.count, "tokens": int(m.tokens or 0), "avg_latency_ms": round(float(m.avg_latency or 0), 2)}
            for m in by_model
        ],
        "by_day": [
            {"date": str(d.date), "requests": d.count, "tokens": int(d.tokens or 0)}
            for d in by_day
        ],
        "by_endpoint": [
            {"endpoint": e.endpoint, "requests": e.count, "tokens": int(e.tokens or 0)}
            for e in by_endpoint
        ]
    }

@router.get("/analytics/conversations")
def get_conversation_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get conversation analytics."""
    from sqlalchemy import func

    total_conversations = db.query(AIConversation).count()
    total_messages = db.query(AIMessage).count()
    avg_messages_per_conv = total_messages / total_conversations if total_conversations > 0 else 0

    # Most active users
    top_users = db.query(
        AIMessage.conversation_id,
        func.count(AIMessage.id).label("msg_count")
    ).group_by(AIMessage.conversation_id).order_by(func.count(AIMessage.id).desc()).limit(10).all()

    return {
        "total_conversations": total_conversations,
        "total_messages": total_messages,
        "avg_messages_per_conversation": round(avg_messages_per_conv, 2),
        "top_conversations": [
            {"conversation_id": t.conversation_id, "message_count": t.msg_count}
            for t in top_users
        ]
    }

from datetime import datetime


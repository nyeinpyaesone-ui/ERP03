import json
import time
from typing import AsyncGenerator, Dict, Any, List, Optional, Callable
from datetime import datetime
import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import LLMModel, AIConversation, AIMessage, LLMUsage, Contact, Company, Deal, Product, Invoice, Project, Task
from app.config import settings

class LLMService:
    """Service for managing LLM interactions with multi-model support."""

    def __init__(self, db: Session = None):
        self.db = db
        self.ollama_base = settings.OLLAMA_BASE_URL
        self.default_model = settings.OLLAMA_MODEL

    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models from Ollama."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.ollama_base}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = data.get("models", [])
                    return [
                        {
                            "name": m.get("name"),
                            "size": m.get("size"),
                            "modified_at": m.get("modified_at"),
                            "digest": m.get("digest")
                        }
                        for m in models
                    ]
                return []
        except Exception:
            return []

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model_id: str = None,
        stream: bool = False,
        temperature: float = 0.7,
        tools: List[Dict[str, Any]] = None,
        system_prompt: str = None
    ) -> Dict[str, Any]:
        """Send chat completion request to LLM."""
        model_id = model_id or self.default_model

        # Build request payload
        payload = {
            "model": model_id,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature
            }
        }

        if system_prompt:
            # Prepend system message
            payload["messages"] = [{"role": "system", "content": system_prompt}] + messages

        if tools:
            payload["tools"] = tools

        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.ollama_base}/api/chat",
                    json=payload
                )

                latency_ms = int((time.time() - start_time) * 1000)

                if response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"LLM API error: {response.status_code}",
                        "latency_ms": latency_ms
                    }

                data = response.json()

                # Extract response
                message = data.get("message", {})
                content = message.get("content", "")

                # Extract token usage if available
                prompt_tokens = data.get("prompt_eval_count", 0)
                completion_tokens = data.get("eval_count", 0)
                total_tokens = prompt_tokens + completion_tokens

                # Check for tool calls
                tool_calls = None
                if message.get("tool_calls"):
                    tool_calls = message["tool_calls"]

                return {
                    "success": True,
                    "content": content,
                    "model": model_id,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "latency_ms": latency_ms,
                    "tool_calls": tool_calls,
                    "done": data.get("done", True)
                }

        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "LLM request timed out",
                "latency_ms": int((time.time() - start_time) * 1000)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "latency_ms": int((time.time() - start_time) * 1000)
            }

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model_id: str = None,
        temperature: float = 0.7,
        system_prompt: str = None
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion from LLM."""
        model_id = model_id or self.default_model

        payload = {
            "model": model_id,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature
            }
        }

        if system_prompt:
            payload["messages"] = [{"role": "system", "content": system_prompt}] + messages

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.ollama_base}/api/chat",
                    json=payload
                ) as response:
                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                data = json.loads(line)
                                if "message" in data and "content" in data["message"]:
                                    content = data["message"]["content"]
                                    if content:
                                        yield json.dumps({
                                            "type": "content",
                                            "content": content,
                                            "done": data.get("done", False)
                                        }) + "\n"

                                if data.get("done"):
                                    yield json.dumps({
                                        "type": "done",
                                        "prompt_tokens": data.get("prompt_eval_count", 0),
                                        "completion_tokens": data.get("eval_count", 0),
                                        "total_tokens": (data.get("prompt_eval_count", 0) + data.get("eval_count", 0))
                                    }) + "\n"

                            except json.JSONDecodeError:
                                continue

        except Exception as e:
            yield json.dumps({"type": "error", "error": str(e)}) + "\n"

    def log_usage(
        self,
        user_id: int,
        model_id: str,
        conversation_id: int = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        latency_ms: int = 0,
        endpoint: str = "chat",
        success: bool = True,
        error_message: str = None
    ):
        """Log LLM usage for analytics."""
        if not self.db:
            return

        usage = LLMUsage(
            user_id=user_id,
            model_id=model_id,
            conversation_id=conversation_id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            latency_ms=latency_ms,
            endpoint=endpoint,
            success=success,
            error_message=error_message
        )
        self.db.add(usage)
        self.db.commit()

    def get_business_context(self) -> Dict[str, Any]:
        """Gather current business data for AI context."""
        if not self.db:
            return {}

        from sqlalchemy import func

        context = {}

        # CRM
        context["contacts_count"] = self.db.query(Contact).count()
        context["companies_count"] = self.db.query(Company).count()
        context["deals_count"] = self.db.query(Deal).count()
        context["pipeline_value"] = float(self.db.query(func.sum(Deal.value)).filter(Deal.stage != "closed_lost").scalar() or 0)

        # Inventory
        context["products_count"] = self.db.query(Product).count()
        low_stock = self.db.query(Product).filter(Product.quantity_in_stock <= Product.reorder_level).count()
        context["low_stock_count"] = low_stock

        # Finance
        context["invoices_count"] = self.db.query(Invoice).count()
        context["total_revenue"] = float(self.db.query(func.sum(Invoice.amount_paid)).filter(Invoice.status == "paid").scalar() or 0)

        # Projects
        context["projects_count"] = self.db.query(Project).count()
        context["tasks_count"] = self.db.query(Task).count()

        return context

    def build_system_prompt(self, template_name: str = None, custom_context: Dict[str, Any] = None) -> str:
        """Build system prompt with business context."""
        if template_name and self.db:
            template = self.db.query(AIPromptTemplate).filter(
                AIPromptTemplate.name == template_name,
                AIPromptTemplate.is_active == True
            ).first()
            if template:
                return template.system_prompt

        base_prompt = """You are an AI business assistant for an Enterprise Resource Planning (ERP) system. You have access to business data including CRM, HR, Inventory, Finance, and Projects.

Guidelines:
- Be concise and data-driven in your responses
- When analyzing data, provide specific numbers and trends
- Suggest actionable next steps when appropriate
- If you don't have access to specific data, say so clearly
- Maintain a professional but friendly tone
- Format responses with markdown when helpful"""

        # Add business context
        context = custom_context or self.get_business_context()
        if context:
            context_str = "\n\nCurrent Business Context:\n"
            for key, value in context.items():
                context_str += f"- {key}: {value}\n"
            base_prompt += context_str

        return base_prompt

    # Tool definitions for AI agent
    TOOLS = [
        {
            "type": "function",
            "function": {
                "name": "get_contacts",
                "description": "Get list of contacts from CRM",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "Maximum number of contacts to return"},
                        "status": {"type": "string", "description": "Filter by status: lead, prospect, customer, churned"}
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_deals",
                "description": "Get sales deals and pipeline data",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "stage": {"type": "string", "description": "Filter by stage: prospect, qualification, proposal, negotiation, closed_won, closed_lost"},
                        "limit": {"type": "integer", "description": "Maximum number of deals to return"}
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_products",
                "description": "Get inventory products and stock levels",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "low_stock": {"type": "boolean", "description": "Only show products below reorder level"},
                        "limit": {"type": "integer", "description": "Maximum number of products to return"}
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_invoices",
                "description": "Get invoices and payment status",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "description": "Filter by status: draft, sent, paid, overdue, cancelled"},
                        "limit": {"type": "integer", "description": "Maximum number of invoices to return"}
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_projects",
                "description": "Get projects and tasks",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "description": "Filter by status: planning, active, on_hold, completed, cancelled"},
                        "limit": {"type": "integer", "description": "Maximum number of projects to return"}
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "create_contact",
                "description": "Create a new contact in CRM",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "first_name": {"type": "string", "description": "Contact first name"},
                        "last_name": {"type": "string", "description": "Contact last name"},
                        "email": {"type": "string", "description": "Contact email address"},
                        "company": {"type": "string", "description": "Company name"},
                        "status": {"type": "string", "description": "Contact status: lead, prospect, customer"}
                    },
                    "required": ["first_name", "last_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "create_task",
                "description": "Create a new task in a project",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "integer", "description": "Project ID"},
                        "title": {"type": "string", "description": "Task title"},
                        "description": {"type": "string", "description": "Task description"},
                        "priority": {"type": "string", "description": "Priority: low, medium, high"}
                    },
                    "required": ["project_id", "title"]
                }
            }
        }
    ]

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool function and return results."""
        if not self.db:
            return {"error": "Database not available"}

        try:
            if tool_name == "get_contacts":
                limit = arguments.get("limit", 10)
                status = arguments.get("status")
                query = self.db.query(Contact)
                if status:
                    query = query.filter(Contact.status == status)
                contacts = query.limit(limit).all()
                return {
                    "contacts": [
                        {"id": c.id, "name": f"{c.first_name} {c.last_name}", "email": c.email, "status": c.status, "company": c.company.name if c.company else None}
                        for c in contacts
                    ]
                }

            elif tool_name == "get_deals":
                limit = arguments.get("limit", 10)
                stage = arguments.get("stage")
                query = self.db.query(Deal)
                if stage:
                    query = query.filter(Deal.stage == stage)
                deals = query.limit(limit).all()
                return {
                    "deals": [
                        {"id": d.id, "title": d.title, "value": float(d.value or 0), "stage": d.stage, "probability": d.probability}
                        for d in deals
                    ]
                }

            elif tool_name == "get_products":
                limit = arguments.get("limit", 10)
                low_stock = arguments.get("low_stock", False)
                query = self.db.query(Product)
                if low_stock:
                    query = query.filter(Product.quantity_in_stock <= Product.reorder_level)
                products = query.limit(limit).all()
                return {
                    "products": [
                        {"id": p.id, "name": p.name, "sku": p.sku, "stock": p.quantity_in_stock, "reorder_level": p.reorder_level, "price": float(p.unit_price or 0)}
                        for p in products
                    ]
                }

            elif tool_name == "get_invoices":
                limit = arguments.get("limit", 10)
                status = arguments.get("status")
                query = self.db.query(Invoice)
                if status:
                    query = query.filter(Invoice.status == status)
                invoices = query.limit(limit).all()
                return {
                    "invoices": [
                        {"id": i.id, "number": i.invoice_number, "total": float(i.total or 0), "status": i.status, "due_date": str(i.due_date) if i.due_date else None}
                        for i in invoices
                    ]
                }

            elif tool_name == "get_projects":
                limit = arguments.get("limit", 10)
                status = arguments.get("status")
                query = self.db.query(Project)
                if status:
                    query = query.filter(Project.status == status)
                projects = query.limit(limit).all()
                return {
                    "projects": [
                        {"id": p.id, "name": p.name, "status": p.status, "progress": p.progress, "budget": float(p.budget or 0)}
                        for p in projects
                    ]
                }

            elif tool_name == "create_contact":
                contact = Contact(
                    first_name=arguments["first_name"],
                    last_name=arguments["last_name"],
                    email=arguments.get("email"),
                    status=arguments.get("status", "lead")
                )
                self.db.add(contact)
                self.db.commit()
                return {"success": True, "contact_id": contact.id, "message": f"Created contact {contact.first_name} {contact.last_name}"}

            elif tool_name == "create_task":
                task = Task(
                    project_id=arguments["project_id"],
                    title=arguments["title"],
                    description=arguments.get("description"),
                    priority=arguments.get("priority", "medium")
                )
                self.db.add(task)
                self.db.commit()
                return {"success": True, "task_id": task.id, "message": f"Created task: {task.title}"}

            else:
                return {"error": f"Unknown tool: {tool_name}"}

        except Exception as e:
            return {"error": str(e)}


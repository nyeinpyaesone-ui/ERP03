"""
ERP03 Integration Contracts - API v1

This directory contains OpenAPI schema exports for ERP-BACKEND API v1.
These contracts define the interface between ERP-BACKEND and AI-BACKEND.

IMPORTANT: AI systems must ONLY use these contracts. Never import ERP ORM models directly.
"""

# API Contract Version: v1.0.0
# Generated: 2026-08-16

from typing import Dict, Any

# ============================================================================
# OpenAPI Specification Summary
# ============================================================================

OPENAPI_SPEC: Dict[str, Any] = {
    "openapi": "3.0.3",
    "info": {
        "title": "ERP03 API",
        "description": "ERP System of Record API for AI-BACKEND integration",
        "version": "1.0.0",
        "contact": {
            "email": "nyeinpyaesone273@gmail.com"
        }
    },
    "servers": [
        {
            "url": "http://localhost:8000/api/v1",
            "description": "Development server"
        },
        {
            "url": "https://api.yourdomain.com/api/v1",
            "description": "Production server"
        }
    ],
    "security": [
        {"BearerAuth": []},
        {"ApiKeyAuth": []}
    ],
    "paths": {
        # Health & Auth
        "/health": {
            "get": {
                "summary": "Health check",
                "operationId": "healthCheck",
                "responses": {
                    "200": {
                        "description": "Service is healthy",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/HealthStatus"}
                            }
                        }
                    }
                }
            }
        },
        "/auth/me": {
            "get": {
                "summary": "Get current user",
                "operationId": "getCurrentUser",
                "security": [{"BearerAuth": []}],
                "responses": {
                    "200": {
                        "description": "Current user details",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/User"}
                            }
                        }
                    }
                }
            }
        },
        
        # CRM Endpoints
        "/crm/customers": {
            "get": {
                "summary": "List customers",
                "operationId": "listCustomers",
                "parameters": [
                    {"name": "page", "in": "query", "schema": {"type": "integer", "default": 1}},
                    {"name": "page_size", "in": "query", "schema": {"type": "integer", "default": 20}},
                    {"name": "search", "in": "query", "schema": {"type": "string"}}
                ],
                "responses": {
                    "200": {
                        "description": "List of customers",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "items": {"type": "array", "items": {"$ref": "#/components/schemas/Customer"}},
                                        "total": {"type": "integer"},
                                        "page": {"type": "integer"},
                                        "page_size": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "post": {
                "summary": "Create customer",
                "operationId": "createCustomer",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/CustomerCreate"}
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Customer created",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Customer"}
                            }
                        }
                    }
                }
            }
        },
        "/crm/customers/{customer_id}": {
            "get": {
                "summary": "Get customer",
                "operationId": "getCustomer",
                "parameters": [
                    {"name": "customer_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {
                    "200": {
                        "description": "Customer details",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Customer"}
                            }
                        }
                    }
                }
            },
            "put": {
                "summary": "Update customer",
                "operationId": "updateCustomer",
                "parameters": [
                    {"name": "customer_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/CustomerUpdate"}
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Customer updated",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Customer"}
                            }
                        }
                    }
                }
            }
        },
        
        # Inventory Endpoints
        "/inventory/products": {
            "get": {
                "summary": "List products",
                "operationId": "listProducts",
                "parameters": [
                    {"name": "page", "in": "query", "schema": {"type": "integer", "default": 1}},
                    {"name": "page_size", "in": "query", "schema": {"type": "integer", "default": 20}},
                    {"name": "category_id", "in": "query", "schema": {"type": "integer"}},
                    {"name": "search", "in": "query", "schema": {"type": "string"}}
                ],
                "responses": {
                    "200": {
                        "description": "List of products",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "items": {"type": "array", "items": {"$ref": "#/components/schemas/Product"}},
                                        "total": {"type": "integer"},
                                        "page": {"type": "integer"},
                                        "page_size": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "post": {
                "summary": "Create product",
                "operationId": "createProduct",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ProductCreate"}
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Product created",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Product"}
                            }
                        }
                    }
                }
            }
        },
        "/inventory/products/{product_id}": {
            "get": {
                "summary": "Get product",
                "operationId": "getProduct",
                "parameters": [
                    {"name": "product_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {
                    "200": {
                        "description": "Product details",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Product"}
                            }
                        }
                    }
                }
            },
            "put": {
                "summary": "Update product",
                "operationId": "updateProduct",
                "parameters": [
                    {"name": "product_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ProductUpdate"}
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Product updated",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Product"}
                            }
                        }
                    }
                }
            }
        },
        "/inventory/products/{product_id}/adjust_stock": {
            "post": {
                "summary": "Adjust stock level",
                "operationId": "adjustStock",
                "parameters": [
                    {"name": "product_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "quantity": {"type": "integer"},
                                    "reason": {"type": "string"},
                                    "location_id": {"type": "integer"}
                                },
                                "required": ["quantity", "reason"]
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Stock adjusted"
                    }
                }
            }
        }
    },
    "components": {
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            },
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key"
            }
        },
        "schemas": {
            # Base schemas
            "HealthStatus": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["healthy", "degraded", "unhealthy"]},
                    "version": {"type": "string"},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "components": {"type": "object", "additionalProperties": {"type": "object"}}
                }
            },
            "User": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "username": {"type": "string"},
                    "email": {"type": "string", "format": "email"},
                    "full_name": {"type": "string"},
                    "is_active": {"type": "boolean"},
                    "created_at": {"type": "string", "format": "date-time"},
                    "role_ids": {"type": "array", "items": {"type": "integer"}}
                }
            },
            
            # CRM schemas
            "Customer": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "email": {"type": "string", "format": "email"},
                    "phone": {"type": "string"},
                    "company": {"type": "string"},
                    "address": {"type": "string"},
                    "city": {"type": "string"},
                    "state": {"type": "string"},
                    "country": {"type": "string"},
                    "postal_code": {"type": "string"},
                    "status": {"type": "string", "enum": ["active", "inactive", "lead"]},
                    "notes": {"type": "string"},
                    "created_at": {"type": "string", "format": "date-time"},
                    "updated_at": {"type": "string", "format": "date-time"},
                    "tags": {"type": "array", "items": {"type": "string"}}
                }
            },
            "CustomerCreate": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "minLength": 1, "maxLength": 200},
                    "email": {"type": "string", "format": "email"},
                    "phone": {"type": "string", "maxLength": 20},
                    "company": {"type": "string", "maxLength": 200},
                    "address": {"type": "string", "maxLength": 500},
                    "city": {"type": "string", "maxLength": 100},
                    "state": {"type": "string", "maxLength": 100},
                    "country": {"type": "string", "maxLength": 100},
                    "postal_code": {"type": "string", "maxLength": 20},
                    "status": {"type": "string", "default": "active"},
                    "notes": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["name"]
            },
            "CustomerUpdate": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "minLength": 1, "maxLength": 200},
                    "email": {"type": "string", "format": "email"},
                    "phone": {"type": "string", "maxLength": 20},
                    "company": {"type": "string", "maxLength": 200},
                    "status": {"type": "string", "enum": ["active", "inactive", "lead"]},
                    "notes": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}}
                }
            },
            
            # Inventory schemas
            "Product": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "sku": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "category_id": {"type": "integer"},
                    "unit_price": {"type": "number", "minimum": 0},
                    "cost_price": {"type": "number", "minimum": 0},
                    "quantity_on_hand": {"type": "integer", "minimum": 0},
                    "quantity_reserved": {"type": "integer", "minimum": 0},
                    "quantity_available": {"type": "integer", "minimum": 0},
                    "reorder_point": {"type": "integer", "minimum": 0},
                    "reorder_quantity": {"type": "integer", "minimum": 0},
                    "unit_of_measure": {"type": "string"},
                    "is_active": {"type": "boolean"},
                    "created_at": {"type": "string", "format": "date-time"},
                    "tags": {"type": "array", "items": {"type": "string"}}
                }
            },
            "ProductCreate": {
                "type": "object",
                "properties": {
                    "sku": {"type": "string", "minLength": 1, "maxLength": 50},
                    "name": {"type": "string", "minLength": 1, "maxLength": 200},
                    "description": {"type": "string"},
                    "category_id": {"type": "integer"},
                    "unit_price": {"type": "number", "minimum": 0},
                    "cost_price": {"type": "number", "minimum": 0},
                    "reorder_point": {"type": "integer", "minimum": 0},
                    "reorder_quantity": {"type": "integer", "minimum": 0},
                    "unit_of_measure": {"type": "string", "default": "unit"},
                    "tags": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["sku", "name", "unit_price"]
            },
            "ProductUpdate": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "minLength": 1, "maxLength": 200},
                    "description": {"type": "string"},
                    "category_id": {"type": "integer"},
                    "unit_price": {"type": "number", "minimum": 0},
                    "cost_price": {"type": "number", "minimum": 0},
                    "reorder_point": {"type": "integer", "minimum": 0},
                    "reorder_quantity": {"type": "integer", "minimum": 0},
                    "unit_of_measure": {"type": "string"},
                    "is_active": {"type": "boolean"},
                    "tags": {"type": "array", "items": {"type": "string"}}
                }
            }
        }
    }
}

__all__ = ["OPENAPI_SPEC"]

// Re-export all module types for unified imports
export * from './mrp';
export * from './hr';
export * from './pos';
export * from './ecommerce';

// Common types used across modules
export interface PaginationParams {
  page?: number;
  limit?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  totalPages: number;
  hasNext: boolean;
  hasPrev: boolean;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, string[]>;
  timestamp: string;
  path: string;
}

export interface AuditLog {
  id: string;
  userId: string;
  userName: string;
  action: string;
  entityType: string;
  entityId: string;
  oldValues?: Record<string, any>;
  newValues?: Record<string, any>;
  ipAddress?: string;
  userAgent?: string;
  createdAt: string;
}

export interface Notification {
  id: string;
  userId: string;
  title: string;
  body: string;
  type: 'info' | 'warning' | 'error' | 'success';
  module: string;
  entityType?: string;
  entityId?: string;
  isRead: boolean;
  readAt?: string;
  createdAt: string;
  metadata?: Record<string, any>;
}

export interface ActivityFeedItem {
  id: string;
  userId: string;
  userName: string;
  userAvatar?: string;
  action: string;
  module: string;
  entityType: string;
  entityId: string;
  entityName: string;
  description: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface DashboardWidget {
  id: string;
  type: 'kpi' | 'chart' | 'list' | 'table' | 'alert';
  title: string;
  module: string;
  position: { x: number; y: number; w: number; h: number };
  config: Record<string, any>;
  isVisible: boolean;
  refreshInterval?: number;
}

export interface FilterState {
  search?: string;
  dateFrom?: string;
  dateTo?: string;
  status?: string[];
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  customFilters?: Record<string, any>;
}

export interface ExportOptions {
  format: 'csv' | 'excel' | 'pdf' | 'json';
  columns: string[];
  filters?: FilterState;
  includeHeaders?: boolean;
  dateFormat?: string;
  timezone?: string;
}

export interface ImportResult {
  totalRows: number;
  successfulRows: number;
  failedRows: number;
  errors: Array<{
    row: number;
    field: string;
    message: string;
    value: any;
  }>;
  warnings: Array<{
    row: number;
    field: string;
    message: string;
    value: any;
  }>;
}

export interface BulkAction {
  id: string;
  label: string;
  icon: string;
  module: string;
  action: string;
  requiresConfirmation: boolean;
  confirmationMessage?: string;
  allowedRoles: string[];
}

export interface Permission {
  resource: string;
  action: 'create' | 'read' | 'update' | 'delete' | 'manage' | 'export' | 'import';
  conditions?: Record<string, any>;
}

export interface Role {
  id: string;
  name: string;
  description: string;
  permissions: Permission[];
  isSystem: boolean;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  version: string;
  uptime: number;
  checks: {
    database: { status: 'up' | 'down'; latency: number };
    redis: { status: 'up' | 'down'; latency: number };
    storage: { status: 'up' | 'down'; latency: number };
    externalApis: { status: 'up' | 'down'; latency: number };
  };
  metrics: {
    cpuUsage: number;
    memoryUsage: number;
    diskUsage: number;
    activeConnections: number;
    queueDepth: number;
  };
}

export interface WebSocketMessage {
  type: 'notification' | 'activity' | 'update' | 'alert' | 'sync';
  module: string;
  action: string;
  payload: any;
  timestamp: string;
  senderId?: string;
}


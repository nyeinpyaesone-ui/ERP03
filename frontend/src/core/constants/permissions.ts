/**
 * Permissions and Roles Constants
 * Standardized permission and role definitions for RBAC
 * 
 * @module core/constants/permissions
 */

/**
 * System roles
 */
export const ROLES = {
  SUPER_ADMIN: 'super_admin',
  ADMIN: 'admin',
  MANAGER: 'manager',
  SUPERVISOR: 'supervisor',
  USER: 'user',
  GUEST: 'guest',
  VIEWER: 'viewer',
} as const;

/**
 * Permission categories
 */
export const PERMISSION_CATEGORIES = {
  USERS: 'users',
  ROLES: 'roles',
  INVENTORY: 'inventory',
  ORDERS: 'orders',
  REPORTS: 'reports',
  SETTINGS: 'settings',
  ADMIN: 'admin',
} as const;

/**
 * Permission actions
 */
export const PERMISSION_ACTIONS = {
  CREATE: 'create',
  READ: 'read',
  UPDATE: 'update',
  DELETE: 'delete',
  APPROVE: 'approve',
  REJECT: 'reject',
  EXPORT: 'export',
  IMPORT: 'import',
  SHARE: 'share',
  ARCHIVE: 'archive',
} as const;

/**
 * All permissions organized by category
 */
export const PERMISSIONS = {
  // User management
  USERS_CREATE: 'users:create',
  USERS_READ: 'users:read',
  USERS_UPDATE: 'users:update',
  USERS_DELETE: 'users:delete',
  USERS_LIST: 'users:list',
  
  // Role management
  ROLES_CREATE: 'roles:create',
  ROLES_READ: 'roles:read',
  ROLES_UPDATE: 'roles:update',
  ROLES_DELETE: 'roles:delete',
  ROLES_ASSIGN: 'roles:assign',
  
  // Inventory
  INVENTORY_CREATE: 'inventory:create',
  INVENTORY_READ: 'inventory:read',
  INVENTORY_UPDATE: 'inventory:update',
  INVENTORY_DELETE: 'inventory:delete',
  INVENTORY_ADJUST: 'inventory:adjust',
  INVENTORY_COUNT: 'inventory:count',
  
  // Orders
  ORDERS_CREATE: 'orders:create',
  ORDERS_READ: 'orders:read',
  ORDERS_UPDATE: 'orders:update',
  ORDERS_DELETE: 'orders:delete',
  ORDERS_APPROVE: 'orders:approve',
  ORDERS_CANCEL: 'orders:cancel',
  ORDERS_REFUND: 'orders:refund',
  
  // Reports
  REPORTS_VIEW: 'reports:view',
  REPORTS_EXPORT: 'reports:export',
  REPORTS_SCHEDULE: 'reports:schedule',
  
  // Settings
  SETTINGS_VIEW: 'settings:view',
  SETTINGS_UPDATE: 'settings:update',
  
  // Admin
  ADMIN_ACCESS: 'admin:access',
  ADMIN_AUDIT_LOGS: 'admin:audit_logs',
  ADMIN_SYSTEM_CONFIG: 'admin:system_config',
  ADMIN_BACKUP_RESTORE: 'admin:backup_restore',
} as const;

/**
 * Default role permissions mapping
 */
export const ROLE_PERMISSIONS: Record<string, string[]> = {
  [ROLES.SUPER_ADMIN]: Object.values(PERMISSIONS),
  
  [ROLES.ADMIN]: [
    PERMISSIONS.USERS_READ,
    PERMISSIONS.USERS_UPDATE,
    PERMISSIONS.ROLES_READ,
    PERMISSIONS.INVENTORY_CREATE,
    PERMISSIONS.INVENTORY_READ,
    PERMISSIONS.INVENTORY_UPDATE,
    PERMISSIONS.INVENTORY_DELETE,
    PERMISSIONS.ORDERS_CREATE,
    PERMISSIONS.ORDERS_READ,
    PERMISSIONS.ORDERS_UPDATE,
    PERMISSIONS.ORDERS_DELETE,
    PERMISSIONS.ORDERS_APPROVE,
    PERMISSIONS.REPORTS_VIEW,
    PERMISSIONS.REPORTS_EXPORT,
    PERMISSIONS.SETTINGS_VIEW,
    PERMISSIONS.SETTINGS_UPDATE,
  ],
  
  [ROLES.MANAGER]: [
    PERMISSIONS.USERS_READ,
    PERMISSIONS.INVENTORY_CREATE,
    PERMISSIONS.INVENTORY_READ,
    PERMISSIONS.INVENTORY_UPDATE,
    PERMISSIONS.ORDERS_CREATE,
    PERMISSIONS.ORDERS_READ,
    PERMISSIONS.ORDERS_UPDATE,
    PERMISSIONS.ORDERS_APPROVE,
    PERMISSIONS.REPORTS_VIEW,
    PERMISSIONS.REPORTS_EXPORT,
  ],
  
  [ROLES.SUPERVISOR]: [
    PERMISSIONS.INVENTORY_READ,
    PERMISSIONS.ORDERS_CREATE,
    PERMISSIONS.ORDERS_READ,
    PERMISSIONS.ORDERS_UPDATE,
    PERMISSIONS.REPORTS_VIEW,
  ],
  
  [ROLES.USER]: [
    PERMISSIONS.INVENTORY_READ,
    PERMISSIONS.ORDERS_CREATE,
    PERMISSIONS.ORDERS_READ,
  ],
  
  [ROLES.VIEWER]: [
    PERMISSIONS.INVENTORY_READ,
    PERMISSIONS.ORDERS_READ,
    PERMISSIONS.REPORTS_VIEW,
  ],
  
  [ROLES.GUEST]: [],
};

/**
 * Check if role has permission
 */
export function hasPermission(role: string, permission: string): boolean {
  const rolePermissions = ROLE_PERMISSIONS[role] || [];
  return rolePermissions.includes(permission);
}

/**
 * Get all permissions for a role
 */
export function getRolePermissions(role: string): string[] {
  return ROLE_PERMISSIONS[role] || [];
}

/**
 * Check if user has any of the required permissions
 */
export function hasAnyPermission(role: string, permissions: string[]): boolean {
  return permissions.some(permission => hasPermission(role, permission));
}

/**
 * Check if user has all required permissions
 */
export function hasAllPermissions(role: string, permissions: string[]): boolean {
  return permissions.every(permission => hasPermission(role, permission));
}

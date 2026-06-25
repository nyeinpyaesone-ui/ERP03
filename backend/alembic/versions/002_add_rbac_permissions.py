"""Add RBAC permissions system

Revision ID: 002
Revises: 001
Create Date: 2024-06-15 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Roles table
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Permissions table
    op.create_table(
        'permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('resource', sa.String(length=100), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Role-Permission junction
    op.create_table(
        'role_permissions',
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('role_id', 'permission_id')
    )

    # User-Role junction (many-to-many)
    op.create_table(
        'user_roles',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'role_id')
    )

    # Field-level permissions
    op.create_table(
        'field_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('resource', sa.String(length=100), nullable=False),
        sa.Column('field_name', sa.String(length=100), nullable=False),
        sa.Column('access_level', sa.String(length=20), nullable=False, server_default='read'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('role_id', 'resource', 'field_name', name='uq_field_permission')
    )

    # Data policies (row-level access)
    op.create_table(
        'data_policies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('resource', sa.String(length=100), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('condition', postgresql.JSONB(), nullable=True),
        sa.Column('effect', sa.String(length=20), nullable=False, server_default='allow'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Insert default roles
    op.execute("""
        INSERT INTO roles (name, display_name, description, is_system) VALUES
        ('superadmin', 'Super Administrator', 'Full system access', true),
        ('admin', 'Administrator', 'Admin access to all modules', true),
        ('manager', 'Manager', 'Can manage team data and view reports', true),
        ('user', 'Standard User', 'Can create and edit own records', true),
        ('viewer', 'Viewer', 'Read-only access to assigned data', true)
    """)

    # Insert default permissions
    op.execute("""
        INSERT INTO permissions (name, resource, action, description) VALUES
        ('users.read', 'users', 'read', 'View user profiles'),
        ('users.create', 'users', 'create', 'Create new users'),
        ('users.update', 'users', 'update', 'Edit user profiles'),
        ('users.delete', 'users', 'delete', 'Delete users'),
        ('contacts.read', 'contacts', 'read', 'View contacts'),
        ('contacts.create', 'contacts', 'create', 'Create contacts'),
        ('contacts.update', 'contacts', 'update', 'Edit contacts'),
        ('contacts.delete', 'contacts', 'delete', 'Delete contacts'),
        ('companies.read', 'companies', 'read', 'View companies'),
        ('companies.create', 'companies', 'create', 'Create companies'),
        ('companies.update', 'companies', 'update', 'Edit companies'),
        ('companies.delete', 'companies', 'delete', 'Delete companies'),
        ('deals.read', 'deals', 'read', 'View deals'),
        ('deals.create', 'deals', 'create', 'Create deals'),
        ('deals.update', 'deals', 'update', 'Edit deals'),
        ('deals.delete', 'deals', 'delete', 'Delete deals'),
        ('products.read', 'products', 'read', 'View products'),
        ('products.create', 'products', 'create', 'Create products'),
        ('products.update', 'products', 'update', 'Edit products'),
        ('products.delete', 'products', 'delete', 'Delete products'),
        ('invoices.read', 'invoices', 'read', 'View invoices'),
        ('invoices.create', 'invoices', 'create', 'Create invoices'),
        ('invoices.update', 'invoices', 'update', 'Edit invoices'),
        ('invoices.delete', 'invoices', 'delete', 'Delete invoices'),
        ('employees.read', 'employees', 'read', 'View employees'),
        ('employees.create', 'employees', 'create', 'Create employees'),
        ('employees.update', 'employees', 'update', 'Edit employees'),
        ('employees.delete', 'employees', 'delete', 'Delete employees'),
        ('projects.read', 'projects', 'read', 'View projects'),
        ('projects.create', 'projects', 'create', 'Create projects'),
        ('projects.update', 'projects', 'update', 'Edit projects'),
        ('projects.delete', 'projects', 'delete', 'Delete projects'),
        ('reports.read', 'reports', 'read', 'View reports'),
        ('reports.create', 'reports', 'create', 'Create reports'),
        ('settings.read', 'settings', 'read', 'View settings'),
        ('settings.update', 'settings', 'update', 'Edit settings'),
        ('workflows.read', 'workflows', 'read', 'View workflows'),
        ('workflows.create', 'workflows', 'create', 'Create workflows'),
        ('workflows.update', 'workflows', 'update', 'Edit workflows'),
        ('workflows.delete', 'workflows', 'delete', 'Delete workflows'),
        ('admin.access', 'admin', 'access', 'Access admin panel'),
        ('bulk.import', 'bulk', 'import', 'Import data'),
        ('bulk.export', 'bulk', 'export', 'Export data'),
        ('migrations.manage', 'migrations', 'manage', 'Manage database migrations')
    """)

    # Assign all permissions to superadmin
    op.execute("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id FROM roles r, permissions p WHERE r.name = 'superadmin'
    """)

    # Assign permissions to admin (all except migrations.manage)
    op.execute("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id FROM roles r, permissions p
        WHERE r.name = 'admin' AND p.name != 'migrations.manage'
    """)

    # Assign basic permissions to manager
    op.execute("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id FROM roles r, permissions p
        WHERE r.name = 'manager' AND p.action IN ('read', 'create', 'update') AND p.resource NOT IN ('users', 'settings', 'migrations')
    """)

    # Assign read-only to viewer
    op.execute("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id FROM roles r, permissions p
        WHERE r.name = 'viewer' AND p.action = 'read'
    """)

    # Assign basic permissions to user
    op.execute("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id FROM roles r, permissions p
        WHERE r.name = 'user' AND p.action IN ('read', 'create', 'update') AND p.resource NOT IN ('users', 'settings', 'migrations', 'admin')
    """)

    # Insert default field permissions (hide salary from non-managers)
    op.execute("""
        INSERT INTO field_permissions (role_id, resource, field_name, access_level)
        SELECT r.id, 'employees', 'salary', 'hidden'
        FROM roles r WHERE r.name IN ('user', 'viewer')
    """)

    op.execute("""
        INSERT INTO field_permissions (role_id, resource, field_name, access_level)
        SELECT r.id, 'employees', 'cost_price', 'hidden'
        FROM roles r WHERE r.name IN ('user', 'viewer')
    """)

    op.execute("""
        INSERT INTO field_permissions (role_id, resource, field_name, access_level)
        SELECT r.id, 'contacts', 'lifetime_value', 'hidden'
        FROM roles r WHERE r.name = 'viewer'
    """)

def downgrade() -> None:
    op.drop_table('data_policies')
    op.drop_table('field_permissions')
    op.drop_table('user_roles')
    op.drop_table('role_permissions')
    op.drop_table('permissions')
    op.drop_table('roles')


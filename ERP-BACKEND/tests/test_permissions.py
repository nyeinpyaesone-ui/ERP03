"""
Unit tests for the permissions service (app/services/permissions.py).
"""
import pytest
from unittest.mock import MagicMock, patch

from app.services.permissions import (
    has_permission,
    require_permission,
    get_user_permissions,
    get_field_permissions,
    filter_fields,
    check_data_policy,
    matches_condition,
    permission_required,
    PermissionDenied
)
from app.models import User, Role, Permission, FieldPermission, DataPolicy


class TestHasPermission:
    """Tests for has_permission function."""

    def test_has_permission_user_inactive(self, sample_user):
        """Test inactive user has no permissions."""
        sample_user.is_active = False
        db = MagicMock()
        
        result = has_permission(sample_user, "contacts", "read", db)
        
        assert result is False

    def test_has_permission_superadmin_bypass(self, sample_superadmin):
        """Test superadmin bypasses all permission checks."""
        role = Role(id=1, name="superadmin")
        sample_superadmin.roles = [role]
        db = MagicMock()
        
        result = has_permission(sample_superadmin, "any_resource", "any_action", db)
        
        assert result is True

    def test_has_permission_with_matching_permission(self, sample_user, mock_db):
        """Test user with matching permission returns True."""
        role = Role(id=1, name="user")
        perm = Permission(id=1, resource="contacts", action="read")
        role.permissions = [perm]
        sample_user.roles = [role]
        
        result = has_permission(sample_user, "contacts", "read", mock_db)
        
        assert result is True

    def test_has_permission_without_matching_permission(self, sample_user, mock_db):
        """Test user without matching permission returns False."""
        role = Role(id=1, name="user")
        perm = Permission(id=1, resource="contacts", action="read")
        role.permissions = [perm]
        sample_user.roles = [role]
        
        result = has_permission(sample_user, "deals", "delete", mock_db)
        
        assert result is False

    def test_has_permission_multiple_roles(self, sample_user, mock_db):
        """Test user with multiple roles checks all permissions."""
        role1 = Role(id=1, name="user")
        role2 = Role(id=2, name="manager")
        perm1 = Permission(id=1, resource="contacts", action="read")
        perm2 = Permission(id=2, resource="deals", action="write")
        role1.permissions = [perm1]
        role2.permissions = [perm2]
        sample_user.roles = [role1, role2]
        
        # Should find permission in second role
        result = has_permission(sample_user, "deals", "write", mock_db)
        
        assert result is True


class TestGetUserPermissions:
    """Tests for get_user_permissions function."""

    def test_get_user_permissions_empty(self, sample_user, mock_db):
        """Test user with no roles returns empty list."""
        sample_user.roles = []
        
        result = get_user_permissions(sample_user, mock_db)
        
        assert result == []

    def test_get_user_permissions_single_role(self, sample_user, mock_db):
        """Test user with single role returns correct permissions."""
        role = Role(id=1, name="user")
        perm1 = Permission(id=1, resource="contacts", action="read")
        perm2 = Permission(id=2, resource="contacts", action="write")
        role.permissions = [perm1, perm2]
        sample_user.roles = [role]
        
        result = get_user_permissions(sample_user, mock_db)
        
        assert "contacts.read" in result
        assert "contacts.write" in result
        assert len(result) == 2

    def test_get_user_permissions_multiple_roles_duplicate(self, sample_user, mock_db):
        """Test duplicate permissions across roles are deduplicated."""
        role1 = Role(id=1, name="user")
        role2 = Role(id=2, name="manager")
        perm1 = Permission(id=1, resource="contacts", action="read")
        perm2 = Permission(id=2, resource="contacts", action="read")  # Same as perm1
        role1.permissions = [perm1]
        role2.permissions = [perm2]
        sample_user.roles = [role1, role2]
        
        result = get_user_permissions(sample_user, mock_db)
        
        assert "contacts.read" in result
        assert len(result) == 1  # Deduplicated


class TestGetFieldPermissions:
    """Tests for get_field_permissions function."""

    def test_get_field_permissions_empty(self, sample_user, mock_db):
        """Test user with no field permissions returns empty dict."""
        sample_user.roles = []
        
        result = get_field_permissions(sample_user, "contacts", mock_db)
        
        assert result == {}

    def test_get_field_permissions_higher_access_wins(self, sample_user, mock_db):
        """Test higher access level wins when same field has multiple permissions."""
        role = Role(id=1, name="user")
        fp1 = FieldPermission(id=1, resource="contacts", field_name="email", access_level="read")
        fp2 = FieldPermission(id=2, resource="contacts", field_name="email", access_level="write")
        role.field_permissions = [fp1, fp2]
        sample_user.roles = [role]
        
        result = get_field_permissions(sample_user, "contacts", mock_db)
        
        assert result["email"] == "write"

    def test_get_field_permissions_hidden_default(self, sample_user, mock_db):
        """Test fields not in permissions default to hidden."""
        role = Role(id=1, name="user")
        fp = FieldPermission(id=1, resource="contacts", field_name="name", access_level="read")
        role.field_permissions = [fp]
        sample_user.roles = [role]
        
        result = get_field_permissions(sample_user, "contacts", mock_db)
        
        assert "name" in result
        assert "email" not in result  # Not defined, defaults to hidden


class TestFilterFields:
    """Tests for filter_fields function."""

    def test_filter_fields_dict_hidden(self, sample_user, mock_db):
        """Test filtering hidden fields from dict."""
        role = Role(id=1, name="user")
        fp = FieldPermission(id=1, resource="contacts", field_name="email", access_level="hidden")
        role.field_permissions = [fp]
        sample_user.roles = [role]
        
        data = {"name": "John", "email": "john@example.com", "phone": "123"}
        result = filter_fields(data, sample_user, "contacts", mock_db)
        
        assert "name" in result
        assert "phone" in result
        assert "email" not in result

    def test_filter_fields_list(self, sample_user, mock_db):
        """Test filtering hidden fields from list of dicts."""
        role = Role(id=1, name="user")
        fp = FieldPermission(id=1, resource="contacts", field_name="salary", access_level="hidden")
        role.field_permissions = [fp]
        sample_user.roles = [role]
        
        data = [
            {"name": "John", "salary": 50000},
            {"name": "Jane", "salary": 60000}
        ]
        result = filter_fields(data, sample_user, "contacts", mock_db)
        
        assert len(result) == 2
        assert "salary" not in result[0]
        assert "salary" not in result[1]

    def test_filter_fields_non_dict_returns_as_is(self, sample_user, mock_db):
        """Test non-dict/list data returns unchanged."""
        sample_user.roles = []
        
        result = filter_fields("string", sample_user, "contacts", mock_db)
        
        assert result == "string"


class TestMatchesCondition:
    """Tests for matches_condition function."""

    def test_matches_condition_empty(self):
        """Test empty condition matches everything."""
        record = {"status": "active"}
        result = matches_condition(record, {})
        assert result is True

    def test_matches_condition_simple_eq(self):
        """Test simple equality match."""
        record = {"status": "active", "value": 100}
        condition = {"status": "active"}
        result = matches_condition(record, condition)
        assert result is True

    def test_matches_condition_simple_ne(self):
        """Test not equal match fails."""
        record = {"status": "active"}
        condition = {"status": "inactive"}
        result = matches_condition(record, condition)
        assert result is False

    def test_matches_condition_operator_gt(self):
        """Test greater than operator."""
        record = {"value": 100}
        condition = {"value": {"gt": 50}}
        result = matches_condition(record, condition)
        assert result is True

    def test_matches_condition_operator_lt(self):
        """Test less than operator."""
        record = {"value": 100}
        condition = {"value": {"lt": 50}}
        result = matches_condition(record, condition)
        assert result is False

    def test_matches_condition_operator_in(self):
        """Test 'in' operator."""
        record = {"status": "active"}
        condition = {"status": {"in": ["active", "pending"]}}
        result = matches_condition(record, condition)
        assert result is True

    def test_matches_condition_and(self):
        """Test _and logical operator."""
        record = {"status": "active", "value": 100}
        condition = {
            "_and": [
                {"status": "active"},
                {"value": {"gt": 50}}
            ]
        }
        result = matches_condition(record, condition)
        assert result is True

    def test_matches_condition_or(self):
        """Test _or logical operator."""
        record = {"status": "active"}
        condition = {
            "_or": [
                {"status": "pending"},
                {"status": "active"}
            ]
        }
        result = matches_condition(record, condition)
        assert result is True

    def test_matches_condition_null_value(self):
        """Test comparison with null value."""
        record = {"value": None}
        condition = {"value": {"gt": 50}}
        result = matches_condition(record, condition)
        assert result is False


class TestCheckDataPolicy:
    """Tests for check_data_policy function."""

    def test_check_data_policy_no_policies(self, sample_user, mock_db):
        """Test no policies means default allow."""
        sample_user.roles = []
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        
        record = {"id": 1, "status": "active"}
        result = check_data_policy(sample_user, "contacts", record, mock_db)
        
        assert result is True

    def test_check_data_policy_deny_effect(self, sample_user, mock_db):
        """Test deny policy blocks access."""
        role = Role(id=1, name="user")
        sample_user.roles = [role]
        
        policy = DataPolicy(
            id=1,
            role_id=1,
            resource="contacts",
            effect="deny",
            condition={"status": "archived"},
            is_active=True,
            priority=1
        )
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [policy]
        
        record = {"id": 1, "status": "archived"}
        result = check_data_policy(sample_user, "contacts", record, mock_db)
        
        assert result is False

    def test_check_data_policy_allow_effect(self, sample_user, mock_db):
        """Test allow policy grants access."""
        role = Role(id=1, name="user")
        sample_user.roles = [role]
        
        policy = DataPolicy(
            id=1,
            role_id=1,
            resource="contacts",
            effect="allow",
            condition={"status": "active"},
            is_active=True,
            priority=1
        )
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [policy]
        
        record = {"id": 1, "status": "active"}
        result = check_data_policy(sample_user, "contacts", record, mock_db)
        
        assert result is True


class TestRequirePermission:
    """Tests for require_permission dependency."""

    @pytest.mark.asyncio
    async def test_require_permission_granted(self, sample_user, mock_db):
        """Test require_permission when permission is granted."""
        role = Role(id=1, name="user")
        perm = Permission(id=1, resource="contacts", action="read")
        role.permissions = [perm]
        sample_user.roles = [role]
        
        # Mock request
        request = MagicMock()
        
        with patch('app.services.permissions.get_current_user') as mock_auth:
            mock_auth.return_value = sample_user
            
            checker = require_permission("contacts", "read")
            
            # Note: This would normally be called by FastAPI's Depends
            # Here we just verify it doesn't raise
            result = checker(request=request, current_user=sample_user, db=mock_db)
            assert result == sample_user

    @pytest.mark.asyncio
    async def test_require_permission_denied(self, sample_user, mock_db):
        """Test require_permission when permission is denied raises HTTPException."""
        from fastapi import HTTPException
        
        sample_user.roles = []
        request = MagicMock()
        
        checker = require_permission("contacts", "delete")
        
        with pytest.raises(HTTPException) as exc_info:
            checker(request=request, current_user=sample_user, db=mock_db)
        
        assert exc_info.value.status_code == 403
        assert "Permission denied" in exc_info.value.detail


class TestPermissionRequiredDecorator:
    """Tests for permission_required decorator."""

    @pytest.mark.asyncio
    async def test_permission_required_decorator_granted(self, sample_user, mock_db):
        """Test decorator allows access when permission granted."""
        role = Role(id=1, name="user")
        perm = Permission(id=1, resource="contacts", action="read")
        role.permissions = [perm]
        sample_user.roles = [role]
        
        @permission_required("contacts", "read")
        async def test_func(current_user=None, db=None):
            return "success"
        
        result = await test_func(current_user=sample_user, db=mock_db)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_permission_required_decorator_denied(self, sample_user, mock_db):
        """Test decorator denies access when permission not granted."""
        from fastapi import HTTPException
        
        sample_user.roles = []
        
        @permission_required("contacts", "delete")
        async def test_func(current_user=None, db=None):
            return "success"
        
        with pytest.raises(HTTPException) as exc_info:
            await test_func(current_user=sample_user, db=mock_db)
        
        assert exc_info.value.status_code == 403

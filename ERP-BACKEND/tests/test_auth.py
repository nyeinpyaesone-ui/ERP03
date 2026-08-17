"""
Unit tests for the authentication module (app/auth.py).
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from fastapi import HTTPException

from app.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_token,
    get_current_user,
    require_admin,
    get_current_user_optional,
    pwd_context,
    oauth2_scheme
)
from app.models import User


class TestVerifyPassword:
    """Tests for verify_password function."""

    def test_verify_password_correct(self, mock_pwd_context):
        """Test verifying a correct password."""
        result = verify_password("plain_password", "hashed_password")
        assert result is True
        mock_pwd_context.verify.assert_called_once_with("plain_password", "hashed_password")

    def test_verify_password_incorrect(self, mock_pwd_context):
        """Test verifying an incorrect password."""
        mock_pwd_context.verify.return_value = False
        result = verify_password("wrong_password", "hashed_password")
        assert result is False


class TestGetPasswordHash:
    """Tests for get_password_hash function."""

    def test_get_password_hash(self, mock_pwd_context):
        """Test hashing a password."""
        result = get_password_hash("plain_password")
        assert result == "hashed_password"
        mock_pwd_context.hash.assert_called_once_with("plain_password")


class TestCreateAccessToken:
    """Tests for create_access_token function."""

    @patch('app.auth.jwt.encode')
    def test_create_access_token_with_default_expiry(self, mock_jwt_encode, test_settings):
        """Test creating access token with default expiry."""
        with patch('app.auth.settings', test_settings):
            data = {"sub": "1"}
            token = create_access_token(data)
            
            mock_jwt_encode.assert_called_once()
            call_args = mock_jwt_encode.call_args[0][0]
            assert call_args["sub"] == "1"
            assert "exp" in call_args  # Just verify exp exists

    @patch('app.auth.jwt.encode')
    def test_create_access_token_with_custom_expiry(self, mock_jwt_encode, test_settings):
        """Test creating access token with custom expiry."""
        with patch('app.auth.settings', test_settings):
            data = {"sub": "1"}
            expires_delta = timedelta(hours=2)
            token = create_access_token(data, expires_delta=expires_delta)
            
            mock_jwt_encode.assert_called_once()


class TestDecodeToken:
    """Tests for decode_token function."""

    @patch('app.auth.jwt.decode')
    def test_decode_token_valid(self, mock_jwt_decode, test_settings):
        """Test decoding a valid token."""
        with patch('app.auth.settings', test_settings):
            mock_jwt_decode.return_value = {"sub": "1", "exp": 9999999999}
            
            result = decode_token("valid_token")
            
            assert result == {"sub": "1", "exp": 9999999999}
            mock_jwt_decode.assert_called_once_with(
                "valid_token",
                test_settings.SECRET_KEY,
                algorithms=[test_settings.ALGORITHM]
            )

    @patch('app.auth.jwt.decode')
    def test_decode_token_invalid(self, mock_jwt_decode, test_settings):
        """Test decoding an invalid token raises HTTPException."""
        from jose import JWTError
        
        with patch('app.auth.settings', test_settings):
            mock_jwt_decode.side_effect = JWTError("Invalid token")
            
            with pytest.raises(HTTPException) as exc_info:
                decode_token("invalid_token")
            
            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "Invalid token"


class TestGetCurrentUser:
    """Tests for get_current_user function."""

    @pytest.mark.asyncio
    @patch('app.auth.decode_token')
    async def test_get_current_user_valid(self, mock_decode, mock_db, sample_user, test_settings):
        """Test getting current user with valid token."""
        with patch('app.auth.settings', test_settings):
            mock_decode.return_value = {"sub": "1"}
            mock_query = MagicMock()
            mock_query.filter.return_value.first.return_value = sample_user
            mock_db.query.return_value = mock_query
            
            result = await get_current_user(token="valid_token", db=mock_db)
            
            assert result == sample_user
            mock_decode.assert_called_once_with("valid_token")

    @pytest.mark.asyncio
    @patch('app.auth.decode_token')
    async def test_get_current_user_invalid_token_no_sub(self, mock_decode, mock_db, test_settings):
        """Test getting current user with invalid token (no sub)."""
        with patch('app.auth.settings', test_settings):
            mock_decode.return_value = {"exp": 9999999999}  # No 'sub' field
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(token="invalid_token", db=mock_db)
            
            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "Invalid token"

    @pytest.mark.asyncio
    @patch('app.auth.decode_token')
    async def test_get_current_user_not_found(self, mock_decode, mock_db, test_settings):
        """Test getting current user when user not found in DB."""
        with patch('app.auth.settings', test_settings):
            mock_decode.return_value = {"sub": "999"}
            mock_query = MagicMock()
            mock_query.filter.return_value.first.return_value = None
            mock_db.query.return_value = mock_query
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(token="valid_token", db=mock_db)
            
            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "User not found or inactive"

    @pytest.mark.asyncio
    @patch('app.auth.decode_token')
    async def test_get_current_user_inactive(self, mock_decode, mock_db, sample_user, test_settings):
        """Test getting current user when user is inactive."""
        with patch('app.auth.settings', test_settings):
            sample_user.is_active = False
            mock_decode.return_value = {"sub": "1"}
            mock_query = MagicMock()
            mock_query.filter.return_value.first.return_value = sample_user
            mock_db.query.return_value = mock_query
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(token="valid_token", db=mock_db)
            
            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "User not found or inactive"


class TestRequireAdmin:
    """Tests for require_admin function."""

    @pytest.mark.asyncio
    async def test_require_admin_user_is_admin(self, sample_admin):
        """Test require_admin with admin user."""
        result = await require_admin(current_user=sample_admin)
        assert result == sample_admin

    @pytest.mark.asyncio
    async def test_require_admin_user_is_superadmin(self, sample_superadmin):
        """Test require_admin with superadmin user."""
        result = await require_admin(current_user=sample_superadmin)
        assert result == sample_superadmin

    @pytest.mark.asyncio
    async def test_require_admin_user_not_admin(self, sample_user):
        """Test require_admin with non-admin user raises exception."""
        with pytest.raises(HTTPException) as exc_info:
            await require_admin(current_user=sample_user)
        
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Admin access required"


class TestGetCurrentUserOptional:
    """Tests for get_current_user_optional function."""

    @pytest.mark.asyncio
    @patch('app.auth.decode_token')
    async def test_get_current_user_optional_no_token(self, mock_decode, mock_db):
        """Test with no token returns None."""
        result = await get_current_user_optional(token=None, db=mock_db)
        assert result is None
        mock_decode.assert_not_called()

    @pytest.mark.asyncio
    @patch('app.auth.decode_token')
    async def test_get_current_user_optional_valid_token(self, mock_decode, mock_db, sample_user):
        """Test with valid token returns user."""
        mock_decode.return_value = {"sub": "1"}
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = sample_user
        mock_db.query.return_value = mock_query
        
        result = await get_current_user_optional(token="valid_token", db=mock_db)
        
        assert result == sample_user

    @pytest.mark.asyncio
    @patch('app.auth.decode_token')
    async def test_get_current_user_optional_invalid_token(self, mock_decode, mock_db):
        """Test with invalid token returns None."""
        mock_decode.side_effect = Exception("Invalid token")
        
        result = await get_current_user_optional(token="invalid_token", db=mock_db)
        
        assert result is None

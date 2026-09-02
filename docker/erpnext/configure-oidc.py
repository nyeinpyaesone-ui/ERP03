#!/usr/bin/env python3
"""
OIDC Configuration Script for ERPNext

This script configures OAuth/OIDC provider settings in ERPNext site_config.json
when OIDC_ENABLED environment variable is set to 'true'.

Environment Variables:
    OIDC_ENABLED: Set to 'true' to enable OIDC authentication
    OIDC_PROVIDER: Name of the OIDC provider (e.g., 'keycloak', 'google', 'auth0')
    OIDC_CLIENT_ID: OAuth2 Client ID
    OIDC_CLIENT_SECRET: OAuth2 Client Secret
    OIDC_REDIRECT_URI: Redirect URI for OAuth callback
    OIDC_SCOPE: OAuth scopes (default: 'openid profile email')
    OIDC_AUTHORIZATION_URL: Authorization endpoint URL
    OIDC_TOKEN_URL: Token endpoint URL
    OIDC_USERINFO_URL: Userinfo endpoint URL
    OIDC_JWKS_URL: JWKS endpoint URL for token validation
    OIDC_ISSUER: Issuer identifier
"""

import json
import os
import sys
from pathlib import Path


def get_env_bool(name: str, default: bool = False) -> bool:
    """Get boolean value from environment variable."""
    value = os.environ.get(name, '').lower()
    if value in ('true', '1', 'yes'):
        return True
    if value in ('false', '0', 'no'):
        return False
    return default


def get_env_str(name: str, default: str = '') -> str:
    """Get string value from environment variable."""
    return os.environ.get(name, default)


def configure_oidc(site_config_path: str) -> bool:
    """
    Configure OIDC settings in site_config.json.

    Args:
        site_config_path: Path to the site_config.json file

    Returns:
        True if configuration was applied, False otherwise
    """
    # Check if OIDC is enabled
    if not get_env_bool('OIDC_ENABLED'):
        print("[configure-oidc] OIDC is disabled (OIDC_ENABLED=false or not set)")
        return False

    # Required OIDC settings
    client_id = get_env_str('OIDC_CLIENT_ID')
    client_secret = get_env_str('OIDC_CLIENT_SECRET')
    redirect_uri = get_env_str('OIDC_REDIRECT_URI')
    provider = get_env_str('OIDC_PROVIDER', 'generic')

    if not client_id or not client_secret or not redirect_uri:
        print("[configure-oidc] Missing required OIDC environment variables:")
        if not client_id:
            print("  - OIDC_CLIENT_ID is required")
        if not client_secret:
            print("  - OIDC_CLIENT_SECRET is required")
        if not redirect_uri:
            print("  - OIDC_REDIRECT_URI is required")
        print("[configure-oidc] Skipping OIDC configuration")
        return False

    # Optional OIDC settings
    scope = get_env_str('OIDC_SCOPE', 'openid profile email')
    auth_url = get_env_str('OIDC_AUTHORIZATION_URL')
    token_url = get_env_str('OIDC_TOKEN_URL')
    userinfo_url = get_env_str('OIDC_USERINFO_URL')
    jwks_url = get_env_str('OIDC_JWKS_URL')
    issuer = get_env_str('OIDC_ISSUER')

    # Load existing site config
    config_path = Path(site_config_path)
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text())
        except json.JSONDecodeError as e:
            print(f"[configure-oidc] Error reading site_config.json: {e}")
            config = {}
    else:
        config = {}
        config_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure social login providers in ERPNext format
    # ERPNext uses "Social Login Key" doctype for OAuth providers
    oidc_config = {
        'enable_oauth': True,
        'oauth_provider': provider,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'scope': scope,
    }

    # Add optional endpoints if provided
    if auth_url:
        oidc_config['authorization_url'] = auth_url
    if token_url:
        oidc_config['token_url'] = token_url
    if userinfo_url:
        oidc_config['userinfo_url'] = userinfo_url
    if jwks_url:
        oidc_config['jwks_url'] = jwks_url
    if issuer:
        oidc_config['issuer'] = issuer

    # Merge OIDC config into site config
    config.setdefault('oidc', {}).update(oidc_config)

    # Also add to common_site_config for ERPNext social login compatibility
    # This follows ERPNext's convention for OAuth providers
    config['social_login_key'] = provider
    config[f'{provider}_client_id'] = client_id
    config[f'{provider}_redirect_uri'] = redirect_uri

    # Write updated config
    config_path.write_text(json.dumps(config, indent=2) + '\n')

    print(f"[configure-oidc] OIDC configuration applied for provider: {provider}")
    print(f"[configure-oidc] Client ID: {client_id[:8]}...")
    print(f"[configure-oidc] Redirect URI: {redirect_uri}")
    if auth_url:
        print(f"[configure-oidc] Authorization URL: {auth_url}")
    if token_url:
        print(f"[configure-oidc] Token URL: {token_url}")

    return True


def main():
    """Main entry point."""
    # Default path to site_config.json
    site_name = get_env_str('SITE_NAME', 'site1.local')
    site_config_path = get_env_str(
        'SITE_CONFIG_PATH',
        f'/home/frappe/frappe-bench/sites/{site_name}/site_config.json'
    )

    # Allow override via command line argument
    if len(sys.argv) > 1:
        site_config_path = sys.argv[1]

    print("[configure-oidc] Starting OIDC configuration...")

    try:
        success = configure_oidc(site_config_path)
        if success:
            print("[configure-oidc] ✓ OIDC configuration completed successfully")
            return 0
        else:
            print("[configure-oidc] ℹ OIDC configuration skipped or not enabled")
            return 0
    except Exception as e:
        print(f"[configure-oidc] ✗ Error configuring OIDC: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())

"""
Unit tests for SecretManager
"""

import pytest
import json
import os
from pathlib import Path
import tempfile
import shutil
from datetime import datetime, timedelta
from workflows.mvp_incremental.secret_manager import SecretManager, Secret, SecretValidationResult


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def secret_manager(temp_project_dir):
    """Create a SecretManager instance"""
    return SecretManager(temp_project_dir)


class TestSecret:
    
    def test_secret_initialization(self):
        """Test Secret dataclass initialization"""
        secret = Secret(
            name="API_KEY",
            value="test-value",
            description="Test API key",
            rotation_days=30
        )
        
        assert secret.name == "API_KEY"
        assert secret.value == "test-value"
        assert secret.description == "Test API key"
        assert secret.rotation_days == 30
        assert not secret.is_expired
        assert not secret.needs_rotation
    
    def test_secret_expiration(self):
        """Test secret expiration check"""
        expired_secret = Secret(
            name="API_KEY",
            expires_at=datetime.now() - timedelta(days=1)
        )
        assert expired_secret.is_expired
        
        valid_secret = Secret(
            name="API_KEY",
            expires_at=datetime.now() + timedelta(days=1)
        )
        assert not valid_secret.is_expired
    
    def test_secret_rotation_needed(self):
        """Test secret rotation check"""
        secret = Secret(
            name="API_KEY",
            rotation_days=30,
            last_rotated=datetime.now() - timedelta(days=31)
        )
        assert secret.needs_rotation
        
        recent_secret = Secret(
            name="API_KEY",
            rotation_days=30,
            last_rotated=datetime.now() - timedelta(days=10)
        )
        assert not recent_secret.needs_rotation


class TestSecretManager:
    
    def test_initialization(self, secret_manager, temp_project_dir):
        """Test SecretManager initialization"""
        assert secret_manager.project_path == temp_project_dir
        assert (temp_project_dir / '.secrets').exists()
        assert secret_manager.master_key is not None
        assert secret_manager.cipher_suite is not None
    
    def test_add_secret(self, secret_manager):
        """Test adding a secret"""
        secret = secret_manager.add_secret(
            "API_KEY",
            value="test-api-key-123",
            description="Test API key",
            rotation_days=90,
            tags={"test", "api"}
        )
        
        assert secret.name == "API_KEY"
        assert secret.encrypted_value == "encrypted"
        assert secret.value is None  # Should not store plaintext
        assert secret.description == "Test API key"
        assert secret.rotation_days == 90
        assert secret.tags == {"test", "api"}
        
        # Check metadata is saved
        metadata_file = secret_manager.secrets_dir / 'metadata.json'
        assert metadata_file.exists()
    
    def test_get_secret(self, secret_manager):
        """Test retrieving a secret"""
        # Add a secret
        secret_manager.add_secret("API_KEY", value="test-value-123")
        
        # Retrieve it
        value = secret_manager.get_secret("API_KEY")
        assert value == "test-value-123"
        
        # Try non-existent secret
        assert secret_manager.get_secret("NON_EXISTENT") is None
    
    def test_auto_generate_secret(self, secret_manager):
        """Test auto-generation of secrets"""
        # JWT secret
        jwt_secret = secret_manager.add_secret("JWT_SECRET")
        jwt_value = secret_manager.get_secret("JWT_SECRET")
        assert jwt_value is not None
        assert len(jwt_value) >= 43  # Base64 encoded 256-bit
        
        # API key
        api_secret = secret_manager.add_secret("API_KEY")
        api_value = secret_manager.get_secret("API_KEY")
        assert api_value is not None
        assert api_value.startswith("sk_")
        
        # Session secret
        session_secret = secret_manager.add_secret("SESSION_SECRET")
        session_value = secret_manager.get_secret("SESSION_SECRET")
        assert session_value is not None
        assert len(session_value) >= 32
    
    def test_generate_secret_value(self, secret_manager):
        """Test secret value generation for different types"""
        # JWT/Token type
        jwt_value = secret_manager.generate_secret_value("JWT_SECRET")
        assert len(jwt_value) >= 43
        
        # API key type
        api_value = secret_manager.generate_secret_value("API_KEY")
        assert api_value.startswith("sk_")
        
        # Password type
        password_value = secret_manager.generate_secret_value("DB_PASSWORD")
        assert len(password_value) >= 16
        # Check password complexity
        assert any(c.isupper() for c in password_value)
        assert any(c.islower() for c in password_value)
        assert any(c.isdigit() for c in password_value)
        assert any(c in "!@#$%^&*" for c in password_value)
        
        # Default type
        default_value = secret_manager.generate_secret_value("RANDOM_SECRET")
        assert len(default_value) >= 32
    
    def test_rotate_secret(self, secret_manager):
        """Test secret rotation"""
        # Add a secret
        secret_manager.add_secret("API_KEY", value="old-value")
        old_value = secret_manager.get_secret("API_KEY")
        
        # Rotate it
        success = secret_manager.rotate_secret("API_KEY")
        assert success
        
        # Check new value is different
        new_value = secret_manager.get_secret("API_KEY")
        assert new_value != old_value
        
        # Check metadata is updated
        secret = secret_manager.secrets["API_KEY"]
        assert secret.last_rotated is not None
    
    def test_validate_secrets(self, secret_manager):
        """Test secret validation"""
        # Add some secrets
        secret_manager.add_secret("API_KEY", value="test-key")
        secret_manager.add_secret("JWT_SECRET", value="weak")
        
        # Create an expired secret
        expired_secret = Secret(
            name="EXPIRED_KEY",
            expires_at=datetime.now() - timedelta(days=1)
        )
        secret_manager.secrets["EXPIRED_KEY"] = expired_secret
        
        # Validate
        result = secret_manager.validate_secrets(["API_KEY", "JWT_SECRET", "EXPIRED_KEY", "MISSING_KEY"])
        
        assert not result.is_valid
        assert any("Missing required secret: MISSING_KEY" in error for error in result.errors)
        assert any("EXPIRED_KEY is expired" in error for error in result.errors)
        assert any("JWT_SECRET is weak" in warning for warning in result.warnings)
    
    def test_check_secret_strength(self, secret_manager):
        """Test secret strength checking"""
        # Weak secret - common value takes precedence
        weak_result = secret_manager._check_secret_strength("API_KEY", "12345")
        assert weak_result['is_weak']
        assert 'Common value' in weak_result['reason']
        
        # Short but not common
        short_result = secret_manager._check_secret_strength("API_KEY", "abc123xyz789")
        assert short_result['is_weak']
        assert 'Too short' in short_result['reason']
        
        # Common value
        common_result = secret_manager._check_secret_strength("API_KEY", "password")
        assert common_result['is_weak']
        assert 'Common value' in common_result['reason']
        
        # Strong secret
        strong_secret = secret_manager.generate_secret_value("API_KEY")
        strong_result = secret_manager._check_secret_strength("API_KEY", strong_secret)
        assert not strong_result['is_weak']
    
    def test_calculate_entropy(self, secret_manager):
        """Test entropy calculation"""
        # Low entropy
        low_entropy = secret_manager._calculate_entropy("aaaaaaa")
        assert low_entropy < 1.0
        
        # High entropy
        high_entropy = secret_manager._calculate_entropy("aB3$xY9!mP2@qR5")
        assert high_entropy > 3.0
        
        # Empty string
        assert secret_manager._calculate_entropy("") == 0.0
    
    def test_export_secrets_template(self, secret_manager, temp_project_dir):
        """Test exporting secrets template"""
        # Add some secrets
        secret_manager.add_secret("API_KEY", description="Main API key", rotation_days=90)
        secret_manager.add_secret("JWT_SECRET", description="JWT signing secret")
        
        # Export template
        template_path = temp_project_dir / "secrets-template.json"
        secret_manager.export_secrets_template(template_path)
        
        assert template_path.exists()
        
        # Check template content
        with open(template_path) as f:
            template = json.load(f)
        
        assert "secrets" in template
        assert "API_KEY" in template["secrets"]
        assert template["secrets"]["API_KEY"]["description"] == "Main API key"
        assert template["secrets"]["API_KEY"]["rotation_days"] == 90
        assert template["secrets"]["API_KEY"]["example"] == "<api-key>"
        
        assert "JWT_SECRET" in template["secrets"]
        assert template["secrets"]["JWT_SECRET"]["pattern"] == r'^[A-Za-z0-9_\-]{64,}$'
    
    def test_generate_kubernetes_secrets(self, secret_manager):
        """Test Kubernetes secrets generation"""
        # Add secrets
        secret_manager.add_secret("API_KEY", value="test-api-key")
        secret_manager.add_secret("DB_PASSWORD", value="test-password")
        
        # Generate K8s manifest
        k8s_secrets = secret_manager.generate_kubernetes_secrets()
        
        assert k8s_secrets["apiVersion"] == "v1"
        assert k8s_secrets["kind"] == "Secret"
        assert k8s_secrets["type"] == "Opaque"
        
        # Check secrets are base64 encoded
        import base64
        api_key_b64 = k8s_secrets["data"]["api-key"]
        decoded_api_key = base64.b64decode(api_key_b64).decode()
        assert decoded_api_key == "test-api-key"
    
    def test_cleanup_expired_secrets(self, secret_manager):
        """Test cleanup of expired secrets"""
        # Add normal secret
        secret_manager.add_secret("VALID_KEY", value="valid")
        
        # Add expired secret
        expired_secret = Secret(
            name="EXPIRED_KEY",
            expires_at=datetime.now() - timedelta(days=1)
        )
        secret_manager.secrets["EXPIRED_KEY"] = expired_secret
        
        # Create fake encrypted file
        expired_file = secret_manager.secrets_dir / "EXPIRED_KEY.enc"
        expired_file.write_text("encrypted-data")
        
        # Run cleanup
        secret_manager.cleanup_expired_secrets()
        
        # Check expired secret is removed
        assert "EXPIRED_KEY" not in secret_manager.secrets
        assert not expired_file.exists()
        
        # Check valid secret remains
        assert "VALID_KEY" in secret_manager.secrets
    
    def test_metadata_persistence(self, secret_manager):
        """Test saving and loading metadata"""
        # Add secrets
        secret_manager.add_secret(
            "API_KEY",
            description="Test key",
            rotation_days=30,
            tags={"test", "api"}
        )
        
        # Create new manager instance (should load metadata)
        new_manager = SecretManager(secret_manager.project_path, secret_manager.master_key)
        
        # Check secret metadata is loaded
        assert "API_KEY" in new_manager.secrets
        loaded_secret = new_manager.secrets["API_KEY"]
        assert loaded_secret.description == "Test key"
        assert loaded_secret.rotation_days == 30
        assert loaded_secret.tags == {"test", "api"}
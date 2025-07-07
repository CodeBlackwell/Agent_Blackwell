"""
Secret Manager for MVP Incremental Workflow

Handles secure management of sensitive configuration values.
"""

import os
import json
import base64
import secrets
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from workflows.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class Secret:
    """Represents a secret value"""
    name: str
    value: Optional[str] = None
    encrypted_value: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    rotation_days: Optional[int] = None
    last_rotated: Optional[datetime] = None
    tags: Set[str] = field(default_factory=set)
    
    @property
    def is_expired(self) -> bool:
        """Check if secret is expired"""
        if self.expires_at:
            return datetime.now() > self.expires_at
        return False
    
    @property
    def needs_rotation(self) -> bool:
        """Check if secret needs rotation"""
        if self.rotation_days and self.last_rotated:
            return datetime.now() > self.last_rotated + timedelta(days=self.rotation_days)
        return False


@dataclass
class SecretValidationResult:
    """Result of secret validation"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class SecretManager:
    """Manages secrets for generated applications"""
    
    # Common secret patterns
    SECRET_PATTERNS = {
        'api_key': r'^[A-Za-z0-9_\-]{32,}$',
        'jwt_secret': r'^[A-Za-z0-9_\-]{64,}$',
        'database_password': r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{12,}$',
        'oauth_secret': r'^[A-Za-z0-9_\-]{32,}$',
        'encryption_key': r'^[A-Za-z0-9+/]{43}=$',  # Base64 256-bit key
    }
    
    # Secret types that should be auto-generated
    AUTO_GENERATE_TYPES = {
        'JWT_SECRET', 'SESSION_SECRET', 'ENCRYPTION_KEY', 
        'API_KEY', 'REFRESH_TOKEN_SECRET', 'CSRF_SECRET'
    }
    
    def __init__(self, project_path: Path, master_key: Optional[str] = None):
        self.project_path = project_path
        self.secrets_dir = project_path / '.secrets'
        self.secrets_dir.mkdir(exist_ok=True)
        
        # Initialize encryption
        self.master_key = master_key or self._get_or_create_master_key()
        self.cipher_suite = self._create_cipher_suite()
        
        # Track secrets
        self.secrets: Dict[str, Secret] = {}
        self._load_secrets_metadata()
    
    def _get_or_create_master_key(self) -> str:
        """Get or create master encryption key"""
        key_file = self.secrets_dir / '.key'
        
        if key_file.exists():
            return key_file.read_text().strip()
        
        # Generate new key
        key = Fernet.generate_key().decode()
        key_file.write_text(key)
        
        # Secure the file
        os.chmod(key_file, 0o600)
        
        logger.info("Created new master encryption key")
        return key
    
    def _create_cipher_suite(self) -> Fernet:
        """Create cipher suite for encryption"""
        return Fernet(self.master_key.encode())
    
    def _load_secrets_metadata(self):
        """Load secrets metadata"""
        metadata_file = self.secrets_dir / 'metadata.json'
        
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    data = json.load(f)
                    for name, secret_data in data.items():
                        self.secrets[name] = Secret(
                            name=name,
                            description=secret_data.get('description'),
                            created_at=datetime.fromisoformat(secret_data['created_at']),
                            expires_at=datetime.fromisoformat(secret_data['expires_at']) if secret_data.get('expires_at') else None,
                            rotation_days=secret_data.get('rotation_days'),
                            last_rotated=datetime.fromisoformat(secret_data['last_rotated']) if secret_data.get('last_rotated') else None,
                            tags=set(secret_data.get('tags', []))
                        )
            except Exception as e:
                logger.warning(f"Failed to load secrets metadata: {e}")
    
    def _save_secrets_metadata(self):
        """Save secrets metadata"""
        metadata_file = self.secrets_dir / 'metadata.json'
        
        data = {}
        for name, secret in self.secrets.items():
            data[name] = {
                'description': secret.description,
                'created_at': secret.created_at.isoformat(),
                'expires_at': secret.expires_at.isoformat() if secret.expires_at else None,
                'rotation_days': secret.rotation_days,
                'last_rotated': secret.last_rotated.isoformat() if secret.last_rotated else None,
                'tags': list(secret.tags)
            }
        
        with open(metadata_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Secure the file
        os.chmod(metadata_file, 0o600)
    
    def add_secret(self, name: str, value: Optional[str] = None, 
                   description: Optional[str] = None,
                   rotation_days: Optional[int] = None,
                   tags: Optional[Set[str]] = None) -> Secret:
        """Add a new secret"""
        logger.info(f"Adding secret: {name}")
        
        # Auto-generate value if needed
        if value is None and name in self.AUTO_GENERATE_TYPES:
            value = self.generate_secret_value(name)
        
        # Create secret object
        secret = Secret(
            name=name,
            value=value,
            description=description,
            rotation_days=rotation_days,
            tags=tags or set()
        )
        
        # Encrypt and store
        if value:
            self._store_secret_value(name, value)
            secret.encrypted_value = "encrypted"
            secret.value = None  # Don't keep plaintext in memory
        
        # Save metadata
        self.secrets[name] = secret
        self._save_secrets_metadata()
        
        return secret
    
    def get_secret(self, name: str) -> Optional[str]:
        """Get decrypted secret value"""
        if name not in self.secrets:
            return None
        
        secret_file = self.secrets_dir / f"{name}.enc"
        if not secret_file.exists():
            return None
        
        try:
            encrypted_data = secret_file.read_bytes()
            decrypted_value = self.cipher_suite.decrypt(encrypted_data).decode()
            return decrypted_value
        except Exception as e:
            logger.error(f"Failed to decrypt secret {name}: {e}")
            return None
    
    def _store_secret_value(self, name: str, value: str):
        """Store encrypted secret value"""
        secret_file = self.secrets_dir / f"{name}.enc"
        
        encrypted_data = self.cipher_suite.encrypt(value.encode())
        secret_file.write_bytes(encrypted_data)
        
        # Secure the file
        os.chmod(secret_file, 0o600)
    
    def generate_secret_value(self, name: str) -> str:
        """Generate a secure secret value based on type"""
        name_upper = name.upper()
        
        if 'JWT' in name_upper or 'TOKEN' in name_upper:
            # Generate 256-bit JWT secret
            return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
        elif 'SESSION' in name_upper:
            # Generate session secret
            return secrets.token_urlsafe(32)
        elif 'API_KEY' in name_upper:
            # Generate API key
            return f"sk_{secrets.token_urlsafe(32)}"
        elif 'ENCRYPTION' in name_upper or 'KEY' in name_upper:
            # Generate encryption key
            return Fernet.generate_key().decode()
        elif 'PASSWORD' in name_upper:
            # Generate strong password
            return self._generate_strong_password()
        else:
            # Default to URL-safe token
            return secrets.token_urlsafe(32)
    
    def _generate_strong_password(self, length: int = 16) -> str:
        """Generate a strong password"""
        import string
        
        # Ensure password has at least one of each type
        password = []
        password.append(secrets.choice(string.ascii_lowercase))
        password.append(secrets.choice(string.ascii_uppercase))
        password.append(secrets.choice(string.digits))
        password.append(secrets.choice("!@#$%^&*"))
        
        # Fill the rest randomly
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        for _ in range(length - 4):
            password.append(secrets.choice(alphabet))
        
        # Shuffle to avoid predictable pattern
        secrets.SystemRandom().shuffle(password)
        return ''.join(password)
    
    def rotate_secret(self, name: str) -> bool:
        """Rotate a secret"""
        if name not in self.secrets:
            logger.error(f"Secret {name} not found")
            return False
        
        secret = self.secrets[name]
        
        # Generate new value
        new_value = self.generate_secret_value(name)
        
        # Store new value
        self._store_secret_value(name, new_value)
        
        # Update metadata
        secret.last_rotated = datetime.now()
        self._save_secrets_metadata()
        
        logger.info(f"Rotated secret: {name}")
        return True
    
    def validate_secrets(self, required_secrets: List[str]) -> SecretValidationResult:
        """Validate secrets configuration"""
        result = SecretValidationResult(is_valid=True)
        
        # Check required secrets
        for secret_name in required_secrets:
            if secret_name not in self.secrets:
                result.errors.append(f"Missing required secret: {secret_name}")
                result.is_valid = False
            else:
                secret = self.secrets[secret_name]
                
                # Check expiration
                if secret.is_expired:
                    result.errors.append(f"Secret {secret_name} is expired")
                    result.is_valid = False
                
                # Check rotation
                if secret.needs_rotation:
                    result.warnings.append(f"Secret {secret_name} needs rotation")
        
        # Check for weak secrets
        for name, secret in self.secrets.items():
            value = self.get_secret(name)
            if value:
                strength = self._check_secret_strength(name, value)
                if strength['is_weak']:
                    result.warnings.append(f"Secret {name} is weak: {strength['reason']}")
                    result.recommendations.extend(strength['recommendations'])
        
        return result
    
    def _check_secret_strength(self, name: str, value: str) -> Dict[str, Any]:
        """Check secret strength"""
        result = {
            'is_weak': False,
            'reason': '',
            'recommendations': []
        }
        
        reasons = []
        
        # Check against common patterns first (most critical)
        if value in ['secret', 'password', '12345', 'admin', 'test']:
            result['is_weak'] = True
            reasons.append('Common value')
            result['recommendations'].append(f"Never use common values for {name}")
        
        # Check length
        if len(value) < 32:
            result['is_weak'] = True
            reasons.append('Too short')
            result['recommendations'].append(f"Use at least 32 characters for {name}")
        
        # Check entropy
        entropy = self._calculate_entropy(value)
        if entropy < 4.0:  # Low entropy
            result['is_weak'] = True
            reasons.append('Low entropy')
            result['recommendations'].append(f"Use more random characters for {name}")
        
        # Set the primary reason (first one found)
        if reasons:
            result['reason'] = reasons[0]
        
        return result
    
    def _calculate_entropy(self, value: str) -> float:
        """Calculate Shannon entropy of a string"""
        if not value:
            return 0.0
        
        # Count character frequencies
        freq = {}
        for char in value:
            freq[char] = freq.get(char, 0) + 1
        
        # Calculate entropy
        import math
        entropy = 0.0
        length = len(value)
        for count in freq.values():
            probability = count / length
            if probability > 0:
                entropy -= probability * math.log2(probability)
        
        return entropy
    
    def export_secrets_template(self, output_path: Path):
        """Export secrets template for deployment"""
        template = {
            'secrets': {},
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'version': '1.0'
            }
        }
        
        for name, secret in self.secrets.items():
            template['secrets'][name] = {
                'description': secret.description or f"Secret for {name}",
                'required': True,
                'rotation_days': secret.rotation_days,
                'tags': list(secret.tags),
                'example': f"<{name.lower().replace('_', '-')}>",
                'pattern': self._get_secret_pattern(name)
            }
        
        output_path.write_text(json.dumps(template, indent=2))
        logger.info(f"Exported secrets template to {output_path}")
    
    def _get_secret_pattern(self, name: str) -> Optional[str]:
        """Get validation pattern for secret type"""
        name_lower = name.lower()
        
        for pattern_type, pattern in self.SECRET_PATTERNS.items():
            if pattern_type in name_lower:
                return pattern
        
        return None
    
    def generate_kubernetes_secrets(self) -> Dict[str, Any]:
        """Generate Kubernetes secrets manifest"""
        secrets_data = {}
        
        for name in self.secrets:
            value = self.get_secret(name)
            if value:
                # Base64 encode for Kubernetes
                encoded_value = base64.b64encode(value.encode()).decode()
                # Convert to Kubernetes-friendly name
                k8s_name = name.lower().replace('_', '-')
                secrets_data[k8s_name] = encoded_value
        
        return {
            'apiVersion': 'v1',
            'kind': 'Secret',
            'metadata': {
                'name': 'app-secrets',
                'namespace': 'default'
            },
            'type': 'Opaque',
            'data': secrets_data
        }
    
    def cleanup_expired_secrets(self):
        """Clean up expired secrets"""
        expired = []
        
        for name, secret in self.secrets.items():
            if secret.is_expired:
                expired.append(name)
        
        for name in expired:
            secret_file = self.secrets_dir / f"{name}.enc"
            if secret_file.exists():
                secret_file.unlink()
            del self.secrets[name]
            logger.info(f"Removed expired secret: {name}")
        
        if expired:
            self._save_secrets_metadata()
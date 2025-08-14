# Security Coding Standards

## Overview

This document establishes security coding standards for the Yesman-Claude project to prevent vulnerabilities and ensure
secure development practices. All team members must follow these guidelines to maintain a strong security posture.

## 🎯 Core Security Principles

### 1. Defense in Depth

- Implement multiple security layers
- Never rely on a single security control
- Assume any component can be compromised

### 2. Principle of Least Privilege

- Grant minimum necessary permissions
- Use role-based access control (RBAC)
- Regularly audit permissions

### 3. Input Validation and Sanitization

- Validate all user inputs
- Sanitize data before processing
- Use allowlists over denylists

### 4. Secure by Default

- Default configurations must be secure
- Fail securely when errors occur
- Security features should be enabled by default

## 🔒 Secure Coding Practices

### Input Validation

#### Required Validations

```python
# ✅ GOOD: Proper input validation
import re
from typing import Optional

def validate_session_name(name: str) -> bool:
    """Validate session name against security criteria."""
    # Length check
    if not (1 <= len(name) <= 64):
        return False
    
    # Character allowlist
    if not re.match(r'^[a-zA-Z0-9_-]+$', name):
        return False
    
    # Dangerous pattern check
    dangerous_patterns = [
        r'\.\.',           # Path traversal
        r'[<>"\']',       # XSS characters  
        r'(SELECT|DROP|INSERT|DELETE)\s', # SQL injection
        r'(--|;|\/\*)'    # SQL comments
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, name, re.IGNORECASE):
            return False
    
    return True

# ❌ BAD: No input validation
def unsafe_session_name(name: str):
    return name  # Accepts any input
```

#### File Path Validation

```python
# ✅ GOOD: Secure path handling
import os
from pathlib import Path

def validate_file_path(user_path: str, base_dir: str) -> Optional[Path]:
    """Validate file path to prevent directory traversal."""
    try:
        # Normalize and resolve path
        base = Path(base_dir).resolve()
        target = (base / user_path).resolve()
        
        # Ensure target is within base directory
        target.relative_to(base)
        
        return target
    except (ValueError, OSError):
        return None

# ❌ BAD: Direct path concatenation
def unsafe_path(user_path: str, base_dir: str):
    return f"{base_dir}/{user_path}"  # Vulnerable to traversal
```

### Authentication and Authorization

#### Secure Token Handling

```python
# ✅ GOOD: Secure JWT implementation
from datetime import datetime, timedelta
from jose import JWTError, jwt
import secrets

class SecureTokenManager:
    def __init__(self):
        # Use secure random secret (load from environment)
        self.secret_key = os.environ.get('JWT_SECRET_KEY')
        if not self.secret_key:
            raise ValueError("JWT_SECRET_KEY environment variable required")
        
        self.algorithm = "HS256"
        self.token_expiry = timedelta(hours=1)  # Short expiry
    
    def create_token(self, user_data: dict) -> str:
        """Create secure JWT token."""
        payload = {
            **user_data,
            "exp": datetime.utcnow() + self.token_expiry,
            "iat": datetime.utcnow(),
            "jti": secrets.token_hex(16)  # Unique token ID
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> dict:
        """Verify and decode token."""
        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except JWTError:
            raise ValueError("Invalid token")

# ❌ BAD: Insecure token handling
def bad_token(user_data: dict):
    return f"token_{user_data['username']}"  # Predictable tokens
```

#### Permission Checks

```python
# ✅ GOOD: Proper authorization
from functools import wraps
from fastapi import HTTPException

def require_permission(permission: str):
    """Decorator for permission-based access control."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get('request')
            user = getattr(request.state, 'user', None)
            
            if not user:
                raise HTTPException(401, "Authentication required")
            
            if permission not in user.get('permissions', []):
                raise HTTPException(403, f"Missing permission: {permission}")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Usage
@require_permission('session:create')
async def create_session(request: Request):
    pass

# ❌ BAD: No authorization check
async def unsafe_create_session(request: Request):
    # Direct action without permission check
    pass
```

### SQL Injection Prevention

#### Parameterized Queries

```python
# ✅ GOOD: Parameterized queries
async def get_user_sessions(user_id: int) -> List[dict]:
    """Get user sessions safely."""
    query = """
        SELECT id, name, created_at 
        FROM sessions 
        WHERE user_id = $1 
        ORDER BY created_at DESC
    """
    return await database.fetch_all(query, user_id)

# ✅ GOOD: ORM usage
from sqlalchemy import select
from .models import Session

async def get_user_sessions_orm(user_id: int):
    """Get user sessions using ORM."""
    query = select(Session).where(Session.user_id == user_id)
    return await database.fetch_all(query)

# ❌ BAD: String concatenation
async def unsafe_get_sessions(user_id: str):
    query = f"SELECT * FROM sessions WHERE user_id = {user_id}"
    return await database.fetch_all(query)
```

### Cross-Site Scripting (XSS) Prevention

#### Output Encoding

```python
# ✅ GOOD: Proper output encoding
import html
import bleach

def sanitize_user_content(content: str) -> str:
    """Sanitize user content for safe display."""
    # Remove dangerous HTML tags
    allowed_tags = ['p', 'br', 'strong', 'em']
    cleaned = bleach.clean(content, tags=allowed_tags, strip=True)
    
    # HTML escape remaining content
    return html.escape(cleaned)

# ✅ GOOD: Template auto-escaping (FastAPI/Jinja2)
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")
# Jinja2 auto-escapes by default - do not disable!

# ❌ BAD: Raw user input in templates
def unsafe_template():
    return f"<div>{user_input}</div>"  # XSS vulnerable
```

### Error Handling

#### Secure Error Messages

```python
# ✅ GOOD: Generic error messages
import logging
from fastapi import HTTPException

async def secure_login(username: str, password: str):
    """Secure login with generic error messages."""
    try:
        user = await get_user(username)
        if not user or not verify_password(password, user.password_hash):
            # Generic message - don't reveal if user exists
            raise HTTPException(401, "Invalid credentials")
        
        return create_session(user)
    
    except Exception as e:
        # Log detailed error for debugging
        logging.error(f"Login error for {username}: {e}")
        # Return generic message to user
        raise HTTPException(500, "Authentication service unavailable")

# ❌ BAD: Revealing error messages
async def unsafe_login(username: str, password: str):
    user = await get_user(username)
    if not user:
        raise HTTPException(404, "User not found")  # Reveals user existence
    
    if not verify_password(password, user.password_hash):
        raise HTTPException(401, "Wrong password")  # Confirms user exists
```

### Cryptographic Practices

#### Password Hashing

```python
# ✅ GOOD: Secure password hashing
from passlib.context import CryptContext

# Use strong, slow hashing algorithm
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Adjust based on security requirements
)

def hash_password(password: str) -> str:
    """Hash password securely."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)

# ❌ BAD: Weak or no hashing
import hashlib

def unsafe_hash(password: str):
    return hashlib.md5(password.encode()).hexdigest()  # MD5 is broken
```

#### Data Encryption

```python
# ✅ GOOD: Proper encryption
from cryptography.fernet import Fernet
import os

class DataEncryption:
    def __init__(self):
        # Load key from secure environment variable
        key = os.environ.get('ENCRYPTION_KEY')
        if not key:
            raise ValueError("ENCRYPTION_KEY environment variable required")
        self.cipher = Fernet(key.encode())
    
    def encrypt(self, data: str) -> bytes:
        """Encrypt sensitive data."""
        return self.cipher.encrypt(data.encode())
    
    def decrypt(self, encrypted_data: bytes) -> str:
        """Decrypt sensitive data."""
        return self.cipher.decrypt(encrypted_data).decode()

# ❌ BAD: No encryption for sensitive data
def store_sensitive_data(data: str):
    with open('sensitive.txt', 'w') as f:
        f.write(data)  # Stored in plaintext
```

## 🚨 Common Vulnerabilities and Prevention

### 1. Path Traversal (Directory Traversal)

**Vulnerability Example:**

```python
# ❌ VULNERABLE
@app.get("/files/{filename}")
async def get_file(filename: str):
    file_path = f"/app/uploads/{filename}"
    return FileResponse(file_path)

# Attack: GET /files/../../../etc/passwd
```

**Prevention:**

```python
# ✅ SECURE
@app.get("/files/{filename}")
async def get_file(filename: str):
    # Validate filename
    if not re.match(r'^[a-zA-Z0-9._-]+$', filename):
        raise HTTPException(400, "Invalid filename")
    
    # Use secure path joining
    base_dir = Path("/app/uploads")
    file_path = base_dir / filename
    
    # Ensure file is within allowed directory
    try:
        file_path.resolve().relative_to(base_dir.resolve())
    except ValueError:
        raise HTTPException(403, "Access denied")
    
    if not file_path.exists():
        raise HTTPException(404, "File not found")
    
    return FileResponse(file_path)
```

### 2. Command Injection

**Vulnerability Example:**

```python
# ❌ VULNERABLE
import subprocess

@app.post("/process")
async def process_file(filename: str):
    # Direct command execution with user input
    result = subprocess.run(f"convert {filename} output.pdf", shell=True)
    return {"status": "processed"}

# Attack: filename="test.jpg; rm -rf /"
```

**Prevention:**

```python
# ✅ SECURE
import subprocess
import shlex

@app.post("/process")
async def process_file(filename: str):
    # Validate filename
    if not validate_filename(filename):
        raise HTTPException(400, "Invalid filename")
    
    # Use argument list instead of shell command
    try:
        result = subprocess.run([
            "convert", 
            shlex.quote(filename), 
            "output.pdf"
        ], check=True, timeout=30)
        return {"status": "processed"}
    except subprocess.CalledProcessError:
        raise HTTPException(500, "Processing failed")
```

### 3. Insecure Direct Object Reference (IDOR)

**Vulnerability Example:**

```python
# ❌ VULNERABLE
@app.get("/sessions/{session_id}")
async def get_session(session_id: int):
    session = await database.fetch_one(
        "SELECT * FROM sessions WHERE id = ?", session_id
    )
    return session  # Returns any session regardless of owner
```

**Prevention:**

```python
# ✅ SECURE
@app.get("/sessions/{session_id}")
async def get_session(session_id: int, current_user: User = Depends(get_current_user)):
    session = await database.fetch_one(
        "SELECT * FROM sessions WHERE id = ? AND user_id = ?", 
        session_id, current_user.id
    )
    
    if not session:
        raise HTTPException(404, "Session not found")
    
    return session
```

## 🔧 Security Configuration

### Environment Variables

#### Required Security Variables

```bash
# .env.production
JWT_SECRET_KEY=<strong-random-key-256-bits>
DATABASE_ENCRYPTION_KEY=<fernet-key>
SESSION_SECRET=<session-signing-key>
ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# API Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=10

# Security Headers
SECURITY_HEADERS_ENABLED=true
HSTS_MAX_AGE=31536000
```

#### Secret Management

```python
# ✅ GOOD: Environment-based secrets
import os
from typing import Optional

class SecurityConfig:
    def __init__(self):
        self.jwt_secret = self._get_required_env('JWT_SECRET_KEY')
        self.encryption_key = self._get_required_env('DATABASE_ENCRYPTION_KEY')
        self.allowed_hosts = os.getenv('ALLOWED_HOSTS', '').split(',')
    
    def _get_required_env(self, key: str) -> str:
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable {key} not set")
        return value

# ❌ BAD: Hardcoded secrets
JWT_SECRET = "hardcoded-secret-key"  # Never do this
```

### Security Headers

#### FastAPI Security Headers

```python
# ✅ GOOD: Security middleware
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response

app = FastAPI()
app.add_middleware(SecurityHeadersMiddleware)
```

### CORS Configuration

```python
# ✅ GOOD: Restrictive CORS
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# ❌ BAD: Permissive CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Too permissive
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 📋 Security Code Review Checklist

### Input Validation

- [ ] All user inputs are validated
- [ ] Input length limits are enforced
- [ ] Character allowlists are used where appropriate
- [ ] File upload restrictions are implemented
- [ ] Path traversal protection is in place

### Authentication & Authorization

- [ ] Authentication is required for protected endpoints
- [ ] Authorization checks are performed before actions
- [ ] Tokens have appropriate expiration times
- [ ] Session management is secure
- [ ] Password policies are enforced

### Data Protection

- [ ] Sensitive data is encrypted at rest
- [ ] TLS/SSL is used for data in transit
- [ ] Database credentials are protected
- [ ] API keys are stored securely
- [ ] Logs don't contain sensitive information

### Error Handling

- [ ] Error messages don't reveal sensitive information
- [ ] Stack traces are not exposed to users
- [ ] Proper logging is implemented
- [ ] Graceful degradation is handled
- [ ] Rate limiting is implemented

### Dependencies

- [ ] Third-party libraries are up-to-date
- [ ] Vulnerability scans are performed
- [ ] Dependency sources are trusted
- [ ] License compliance is verified
- [ ] CVE monitoring is in place

## 🛠️ Security Tools Integration

### Static Code Analysis

- **Bandit**: Python security linting (integrated in pre-commit hooks)
- **Semgrep**: Additional security pattern detection
- **Safety**: Python dependency vulnerability checking

### Dynamic Testing

- **OWASP ZAP**: Web application security testing
- **Postman/Newman**: API security testing
- **Custom security test suite**: Project-specific tests

### Dependency Monitoring

- **GitHub Dependabot**: Automated dependency updates
- **Snyk**: Continuous vulnerability monitoring
- **pip-audit**: Python package vulnerability scanning

## 📚 Additional Resources

### Security Standards

- [OWASP Top 10](https://owasp.org/Top10/)
- [OWASP Web Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [CWE - Common Weakness Enumeration](https://cwe.mitre.org/)

### Python Security

- [Python Security Best Practices](https://python.org/dev/security/)
- [Bandit Security Linter](https://bandit.readthedocs.io/)
- [Python Cryptographic Authority](https://cryptography.io/)

### FastAPI Security

- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [FastAPI OAuth2](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)

## 🚨 Incident Response

### Security Incident Escalation

1. **Immediate Response** (0-15 minutes)

   - Contain the threat
   - Document initial findings
   - Notify security team lead

1. **Assessment** (15-60 minutes)

   - Determine scope and impact
   - Identify affected systems
   - Begin forensic collection

1. **Communication** (1-4 hours)

   - Notify stakeholders
   - Prepare public communications if needed
   - Contact law enforcement if required

### Post-Incident Review

- Root cause analysis
- Security control improvements
- Process refinements
- Team training updates

______________________________________________________________________

**Last Updated**: 2025-01-11\
**Version**: 1.0\
**Review Schedule**: Quarterly\
**Next Review**: 2025-04-11

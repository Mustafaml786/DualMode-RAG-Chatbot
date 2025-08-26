import bcrypt
import uuid

# Helper functions for password hashing and verification
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# Helper for session token generation
def generate_session_token() -> str:
    return str(uuid.uuid4())
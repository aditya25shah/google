integrations_db = {}

# Encryption utilities
def encrypt_token(token: str) -> str:
    """Encrypt API token for secure storage"""
    return cipher_suite.encrypt(token.encode()).decode()

def decrypt_token(encrypted_token: str) -> str:
    """Decrypt API token for use"""
    return cipher_suite.decrypt(encrypted_token.encode()).decode()


async def get_decrypted_integration(integration_id: str, user_email: str) -> Optional[Dict[str, Any]]:
    """Get integration with decrypted token"""
    integration = integrations_db.get(integration_id)
    if not integration or integration["user_email"] != user_email:
        return None
    integration_copy = integration.copy()
    integration_copy["api_token"] = decrypt_token(integration["encrypted_token"])
    return integration_copy
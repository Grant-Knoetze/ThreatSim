from aiohttp import web
from aiohttp.web import middleware
from app.api.v2.errors import ForbiddenError

@middleware
async def tenant_auth_middleware(request, handler):
    """Middleware to validate tenant headers on every request"""
    
    # Skip auth for certain paths
    if request.path in ['/login', '/health']:
        return await handler(request)
    
    # Get tenant headers
    tenant_id = request.headers.get('X-Tenant-ID')
    api_key = request.headers.get('X-API-Key')
    
    # Validate
    if not _validate_tenant(tenant_id, api_key):
        raise ForbiddenError("Invalid tenant credentials")
    
    # Store tenant in request
    request['tenant'] = tenant_id
    return await handler(request)

def _validate_tenant(tenant_id, api_key):
    """Replace with your actual validation logic"""
    valid_tenants = {
        "client_A": "client_a_secret_key",
        "client_B": "client_b_secret_key"
    }
    return (
        tenant_id in valid_tenants and 
        api_key == valid_tenants[tenant_id]  # In prod, use secrets.compare_digest()
    )
"""Key Changes Made:
Added Tenant Context

self.current_tenant stores the validated tenant

Available to all API handlers inheriting from BaseApi

Modified Permission Flow

Tenant validation happens first in get_request_permissions

Original permission checks still run afterward

Error Handling

Uses Caldera's existing ForbiddenError

Maintains consistent error format

Validation Method

Added _validate_tenant placeholder

Replace with your actual tenant validation logic

How This Works:
For Every API Request:

Checks for X-Tenant-ID and X-API-Key headers

Validates against your tenant database/config

Rejects with 403 if invalid"""

import abc
import json
import logging
from aiohttp import web
import marshmallow as ma

from app.api.v2.errors import (
    RequestUnparsableJsonError,
    RequestValidationError,
    ForbiddenError
)

DEFAULT_LOGGER_NAME = 'rest_api'


class BaseApi(abc.ABC):
    def __init__(self, auth_svc, logger=None):
        self._auth_svc = auth_svc
        self._log = logger or self._create_default_logger()
        self.current_tenant = None  # Add tenant context storage/Stores the validated tenant.

    @property
    def log(self):
        return self._log

    @abc.abstractmethod
    def add_routes(self, app: web.Application):
        raise NotImplementedError

    # MODIFIED: Add tenant authentication to permission check
    async def get_request_permissions(self, request: web.Request):
        # First validate tenant
        tenant = request.headers.get('X-Tenant-ID')
        api_key = request.headers.get('X-API-Key')
        
        if not self._validate_tenant(tenant, api_key):
            raise ForbiddenError("Invalid tenant credentials")
            
        self.current_tenant = tenant  # Store for subsequent use
        
        # Then check normal permissions
        return dict(
            access=tuple(await self._auth_svc.get_permissions(request)),
            tenant=tenant
        )

    # NEW: Add tenant validation method
    def _validate_tenant(self, tenant_id, api_key):
        """Example implementation - replace with your actual validation"""
        valid_tenants = {
            "client_A": "client_a_secret_key",
            "client_B": "client_b_secret_key"
        }
        return (
            tenant_id in valid_tenants and 
            api_key == valid_tenants[tenant_id]  # In prod, use constant-time comparison
        )

    @staticmethod
    async def parse_json_body(request: web.Request, schema: ma.Schema):
        try:
            parsed = schema.load(await request.json())
        except (TypeError, json.JSONDecodeError):
            raise RequestUnparsableJsonError
        except ma.ValidationError as ex:
            raise RequestValidationError(
                message='Request contains schema-invalid json',
                errors=ex.normalized_messages()
            )
        return parsed

    @staticmethod
    def _create_default_logger():
        return logging.getLogger(DEFAULT_LOGGER_NAME)

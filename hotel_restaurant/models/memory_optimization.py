# Copyright (C) 2024-TODAY Memory Optimization Fix
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models
import logging

_logger = logging.getLogger(__name__)


class HotelMenucardMemoryOptimization(models.Model):
    """Memory optimization patches for hotel.menucard model"""
    _inherit = "hotel.menucard"

    @api.model
    def search(self, domain, offset=0, limit=None, order=None):
        """Override search to add default limits and prevent memory overflow"""
        # Add default limit if none specified to prevent loading too many records
        if limit is None:
            limit = 200  # Reasonable default for menucard items
        elif limit > 1000:
            limit = 1000  # Cap the maximum limit
            _logger.warning("Large limit requested for hotel.menucard search, capped at 1000")
        
        return super().search(domain, offset, limit, order)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        """Override read_group to add limits"""
        if limit is None:
            limit = 100  # Default limit for group operations
        elif limit > 500:
            limit = 500
            _logger.warning("Large limit requested for hotel.menucard read_group, capped at 500")
        
        return super().read_group(domain, fields, groupby, offset, limit, orderby, lazy)


class HotelMenucardTypeMemoryOptimization(models.Model):
    """Memory optimization patches for hotel.menucard.type model"""
    _inherit = "hotel.menucard.type"

    @api.model
    def search(self, domain, offset=0, limit=None, order=None):
        """Override search to add default limits"""
        if limit is None:
            limit = 100  # Categories should be limited
        elif limit > 200:
            limit = 200
            _logger.warning("Large limit requested for hotel.menucard.type search, capped at 200")
        
        return super().search(domain, offset, limit, order)


class BaseModelMemoryOptimization(models.AbstractModel):
    """Global memory optimization for large dataset operations"""
    _name = "base.model.memory.optimization"
    _description = "Memory optimization for large datasets"

    @api.model
    def _apply_memory_limits(self, limit):
        """Apply reasonable memory limits based on model type"""
        if limit is None:
            return 200  # Default safe limit
        elif limit > 1000:
            return 1000  # Maximum safe limit
        return limit
# Emergency patch for hotel.menucard web_search_read issue
# Copyright (C) 2024-TODAY Emergency Fix
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models
import logging

_logger = logging.getLogger(__name__)


class HotelMenucardEmergencyPatch(models.Model):
    """Emergency patch to fix web_search_read specification parameter issue"""
    _inherit = "hotel.menucard"

    @api.model
    def web_search_read(self, domain=None, specification=None, offset=0, limit=None, order=None, **kwargs):
        """
        Emergency override to handle the 'specification' parameter correctly.
        This fixes the TypeError: got an unexpected keyword argument 'specification'
        """
        try:
            # Handle the specification parameter that was added in newer Odoo versions
            if specification is not None:
                # For newer Odoo versions that support specification
                return super().web_search_read(
                    domain=domain, 
                    specification=specification, 
                    offset=offset, 
                    limit=limit or 200,  # Add reasonable limit
                    order=order, 
                    **kwargs
                )
            else:
                # Fallback for older versions or when specification is None
                # Convert to fields if we have specification data
                fields = kwargs.get('fields', None)
                return super().web_search_read(
                    domain=domain, 
                    fields=fields, 
                    offset=offset, 
                    limit=limit or 200,  # Add reasonable limit
                    order=order
                )
        except TypeError as e:
            if 'specification' in str(e):
                # If we still get the specification error, use the old method signature
                _logger.warning("Falling back to legacy web_search_read method")
                fields = kwargs.get('fields', None)
                return super(models.Model, self).web_search_read(
                    domain=domain, 
                    fields=fields, 
                    offset=offset, 
                    limit=limit or 200,
                    order=order
                )
            else:
                raise
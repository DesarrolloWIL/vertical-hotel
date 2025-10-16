# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.osv import expression


class HotelMenucardType(models.Model):
    _name = "hotel.menucard.type"  # need to recheck for v15
    _description = "Food Item Type"
    _order = "name, id"
    _rec_names_search = ["name"]

    name = fields.Char(required=True)
    child_ids = fields.One2many("hotel.menucard.type", "menu_id", "Child Categories")
    menu_id = fields.Many2one("hotel.menucard.type", "Food Item Type")

    def _compute_display_name(self):
        def get_names(cat, visited=None):
            """Return the list [cat.name, cat.menu_id.name, ...]
            with protection against circular references"""
            if visited is None:
                visited = set()
            
            # Prevent infinite loops with circular references
            if cat.id in visited:
                return []
            
            visited.add(cat.id)
            res = []
            depth = 0
            max_depth = 5  # Limit depth to prevent memory issues
            
            while cat and depth < max_depth:
                if cat.name:
                    res.append(cat.name)
                cat = cat.menu_id
                depth += 1
            return res

        for cat in self:
            try:
                names = get_names(cat)
                cat.display_name = " / ".join(reversed(names)) or cat.name or ""
            except Exception:
                # Fallback in case of any error
                cat.display_name = cat.name or ""

    @api.model
    def _name_search(self, name, domain=None, operator="ilike", limit=None, order=None):
        """Simplified name search to avoid recursion issues"""
        if not domain:
            domain = []
        
        # Simple search without complex recursion
        if name:
            # Split category names but limit depth for safety
            category_names = name.split(" / ")
            if len(category_names) > 1:
                # Only handle simple parent/child relationship
                child_name = category_names[-1]
                search_domain = [("name", operator, child_name)]
                
                # Look for parent if exists
                if len(category_names) == 2:
                    parent_name = category_names[0]
                    parent_categories = self.search([("name", operator, parent_name)], limit=10)
                    if parent_categories:
                        search_domain = expression.AND([
                            [("menu_id", "in", parent_categories.ids)],
                            search_domain
                        ])
            else:
                search_domain = [("name", operator, name)]
        else:
            search_domain = []
        
        final_domain = expression.AND([search_domain, domain])
        # Add reasonable limit to prevent memory issues
        if limit is None:
            limit = 100
        return self._search(final_domain, limit=limit, order=order)


class HotelMenucard(models.Model):
    _name = "hotel.menucard"
    _description = "Hotel Menucard"
    # Add ordering to improve performance
    _order = "name, id"

    product_id = fields.Many2one(
        "product.product",
        "Hotel Menucard",
        required=True,
        delegate=True,
        ondelete="cascade",
        index=True,
    )
    menu_card_categ_id = fields.Many2one("hotel.menucard.type", "Food Item Category", index=True)
    product_manager_id = fields.Many2one("res.users", "Product Manager")

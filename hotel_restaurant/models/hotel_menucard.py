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
        if not domain:
            domain = []
        
        # Limit recursion depth to prevent infinite loops and memory issues
        max_depth = 5
        if not hasattr(self, '_search_depth'):
            self._search_depth = 0
        
        if self._search_depth >= max_depth:
            # Fallback to simple search if recursion is too deep
            return super()._name_search(name, domain, operator, limit, order)
        
        if name:
            # Be sure name_search is symmetric to name_get
            category_names = name.split(" / ")
            if len(category_names) > max_depth:
                # Limit the number of category levels to prevent memory issues
                category_names = category_names[:max_depth]
            
            parents = list(category_names)
            child = parents.pop()
            search_domain = [("name", operator, child)]
            
            if parents and len(parents) <= 3:  # Limit parent search depth
                try:
                    self._search_depth += 1
                    names_ids = self.name_search(
                        " / ".join(parents),
                        domain=[],  # Use empty domain to avoid duplication
                        operator=operator,
                        limit=limit,
                    )
                    category_ids = [name_id[0] for name_id in names_ids]
                    
                    if category_ids:
                        if operator in expression.NEGATIVE_TERM_OPERATORS:
                            search_domain = expression.AND([
                                [("menu_id", "not in", category_ids)], 
                                search_domain
                            ])
                        else:
                            search_domain = expression.AND([
                                [("menu_id", "in", category_ids)], 
                                search_domain
                            ])
                finally:
                    self._search_depth -= 1
            
            final_domain = expression.AND([search_domain, domain])
            categories = self._search(final_domain, limit=limit, order=order)
        else:
            search_domain = [("name", operator, name)] if name else []
            final_domain = expression.AND([search_domain, domain])
            categories = self._search(final_domain, limit=limit, order=order)

        return categories


class HotelMenucard(models.Model):
    _name = "hotel.menucard"
    _description = "Hotel Menucard"
    # Add ordering and limits to prevent memory issues
    _order = "name, id"
    _rec_names_search = ["name", "code"]

    product_id = fields.Many2one(
        "product.product",
        "Hotel Menucard",
        required=True,
        delegate=True,
        ondelete="cascade",
        index=True,
    )
    menu_card_categ_id = fields.Many2one("hotel.menucard.type", "Food Item Category")
    product_manager_id = fields.Many2one("res.users", "Product Manager")

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, access_rights_uid=None):
        # Add default limit to prevent memory issues on large datasets
        if limit is None:
            limit = 1000  # Default limit for web_search_read operations
        return super()._search(domain, offset, limit, order, access_rights_uid)

    @api.model  
    def web_search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        # Override web_search_read to add safety limits
        if limit is None or limit > 500:
            limit = 500  # Prevent loading too many records at once
        return super().web_search_read(domain, fields, offset, limit, order)

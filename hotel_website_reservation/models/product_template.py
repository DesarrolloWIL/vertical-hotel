# Copyright (C) 2024 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_hotel_room = fields.Boolean(
        string="Is Hotel Room",
        default=False,
        help="Check if this product represents a hotel room"
    )
    hotel_room_id = fields.Many2one(
        'hotel.room',
        string="Hotel Room",
        help="Related hotel room for this product"
    )

    def _get_hotel_room_combination_info(self, combination=False, product_id=False, 
                                       add_qty=1, pricelist=False, **kwargs):
        """Get combination info for hotel room products"""
        combination_info = super()._get_combination_info(
            combination=combination, product_id=product_id, 
            add_qty=add_qty, pricelist=pricelist, **kwargs
        )
        
        if self.is_hotel_room and self.hotel_room_id:
            room = self.hotel_room_id
            combination_info.update({
                'hotel_room_data': {
                    'room_id': room.id,
                    'room_name': room.name,
                    'capacity': room.capacity,
                    'amenities': [amenity.name for amenity in room.amenity_ids],
                    'min_stay': room.min_stay_nights,
                    'max_stay': room.max_stay_nights,
                    'advance_percentage': room.booking_advance_percentage,
                }
            })
        
        return combination_info


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _is_available_for_booking(self, checkin_date, checkout_date):
        """Check if this room product is available for booking"""
        if self.product_tmpl_id.is_hotel_room and self.product_tmpl_id.hotel_room_id:
            room = self.product_tmpl_id.hotel_room_id
            return room._check_availability(checkin_date)
        return True
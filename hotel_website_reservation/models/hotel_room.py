# Copyright (C) 2024 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HotelRoom(models.Model):
    _inherit = "hotel.room"

    # Website fields
    website_published = fields.Boolean(
        string="Published on Website",
        default=False,
        help="Make this room type available for online booking"
    )
    website_description = fields.Html(
        string="Website Description",
        help="Description to display on the website"
    )
    website_image_ids = fields.One2many(
        'hotel.room.image',
        'room_id',
        string="Website Images"
    )
    website_amenity_ids = fields.Many2many(
        'hotel.room.amenities',
        string="Website Amenities",
        help="Amenities to highlight on the website"
    )
    website_price = fields.Float(
        string="Website Display Price",
        compute="_compute_website_price",
        help="Price to display on website (base price + taxes)"
    )
    booking_advance_percentage = fields.Float(
        string="Advance Payment %",
        default=50.0,
        help="Percentage of total amount required as advance payment"
    )
    min_stay_nights = fields.Integer(
        string="Minimum Stay (nights)",
        default=1,
        help="Minimum number of nights for booking"
    )
    max_stay_nights = fields.Integer(
        string="Maximum Stay (nights)",
        default=30,
        help="Maximum number of nights for booking"
    )

    @api.depends('list_price', 'room_type_id.categ_id.property_account_income_categ_id')
    def _compute_website_price(self):
        """Compute the price to display on website including taxes"""
        for room in self:
            price = room.list_price
            # Add tax calculation here if needed
            room.website_price = price

    def get_availability_calendar(self, start_date, end_date):
        """Get availability calendar for the room"""
        availability = {}
        current_date = start_date
        while current_date <= end_date:
            # Check if room is available on this date
            is_available = self._check_availability(current_date)
            availability[current_date.strftime('%Y-%m-%d')] = {
                'available': is_available,
                'price': self.website_price
            }
            current_date += fields.Date.to_date('2024-01-02') - fields.Date.to_date('2024-01-01')
        return availability

    def _check_availability(self, date):
        """Check if room is available on specific date"""
        reservations = self.env['hotel.reservation'].search([
            ('room_id', '=', self.id),
            ('checkin_date', '<=', date),
            ('checkout_date', '>', date),
            ('state', 'in', ['draft', 'confirm'])
        ])
        return len(reservations) == 0


class HotelRoomImage(models.Model):
    _name = 'hotel.room.image'
    _description = 'Hotel Room Images for Website'
    _order = 'sequence, id'

    name = fields.Char(string="Image Name", required=True)
    sequence = fields.Integer(string="Sequence", default=10)
    room_id = fields.Many2one('hotel.room', string="Room", required=True, ondelete='cascade')
    image = fields.Image(string="Image", required=True)
    is_main = fields.Boolean(string="Main Image", default=False)

    @api.model
    def create(self, vals):
        if vals.get('is_main'):
            # Ensure only one main image per room
            self.search([
                ('room_id', '=', vals.get('room_id')),
                ('is_main', '=', True)
            ]).write({'is_main': False})
        return super().create(vals)

    def write(self, vals):
        if vals.get('is_main'):
            # Ensure only one main image per room
            for record in self:
                record.room_id.website_image_ids.filtered(
                    lambda img: img.id != record.id
                ).write({'is_main': False})
        return super().write(vals)
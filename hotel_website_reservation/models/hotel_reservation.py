# Copyright (C) 2024 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HotelReservation(models.Model):
    _inherit = "hotel.reservation"

    # Website booking fields
    website_booking = fields.Boolean(
        string="Website Booking",
        default=False,
        readonly=True,
        help="This reservation was made through the website"
    )
    website_confirmation_sent = fields.Boolean(
        string="Website Confirmation Sent",
        default=False,
        help="Website confirmation email has been sent"
    )
    advance_payment_amount = fields.Float(
        string="Advance Payment Amount",
        compute="_compute_advance_payment_amount",
        store=True,
        help="Amount required as advance payment"
    )
    advance_payment_percentage = fields.Float(
        string="Advance Payment %",
        related="room_id.booking_advance_percentage",
        readonly=True
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string="Sale Order",
        help="Related sale order for website booking"
    )
    payment_status = fields.Selection([
        ('pending', 'Payment Pending'),
        ('partial', 'Partially Paid'),
        ('paid', 'Fully Paid'),
        ('refunded', 'Refunded')
    ], string="Payment Status", default='pending', tracking=True)

    @api.depends('to_invoice_amount_total', 'room_id.booking_advance_percentage')
    def _compute_advance_payment_amount(self):
        """Compute advance payment amount based on percentage"""
        for reservation in self:
            if reservation.room_id and reservation.room_id.booking_advance_percentage:
                percentage = reservation.room_id.booking_advance_percentage / 100
                reservation.advance_payment_amount = reservation.to_invoice_amount_total * percentage
            else:
                reservation.advance_payment_amount = 0.0

    @api.model
    def create_website_reservation(self, vals):
        """Create a reservation from website booking"""
        vals.update({
            'website_booking': True,
            'state': 'draft'
        })
        
        # Validate dates
        if vals.get('checkin_date') and vals.get('checkout_date'):
            checkin = fields.Date.from_string(vals['checkin_date'])
            checkout = fields.Date.from_string(vals['checkout_date'])
            
            if checkin >= checkout:
                raise ValidationError(_("Check-out date must be after check-in date"))
            
            # Check minimum stay
            room = self.env['hotel.room'].browse(vals.get('room_id'))
            if room and room.min_stay_nights:
                nights = (checkout - checkin).days
                if nights < room.min_stay_nights:
                    raise ValidationError(
                        _("Minimum stay for this room is %d nights") % room.min_stay_nights
                    )
            
            # Check maximum stay
            if room and room.max_stay_nights:
                nights = (checkout - checkin).days
                if nights > room.max_stay_nights:
                    raise ValidationError(
                        _("Maximum stay for this room is %d nights") % room.max_stay_nights
                    )
        
        # Check availability
        if not self._check_room_availability(vals.get('room_id'), 
                                           vals.get('checkin_date'), 
                                           vals.get('checkout_date')):
            raise ValidationError(_("Selected room is not available for the chosen dates"))
        
        return self.create(vals)

    def _check_room_availability(self, room_id, checkin_date, checkout_date):
        """Check if room is available for the given dates"""
        existing_reservations = self.search([
            ('room_id', '=', room_id),
            ('state', 'in', ['draft', 'confirm']),
            '|',
            '&', ('checkin_date', '<=', checkin_date), ('checkout_date', '>', checkin_date),
            '&', ('checkin_date', '<', checkout_date), ('checkout_date', '>=', checkout_date)
        ])
        return len(existing_reservations) == 0

    def send_website_confirmation(self):
        """Send confirmation email for website booking"""
        template = self.env.ref('hotel_website_reservation.email_template_website_booking_confirmation', 
                               raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)
            self.website_confirmation_sent = True

    def action_create_sale_order(self):
        """Create sale order for website reservation"""
        if self.sale_order_id:
            return
        
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner_id.id,
            'hotel_reservation_id': self.id,
            'origin': self.reservation_no,
            'order_line': [(0, 0, {
                'product_id': self.room_id.product_id.id,
                'name': f"Hotel Room: {self.room_id.name}",
                'product_uom_qty': self.adults + self.children,
                'price_unit': self.room_id.list_price,
                'hotel_reservation_line_id': False,
            })]
        })
        self.sale_order_id = sale_order.id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sale Order'),
            'res_model': 'sale.order',
            'res_id': sale_order.id,
            'view_mode': 'form',
            'target': 'current',
        }
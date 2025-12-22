# Copyright (C) 2024 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    hotel_reservation_id = fields.Many2one(
        'hotel.reservation',
        string="Hotel Reservation",
        help="Related hotel reservation for this sale order"
    )
    is_hotel_booking = fields.Boolean(
        string="Is Hotel Booking",
        compute="_compute_is_hotel_booking",
        store=True,
        help="True if this sale order contains hotel room bookings"
    )

    @api.depends('order_line.product_id.is_hotel_room')
    def _compute_is_hotel_booking(self):
        """Compute if this sale order is for hotel booking"""
        for order in self:
            order.is_hotel_booking = any(
                line.product_id.product_tmpl_id.is_hotel_room 
                for line in order.order_line
            )

    def action_confirm(self):
        """Override to confirm hotel reservation when sale order is confirmed"""
        result = super().action_confirm()
        
        for order in self:
            if order.hotel_reservation_id and order.hotel_reservation_id.state == 'draft':
                order.hotel_reservation_id.action_confirm()
                order.hotel_reservation_id.payment_status = 'paid' if order.invoice_status == 'invoiced' else 'partial'
        
        return result

    def _create_invoices(self, grouped=False, final=False, date=None):
        """Override to update payment status in hotel reservation"""
        moves = super()._create_invoices(grouped=grouped, final=final, date=date)
        
        for order in self:
            if order.hotel_reservation_id:
                if order.invoice_status == 'invoiced':
                    order.hotel_reservation_id.payment_status = 'paid'
                elif order.invoice_status == 'to invoice':
                    order.hotel_reservation_id.payment_status = 'partial'
        
        return moves


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    hotel_reservation_line_id = fields.Many2one(
        'hotel.reservation.line',
        string="Hotel Reservation Line",
        help="Related hotel reservation line"
    )
    checkin_date = fields.Date(
        string="Check-in Date",
        help="Check-in date for hotel room booking"
    )
    checkout_date = fields.Date(
        string="Check-out Date", 
        help="Check-out date for hotel room booking"
    )
    room_id = fields.Many2one(
        'hotel.room',
        string="Hotel Room",
        help="Selected hotel room"
    )

    @api.onchange('product_id')
    def _onchange_product_id_hotel_room(self):
        """Set hotel room when product is selected"""
        if self.product_id and self.product_id.product_tmpl_id.is_hotel_room:
            self.room_id = self.product_id.product_tmpl_id.hotel_room_id.id
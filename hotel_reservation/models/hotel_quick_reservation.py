# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class QuickRoomReservation(models.TransientModel):
    _name = "quick.room.reservation"
    _description = "Quick Room Reservation"

    partner_id = fields.Many2one("res.partner", "Customer", required=True)
    check_in = fields.Datetime(required=True)
    check_out = fields.Datetime(required=True)
    room_id = fields.Many2one("hotel.room", required=True)
    company_id = fields.Many2one("res.company", "Hotel", required=True)
    pricelist_id = fields.Many2one("product.pricelist", "pricelist")
    partner_invoice_id = fields.Many2one(
        "res.partner", "Invoice Address", required=True
    )
    partner_order_id = fields.Many2one("res.partner", "Ordering Contact", required=True)
    partner_shipping_id = fields.Many2one(
        "res.partner", "Delivery Address", required=True
    )
    adults = fields.Integer("Adults")
    children = fields.Integer("Children")
    summary_id = fields.Many2one("room.reservation.summary", "Reservation Summary")

    @api.onchange("check_out", "check_in")
    def _on_change_check_out(self):
        """
        When you change checkout or checkin it will check whether
        Checkout date should be greater than Checkin date
        and update dummy field
        -----------------------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        """
        if (self.check_out and self.check_in) and (self.check_out < self.check_in):
            raise ValidationError(
                _("Checkout date should be greater than Checkin date.")
            )

    @api.onchange("partner_id")
    def _onchange_partner_id_res(self):
        """
        When you change partner_id it will update the partner_invoice_id,
        partner_shipping_id and pricelist_id of the hotel reservation as well
        ---------------------------------------------------------------------
        @param self: object pointer
        """
        if not self.partner_id:
            self.update(
                {
                    "partner_invoice_id": False,
                    "partner_shipping_id": False,
                    "partner_order_id": False,
                }
            )
        else:
            addr = self.partner_id.address_get(["delivery", "invoice", "contact"])
            self.update(
                {
                    "partner_invoice_id": addr["invoice"],
                    "partner_shipping_id": addr["delivery"],
                    "partner_order_id": addr["contact"],
                    "pricelist_id": self.partner_id.property_product_pricelist.id,
                }
            )

    @api.model
    def default_get(self, fields):
        """
        To get default values for the object.
        @param self: The object pointer.
        @param fields: List of fields for which we want default values
        @return: A dictionary which of fields with values.
        """
        res = super().default_get(fields)
        keys = self._context.keys()
        if "date" in keys:
            res.update({"check_in": self._context["date"]})
        if "room_id" in keys:
            roomid = self._context["room_id"]
            res.update({"room_id": int(roomid)})
        if "summary_id" in keys:
            res.update({"summary_id": self._context["summary_id"]})
        return res

    def room_reserve(self):
        """
        This method create a new record for hotel.reservation
        -----------------------------------------------------
        @param self: The object pointer
        @return: action to reload the summary view or True.
        """
        hotel_res_obj = self.env["hotel.reservation"]
        for res in self:
            rec = hotel_res_obj.create(
                {
                    "partner_id": res.partner_id.id,
                    "partner_invoice_id": res.partner_invoice_id.id,
                    "partner_order_id": res.partner_order_id.id,
                    "partner_shipping_id": res.partner_shipping_id.id,
                    "checkin": res.check_in,
                    "checkout": res.check_out,
                    "company_id": res.company_id.id,
                    "pricelist_id": res.pricelist_id.id,
                    "adults": res.adults,
                    "children": res.children,
                    "reservation_line": [
                        (
                            0,
                            0,
                            {
                                "reserve": [(6, 0, res.room_id.ids)],
                                "name": res.room_id.name or " ",
                            },
                        )
                    ],
                }
            )
            # Automatically confirm the reservation
            rec.confirmed_reservation()
            
            # Update the reservation summary if it exists
            if res.summary_id:
                # Update date_to to one minute more and refresh
                new_date_to = res.summary_id.date_to + timedelta(minutes=1)
                res.summary_id.write({'date_to': new_date_to})
                # Trigger the onchange to refresh the summary
                res.summary_id.get_room_summary()
                
                # Return action to reload the summary view
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'room.reservation.summary',
                    'res_id': res.summary_id.id,
                    'view_mode': 'form',
                    'target': 'current',
                    'context': self.env.context,
                }
        return {'type': 'ir.actions.act_window_close'}

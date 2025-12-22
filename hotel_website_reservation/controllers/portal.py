# Copyright (C) 2024 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class HotelPortalController(CustomerPortal):
    """Portal controller for hotel reservations"""

    def _prepare_home_portal_values(self, counters):
        """Add hotel reservations count to portal home"""
        values = super()._prepare_home_portal_values(counters)
        
        if 'hotel_reservation_count' in counters:
            reservation_count = request.env['hotel.reservation'].search_count([
                ('partner_id', '=', request.env.user.partner_id.id),
                ('website_booking', '=', True)
            ])
            values['hotel_reservation_count'] = reservation_count
        
        return values

    def _prepare_portal_layout_values(self):
        """Add hotel reservations to portal menu"""
        values = super()._prepare_portal_layout_values()
        values['page_name'] = 'hotel_reservations'
        return values

    @http.route(['/my/hotel_reservations', '/my/hotel_reservations/page/<int:page>'], 
                type='http', auth="user", website=True)
    def portal_my_hotel_reservations(self, page=1, date_begin=None, date_end=None, 
                                   sortby=None, filterby=None, **kw):
        """Display user's hotel reservations in portal"""
        values = self._prepare_portal_layout_values()
        
        # Search domain
        domain = [
            ('partner_id', '=', request.env.user.partner_id.id),
            ('website_booking', '=', True)
        ]
        
        # Date filtering
        if date_begin and date_end:
            domain += [('checkin_date', '>=', date_begin), ('checkin_date', '<=', date_end)]
        
        # Sorting options
        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'checkin_date desc'},
            'name': {'label': _('Name'), 'order': 'reservation_no'},
            'state': {'label': _('State'), 'order': 'state'},
        }
        
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        
        # Filtering options
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'draft': {'label': _('Draft'), 'domain': [('state', '=', 'draft')]},
            'confirm': {'label': _('Confirmed'), 'domain': [('state', '=', 'confirm')]},
            'done': {'label': _('Done'), 'domain': [('state', '=', 'done')]},
        }
        
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']
        
        # Count
        reservation_count = request.env['hotel.reservation'].search_count(domain)
        
        # Pager
        pager = portal_pager(
            url="/my/hotel_reservations",
            url_args={'date_begin': date_begin, 'date_end': date_end, 
                     'sortby': sortby, 'filterby': filterby},
            total=reservation_count,
            page=page,
            step=self._items_per_page
        )
        
        # Get reservations
        reservations = request.env['hotel.reservation'].search(
            domain, order=order, limit=self._items_per_page, offset=pager['offset']
        )
        
        values.update({
            'reservations': reservations,
            'page_name': 'hotel_reservations',
            'pager': pager,
            'default_url': '/my/hotel_reservations',
            'searchbar_sortings': searchbar_sortings,
            'searchbar_filters': searchbar_filters,
            'sortby': sortby,
            'filterby': filterby,
        })
        
        return request.render("hotel_website_reservation.portal_my_hotel_reservations", values)

    @http.route(['/my/hotel_reservation/<int:reservation_id>'], 
                type='http', auth="user", website=True)
    def portal_hotel_reservation_detail(self, reservation_id, **kw):
        """Display hotel reservation details in portal"""
        reservation = request.env['hotel.reservation'].browse(reservation_id)
        
        # Check access rights
        if not reservation.exists() or reservation.partner_id != request.env.user.partner_id:
            return request.not_found()
        
        values = {
            'reservation': reservation,
            'page_name': 'hotel_reservation_detail',
        }
        
        return request.render("hotel_website_reservation.portal_hotel_reservation_detail", values)

    @http.route(['/my/hotel_reservation/<int:reservation_id>/cancel'], 
                type='http', auth="user", website=True, methods=['POST'])
    def portal_hotel_reservation_cancel(self, reservation_id, **kw):
        """Cancel hotel reservation from portal"""
        reservation = request.env['hotel.reservation'].browse(reservation_id)
        
        # Check access rights
        if not reservation.exists() or reservation.partner_id != request.env.user.partner_id:
            return request.not_found()
        
        # Check if cancellation is allowed
        if reservation.state not in ['draft', 'confirm']:
            return request.redirect(f'/my/hotel_reservation/{reservation_id}?error=cannot_cancel')
        
        # Cancel reservation
        reservation.action_cancel()
        
        return request.redirect(f'/my/hotel_reservation/{reservation_id}?message=cancelled')
# Copyright (C) 2024 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
from datetime import datetime, timedelta

from odoo import http, fields, _
from odoo.http import request
from odoo.addons.website.controllers.main import Website
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.exceptions import ValidationError


class HotelWebsiteController(http.Controller):

    @http.route(['/hotel', '/hotel/rooms'], type='http', auth="public", website=True)
    def hotel_rooms(self, **kwargs):
        """Display hotel rooms catalog"""
        rooms = request.env['hotel.room'].sudo().search([
            ('website_published', '=', True)
        ])
        
        # Get filter parameters
        checkin = kwargs.get('checkin')
        checkout = kwargs.get('checkout')
        guests = int(kwargs.get('guests', 1))
        
        # Filter available rooms if dates provided
        if checkin and checkout:
            try:
                checkin_date = fields.Date.from_string(checkin)
                checkout_date = fields.Date.from_string(checkout)
                available_rooms = []
                
                for room in rooms:
                    if room._check_availability(checkin_date) and room.capacity >= guests:
                        available_rooms.append(room)
                rooms = available_rooms
            except:
                pass
        
        values = {
            'rooms': rooms,
            'checkin': checkin,
            'checkout': checkout,
            'guests': guests,
            'page_name': 'hotel_rooms',
        }
        return request.render('hotel_website_reservation.hotel_rooms_page', values)

    @http.route(['/hotel/room/<int:room_id>'], type='http', auth="public", website=True)
    def hotel_room_detail(self, room_id, **kwargs):
        """Display hotel room details"""
        room = request.env['hotel.room'].sudo().browse(room_id)
        
        if not room.exists() or not room.website_published:
            return request.not_found()
        
        # Get availability for next 30 days
        start_date = fields.Date.today()
        end_date = start_date + timedelta(days=30)
        availability_calendar = room.get_availability_calendar(start_date, end_date)
        
        values = {
            'room': room,
            'availability_calendar': availability_calendar,
            'checkin': kwargs.get('checkin'),
            'checkout': kwargs.get('checkout'),
            'guests': kwargs.get('guests', 1),
            'page_name': 'hotel_room_detail',
        }
        return request.render('hotel_website_reservation.hotel_room_detail_page', values)

    @http.route(['/hotel/booking/check_availability'], type='json', auth="public", website=True)
    def check_availability(self, room_id, checkin_date, checkout_date, guests=1):
        """Check room availability via AJAX"""
        try:
            room = request.env['hotel.room'].sudo().browse(int(room_id))
            checkin = fields.Date.from_string(checkin_date)
            checkout = fields.Date.from_string(checkout_date)
            
            if not room.exists():
                return {'error': _('Room not found')}
            
            if checkin >= checkout:
                return {'error': _('Check-out date must be after check-in date')}
            
            if room.capacity < int(guests):
                return {'error': _('Room capacity exceeded')}
            
            # Check minimum stay
            nights = (checkout - checkin).days
            if room.min_stay_nights and nights < room.min_stay_nights:
                return {'error': _('Minimum stay is %d nights') % room.min_stay_nights}
            
            # Check availability
            available = room._check_availability(checkin)
            if not available:
                return {'error': _('Room not available for selected dates')}
            
            # Calculate price
            total_price = room.list_price * nights
            advance_amount = total_price * (room.booking_advance_percentage / 100)
            
            return {
                'available': True,
                'nights': nights,
                'total_price': total_price,
                'advance_amount': advance_amount,
                'currency_symbol': request.env.company.currency_id.symbol,
            }
            
        except Exception as e:
            return {'error': str(e)}

    @http.route(['/hotel/booking/create'], type='http', auth="public", website=True, methods=['POST'])
    def create_booking(self, **post):
        """Create a new hotel booking"""
        try:
            # Get form data
            room_id = int(post.get('room_id'))
            checkin_date = post.get('checkin_date')
            checkout_date = post.get('checkout_date')
            adults = int(post.get('adults', 1))
            children = int(post.get('children', 0))
            guest_name = post.get('guest_name')
            guest_email = post.get('guest_email')
            guest_phone = post.get('guest_phone', '')
            special_requests = post.get('special_requests', '')
            
            # Create or find partner
            partner = request.env['res.partner'].sudo().search([
                ('email', '=', guest_email)
            ], limit=1)
            
            if not partner:
                partner = request.env['res.partner'].sudo().create({
                    'name': guest_name,
                    'email': guest_email,
                    'phone': guest_phone,
                    'is_company': False,
                })
            
            # Create reservation
            reservation_vals = {
                'partner_id': partner.id,
                'room_id': room_id,
                'checkin_date': checkin_date,
                'checkout_date': checkout_date,
                'adults': adults,
                'children': children,
                'special_requests': special_requests,
            }
            
            reservation = request.env['hotel.reservation'].sudo().create_website_reservation(reservation_vals)
            
            # Create sale order for payment
            sale_order = request.env['sale.order'].sudo().create({
                'partner_id': partner.id,
                'hotel_reservation_id': reservation.id,
                'origin': reservation.reservation_no,
            })
            
            # Add room as product to sale order
            room = request.env['hotel.room'].sudo().browse(room_id)
            nights = (fields.Date.from_string(checkout_date) - fields.Date.from_string(checkin_date)).days
            
            request.env['sale.order.line'].sudo().create({
                'order_id': sale_order.id,
                'product_id': room.product_id.id if room.product_id else False,
                'name': f"Hotel Room: {room.name} ({nights} nights)",
                'product_uom_qty': nights,
                'price_unit': room.list_price,
                'checkin_date': checkin_date,
                'checkout_date': checkout_date,
                'room_id': room_id,
            })
            
            reservation.sale_order_id = sale_order.id
            
            # Redirect to payment page
            return request.redirect(f'/shop/payment?sale_order_id={sale_order.id}')
            
        except ValidationError as e:
            return request.render('hotel_website_reservation.booking_error_page', {
                'error_message': str(e),
                'page_name': 'booking_error'
            })
        except Exception as e:
            return request.render('hotel_website_reservation.booking_error_page', {
                'error_message': _('An unexpected error occurred. Please try again.'),
                'page_name': 'booking_error'
            })


class HotelWebsiteSale(WebsiteSale):
    """Extend WebsiteSale for hotel-specific functionality"""
    
    def _get_shop_payment_values(self, order, **kwargs):
        """Override to add hotel booking context"""
        values = super()._get_shop_payment_values(order, **kwargs)
        
        if order.is_hotel_booking and order.hotel_reservation_id:
            values.update({
                'hotel_reservation': order.hotel_reservation_id,
                'is_hotel_booking': True,
            })
        
        return values

    @http.route(['/shop/confirmation'], type='http', auth="public", website=True, sitemap=False)
    def shop_payment_confirmation(self, **post):
        """Override to send hotel booking confirmation"""
        result = super().shop_payment_confirmation(**post)
        
        # Get the sale order from session
        sale_order_id = request.session.get('sale_last_order_id')
        if sale_order_id:
            order = request.env['sale.order'].sudo().browse(sale_order_id)
            if order.hotel_reservation_id:
                # Send hotel booking confirmation email
                order.hotel_reservation_id.send_website_confirmation()
        
        return result
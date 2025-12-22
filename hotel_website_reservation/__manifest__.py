# Copyright (C) 2024 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Hotel Website Reservation",
    "version": "17.0.1.0.0",
    "author": "Serpent Consulting Services Pvt. Ltd., "
              "Odoo Community Association (OCA)",
    "category": "Hotel Management",
    "website": "https://github.com/OCA/vertical-hotel",
    "depends": [
        "hotel_reservation",
        "website_sale",
        "website",
        "portal",
    ],
    "license": "AGPL-3",
    "summary": "Online Hotel Room Reservations with Payment Integration",
    "description": """
Hotel Website Reservation
=========================

This module extends the hotel management system to allow customers to make
reservations directly from the website with online payment capabilities.

Features:
---------
* Online room availability checker
* Hotel room catalog with detailed information
* Customer reservation portal
* Integration with website_sale for online payments
* Email confirmations and notifications
* Responsive design for mobile devices
* Customer account management for bookings

The module integrates seamlessly with the existing hotel management modules
and provides a complete solution for online hotel reservations.
    """,
    "data": [
        "security/ir.model.access.csv",
        "data/website_menu.xml",
        "data/product_template_data.xml",
        "views/hotel_room_views.xml",
        "views/hotel_reservation_views.xml",
        "templates/hotel_website_templates.xml",
        "templates/hotel_reservation_templates.xml",
        "templates/hotel_portal_templates.xml",
    ],
    "demo": [
        "demo/hotel_website_demo.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "hotel_website_reservation/static/src/css/hotel_frontend.css",
            "hotel_website_reservation/static/src/js/hotel_reservation.js",
        ],
    },
    "images": ["static/description/banner.png"],
    "application": False,
    "installable": True,
    "auto_install": False,
}
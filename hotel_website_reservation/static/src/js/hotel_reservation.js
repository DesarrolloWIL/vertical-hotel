/* Hotel Website Reservation JavaScript */

odoo.define('hotel_website_reservation.booking', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var _t = core._t;

    publicWidget.registry.HotelBookingForm = publicWidget.Widget.extend({
        selector: '#bookingForm',
        events: {
            'change input[name="checkin_date"], input[name="checkout_date"]': '_onDateChange',
            'change select[name="adults"], select[name="children"]': '_onGuestChange',
            'submit': '_onFormSubmit',
        },

        /**
         * @override
         */
        start: function () {
            var self = this;
            this.roomId = this.$('input[name="room_id"]').val();
            this.pricePerNight = parseFloat(this.$el.data('price-per-night')) || 0;
            this.advancePercentage = parseFloat(this.$el.data('advance-percentage')) || 50;
            
            // Set minimum date to today
            var today = new Date().toISOString().split('T')[0];
            this.$('input[name="checkin_date"]').attr('min', today);
            this.$('input[name="checkout_date"]').attr('min', today);
            
            // Initial calculation if dates are present
            this._updatePricing();
            
            return this._super.apply(this, arguments);
        },

        /**
         * Handle date changes
         */
        _onDateChange: function () {
            var checkinDate = this.$('input[name="checkin_date"]').val();
            var checkoutDate = this.$('input[name="checkout_date"]').val();
            
            if (checkinDate && checkoutDate) {
                // Update minimum checkout date
                this.$('input[name="checkout_date"]').attr('min', checkinDate);
                
                // Check if checkout is after checkin
                if (new Date(checkoutDate) <= new Date(checkinDate)) {
                    var nextDay = new Date(checkinDate);
                    nextDay.setDate(nextDay.getDate() + 1);
                    this.$('input[name="checkout_date"]').val(nextDay.toISOString().split('T')[0]);
                }
                
                this._checkAvailability();
            }
        },

        /**
         * Handle guest count changes
         */
        _onGuestChange: function () {
            this._updatePricing();
        },

        /**
         * Check room availability
         */
        _checkAvailability: function () {
            var self = this;
            var checkinDate = this.$('input[name="checkin_date"]').val();
            var checkoutDate = this.$('input[name="checkout_date"]').val();
            var adults = parseInt(this.$('select[name="adults"]').val()) || 1;
            var children = parseInt(this.$('select[name="children"]').val()) || 0;
            var totalGuests = adults + children;

            if (!checkinDate || !checkoutDate) {
                return;
            }

            this._showLoading(true);

            ajax.jsonRpc('/hotel/booking/check_availability', 'call', {
                room_id: this.roomId,
                checkin_date: checkinDate,
                checkout_date: checkoutDate,
                guests: totalGuests
            }).then(function (result) {
                self._showLoading(false);
                
                if (result.error) {
                    self._showError(result.error);
                    self.$('button[type="submit"]').prop('disabled', true);
                } else if (result.available) {
                    self._showSuccess('Room is available for your selected dates!');
                    self._updatePricingFromServer(result);
                    self.$('button[type="submit"]').prop('disabled', false);
                }
            }).catch(function (error) {
                self._showLoading(false);
                self._showError(_t('Failed to check availability. Please try again.'));
                self.$('button[type="submit"]').prop('disabled', true);
            });
        },

        /**
         * Update pricing display
         */
        _updatePricing: function () {
            var checkinDate = this.$('input[name="checkin_date"]').val();
            var checkoutDate = this.$('input[name="checkout_date"]').val();
            
            if (checkinDate && checkoutDate) {
                var nights = this._calculateNights(checkinDate, checkoutDate);
                if (nights > 0) {
                    var totalPrice = this.pricePerNight * nights;
                    var advanceAmount = totalPrice * (this.advancePercentage / 100);
                    
                    this.$('#totalPrice span:last-child').text('$' + totalPrice.toFixed(2));
                    this.$('#advanceAmount span:last-child').text('$' + advanceAmount.toFixed(2));
                    this.$('#priceSummary').prepend(
                        '<div class="d-flex justify-content-between mb-2">' +
                        '<span>Nights:</span><span>' + nights + '</span></div>'
                    );
                }
            }
        },

        /**
         * Update pricing from server response
         */
        _updatePricingFromServer: function (data) {
            this.$('#totalPrice span:last-child').text(data.currency_symbol + data.total_price.toFixed(2));
            this.$('#advanceAmount span:last-child').text(data.currency_symbol + data.advance_amount.toFixed(2));
            
            // Update nights display
            var existingNights = this.$('#priceSummary .nights-display');
            if (existingNights.length) {
                existingNights.find('span:last-child').text(data.nights);
            } else {
                this.$('#priceSummary').prepend(
                    '<div class="d-flex justify-content-between mb-2 nights-display">' +
                    '<span>Nights:</span><span>' + data.nights + '</span></div>'
                );
            }
        },

        /**
         * Calculate number of nights
         */
        _calculateNights: function (checkin, checkout) {
            var checkinDate = new Date(checkin);
            var checkoutDate = new Date(checkout);
            var timeDiff = checkoutDate.getTime() - checkinDate.getTime();
            return Math.ceil(timeDiff / (1000 * 3600 * 24));
        },

        /**
         * Handle form submission
         */
        _onFormSubmit: function (event) {
            if (!this._validateForm()) {
                event.preventDefault();
                return false;
            }
            
            this._showLoading(true);
            this.$('button[type="submit"]').prop('disabled', true);
        },

        /**
         * Validate form data
         */
        _validateForm: function () {
            var isValid = true;
            var requiredFields = ['checkin_date', 'checkout_date', 'guest_name', 'guest_email'];
            
            requiredFields.forEach(function (field) {
                var input = this.$('input[name="' + field + '"]');
                if (!input.val()) {
                    input.addClass('is-invalid');
                    isValid = false;
                } else {
                    input.removeClass('is-invalid').addClass('is-valid');
                }
            }.bind(this));
            
            // Validate email format
            var email = this.$('input[name="guest_email"]').val();
            if (email && !this._isValidEmail(email)) {
                this.$('input[name="guest_email"]').addClass('is-invalid');
                isValid = false;
            }
            
            return isValid;
        },

        /**
         * Validate email format
         */
        _isValidEmail: function (email) {
            var emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return emailRegex.test(email);
        },

        /**
         * Show loading state
         */
        _showLoading: function (show) {
            if (show) {
                if (!this.$('.loading-overlay').length) {
                    this.$el.append(
                        '<div class="loading-overlay">' +
                        '<div class="spinner-border spinner-border-hotel" role="status">' +
                        '<span class="visually-hidden">Loading...</span>' +
                        '</div></div>'
                    );
                }
            } else {
                this.$('.loading-overlay').remove();
            }
        },

        /**
         * Show error message
         */
        _showError: function (message) {
            this._removeMessages();
            this.$el.prepend(
                '<div class="alert alert-danger alert-dismissible fade show" role="alert">' +
                '<i class="fa fa-exclamation-triangle me-2"></i>' + message +
                '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>' +
                '</div>'
            );
        },

        /**
         * Show success message
         */
        _showSuccess: function (message) {
            this._removeMessages();
            this.$el.prepend(
                '<div class="alert alert-success alert-dismissible fade show" role="alert">' +
                '<i class="fa fa-check-circle me-2"></i>' + message +
                '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>' +
                '</div>'
            );
        },

        /**
         * Remove existing messages
         */
        _removeMessages: function () {
            this.$('.alert').remove();
        },
    });

    // Room search form widget
    publicWidget.registry.HotelRoomSearch = publicWidget.Widget.extend({
        selector: '.hotel-room-search-form',
        events: {
            'change input[name="checkin"]': '_onSearchDateChange',
            'submit': '_onSearchSubmit',
        },

        /**
         * @override
         */
        start: function () {
            // Set minimum date to today
            var today = new Date().toISOString().split('T')[0];
            this.$('input[name="checkin"]').attr('min', today);
            this.$('input[name="checkout"]').attr('min', today);
            
            return this._super.apply(this, arguments);
        },

        /**
         * Handle search date changes
         */
        _onSearchDateChange: function () {
            var checkinDate = this.$('input[name="checkin"]').val();
            if (checkinDate) {
                this.$('input[name="checkout"]').attr('min', checkinDate);
                
                // Auto-set checkout to next day if not set
                var checkoutDate = this.$('input[name="checkout"]').val();
                if (!checkoutDate || new Date(checkoutDate) <= new Date(checkinDate)) {
                    var nextDay = new Date(checkinDate);
                    nextDay.setDate(nextDay.getDate() + 1);
                    this.$('input[name="checkout"]').val(nextDay.toISOString().split('T')[0]);
                }
            }
        },

        /**
         * Handle search form submission
         */
        _onSearchSubmit: function (event) {
            var checkinDate = this.$('input[name="checkin"]').val();
            var checkoutDate = this.$('input[name="checkout"]').val();
            
            if (!checkinDate || !checkoutDate) {
                event.preventDefault();
                alert(_t('Please select both check-in and check-out dates.'));
                return false;
            }
            
            if (new Date(checkoutDate) <= new Date(checkinDate)) {
                event.preventDefault();
                alert(_t('Check-out date must be after check-in date.'));
                return false;
            }
        },
    });

    return {
        HotelBookingForm: publicWidget.registry.HotelBookingForm,
        HotelRoomSearch: publicWidget.registry.HotelRoomSearch,
    };
});
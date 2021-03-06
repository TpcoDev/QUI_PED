odoo.define('website_dispatch_requests.website_portal', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    const Dialog = require('web.Dialog');
    const {_t, qweb} = require('web.core');
    var time = require('web.time');
    const ajax = require('web.ajax');

//    document.getElementById("partner_ids");
//    slcchange.addEventListener("change", function() {
//    console.log(slcchange.value)
//    });

    publicWidget.registry.dispatchForm = publicWidget.Widget.extend({
        selector: '.o_dispatch_form',
        events: {
            'change select[name="sale_order_id"]': '_onOrderChange',
            'change select[name="line_id"]': '_onLineChange',
            'change input[name="cantidad"]': '_onCantidadChange',
            'change select[name="partner_ids"]': '_onPartnerChange',
        },
        /**
         * @constructor
         */
        init: function () {
            this._super.apply(this, arguments);
            this._changePartner = _.debounce(this._changePartner.bind(this), 500);
            this._changeTaskTitle = _.debounce(this._changeTaskTitle.bind(this), 500);
        },
        /**
         * @override
         */
        start: function () {
            var def = this._super.apply(this, arguments);

            this.$order = this.$('select[name="sale_order_id"]');
            this.$line = this.$('select[name="line_id"]');
            this.$delivery = this.$('select[name="delivery_ids"]');
            this.$partner = this.$('select[name="partner_ids"]');
//            this.$lineOptions = this.$line.filter(':enabled').find('option:not(:first)');
            this.$partnerOptions = this.$partner.filter(':enabled').find('option:not(:first)');
            this.$deliveryOptions = this.$delivery.filter(':enabled').find('option:not(:first)');
            this.$datetimepicker = $('#datetimepicker4');
            this.$cantidadPendiente = $('input[name="cantidad_pendiente"]');
            this.$cantidadSolicitada = $('input[name="cantidad"]')
            this.$alert = $("#alert");

            const addBusinessDays = (date, days) => {
                var d = moment(new Date(date)).add(Math.floor(days / 5) * 7, 'd');
                var remaining = days % 5;
                while (remaining) {
                    d.add(1, 'd');
                    if (d.day() !== 0 && d.day() !== 6)
                        remaining--;
                }
                return d;
            };

            var datepickers_options = {
                minDate: addBusinessDays(new Date(), 3),
                maxDate: moment({y: 9999, M: 11, d: 31}),
                calendarWeeks: true,
                icons: {
                    date: 'fa fa-calendar',
                    next: 'fa fa-chevron-right',
                    previous: 'fa fa-chevron-left',
                    up: 'fa fa-chevron-up',
                    down: 'fa fa-chevron-down',
                },
                locale: moment.locale(),
                format: 'L',
                daysOfWeekDisabled: [0, 6],

            };

            this.$datetimepicker.datetimepicker(datepickers_options);

            // $(".alert").hide();

            this._adaptOrderForm();
            this._changeTaskTitle();
            this._changePartner();
            this._changeCantidadPendiente();

            return def;
        },


        /**
         * @private
         */
        _adaptOrderForm: function () {
//            var $orderID = (this.$order.val() || 0);
//            this.$lineOptions.detach();
//            var $displayedLine = this.$lineOptions.filter('[data-order_id=' + $orderID + ']');
//            var nb = $displayedLine.appendTo(this.$line).show().length;
//            this.$line.parent().toggle(nb >= 1);

            var $partnerID = (this.$partner.val() || 0);
            this.$partnerOptions.detach();
            var $displayedLine = this.$partnerOptions.filter('[data-partner_id != -1]');
            var nb = $displayedLine.appendTo(this.$partner).show().length;
            this.$partner.parent().toggle(nb >= 1);


        },

        /**
         * @private
         */
        _onOrderChange: function () {
            debugger;
            this._adaptOrderForm();
            this._changeTaskTitle();

            this._rpc({
                route: "/dispatch/get_products/",
                params: {
                    order_line_id: this.$order.val(),
                },
            }).then(function (data) {
                var linesSelect = $('#line_id');
                if (data['ids']) {
                    linesSelect.html('');
                    var opt = $('<option>').text('Producto...').attr('value', '-1');
                    linesSelect.append(opt);
                    for (var i in data['ids']) {
                        var opt = $('<option>').text(data['names'][i]).attr('value', data['ids'][i]);
                        linesSelect.append(opt);

                    }
                    var cantidad_pendiente = $("input[name='cantidad_pendiente']");
                    cantidad_pendiente.attr('value', 0);
                }

            });


        },

        /**
         * @private
         * @param {Event} ev
         */
        _onLineChange: function (ev) {
            debugger;
            console.log('Sale line', this.$line);
            this._changeTaskTitle();
            this._changeCantidadPendiente();

        },

        _changeAddress: function () {
            debugger;
            var self = this;
            var $partnerID = (this.$partner.val() || 0);
            this.$deliveryOptions.detach();
            var $displayedLine = this.$deliveryOptions.filter('[data-delivery_id=' + $partnerID + ']');
            var nb = $displayedLine.appendTo(this.$delivery).show().length;
            this.$delivery.parent().toggle(nb >= 1);
        },

        /**
         * @private
         * @param {Event} ev
         */
        _onPartnerChange: function (ev) {
            debugger;
            console.log('Partner', this.$partner);
            this._changePartner()
            this._changeAddress();

        },

        /**
         * @private
         * @param {Event} ev
         */
        _onCantidadChange: function (ev) {
            debugger;
            var self = this;

            if (parseInt(this.$cantidadSolicitada.val()) < 0 ||
                parseInt(this.$cantidadSolicitada.val()) > parseInt(this.$cantidadPendiente.val())) {
                this.$alert.css("display", "block");
                this.$cantidadSolicitada.val(0);
                window.setTimeout(function () {
                    self.$alert.css("display", "none");

                }, 3000);
            }

            this._rpc({
                route: "/dispatch/get_title/",
                params: {
                    order_sale_id: this.$order.val(),
                    order_line_id: this.$line.val(),
                    qty: this.$cantidadSolicitada.val(),
                },
            }).then(function (data) {
                // populate states and display
                var taskTitle = $("input[name='task_title']");
                taskTitle.attr('value', data);

            });
        },
        /**
         * @private
         */
        _changeTaskTitle: function () {
            debugger;
            var self = this;
            this._rpc({
                route: "/dispatch/get_title/",
                params: {
                    order_sale_id: this.$order.val(),
                    order_line_id: this.$line.val(),
                    qty: this.$cantidadSolicitada.val(),
                },
            }).then(function (data) {
                // populate states and display
                var taskTitle = $("input[name='task_title']");
                taskTitle.attr('value', data);

            });
        },


        /**
         * @private
         */
        _changePartner: function () {
            debugger;
            var self = this;
            var partner = $("input[name='partner_id']");
            if (this.$partner.val()) {
                partner.attr('value', this.$partner.val());
            }


            this._rpc({
                route: "/dispatch/get_sale_order_lines/",
                params: {
                    partner_id: this.$partner.val(),
                },
            }).then(function (data) {
                var select = document.getElementById("sale_order_id");
                var length = select.options.length;
                for (i = length - 1; i >= 0; i--) {
                    select.remove(i);
                }
                select.innerHTML += "<option value=0>Pedidos...</option>";
                if (data['ids'])
                    for (var i in data['ids']) {
                        select.innerHTML += "<option value='" + data['ids'][i] + "'>" + data['names'][i] + "</option>";
                    }
                var select = document.getElementById("line_id");
                var length = select.options.length;
                for (i = length - 1; i >= 0; i--) {
                    select.remove(i);
                }
                select.innerHTML += "<option value=0>Producto...</option>";
                var taskTitle = $("input[name='task_title']");
                taskTitle.attr('value', '');
                self.$cantidadPendiente.attr('value', 0);
            });

        },

        /**
         * @private
         */
        _changeCantidadPendiente: function () {
            debugger;
            var self = this;

            this._rpc({
                route: "/dispatch/get_cantidad/",
                params: {
                    order_line_id: this.$line.val(),
                },
            }).then(function (data) {
                // populate states and display
                self.$cantidadPendiente.attr('value', data);

            });
        },


    });


});
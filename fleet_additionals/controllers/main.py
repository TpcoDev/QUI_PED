# -*- coding: utf-8 -*-

import logging
from collections import OrderedDict
import requests
from odoo import http, tools, _
from odoo.http import request
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.portal.controllers.mail import PortalChatter
from odoo.tools.misc import consteq
from odoo.addons.portal.controllers.portal import get_records_pager, CustomerPortal, pager as portal_pager
from odoo.osv.expression import OR
import json
import logging

_logger = logging.getLogger(__name__)


class DispatchRequestsController(http.Controller):
    
    def values_preprocess(self, values):
        return values
    
    def _get_mandatory_fields(self):
        return [
            "task_title", "dispatch_date", "cantidad", "sale_order_id", "line_id",
            'horarios_recepcion'
        ]
    
    def checkout_form_validate(self, data):
        # all_form_values: all values before preprocess
        # data: values after preprocess
        error = dict()
        error_message = []
        
        # Required fields from form
        required_fields = self._get_mandatory_fields()
        # error message for empty required fields
        for field_name in required_fields:
            if not data.get(field_name):
                error[field_name] = 'missing'
        
        if [err for err in error.items() if err == 'missing']:
            error_message.append(_('Some required fields are empty.'))
        
        return error, error_message
    
    @http.route('/dispatch/errors', type='json', auth="public", methods=['POST'], website=True)
    def add_errors(self, **kw):
        error = {
            'error': {'error_message': 'La cantidad solicitada no puede ser mayor a la cantidad pendiente'}
        }
        return error
    
    @http.route('/dispatch/get_title', type='json', auth="public", methods=['POST'], website=True)
    def get_task_title(self, order_sale_id=False, order_line_id=False, qty=False, **kw):
        title = name = default_code = product_uom_name = ''
        product_uom_qty = -1
        if order_sale_id:
            order_id = request.env['sale.order'].sudo().browse(int(order_sale_id))
            name = order_id.name
        if order_line_id:
            order_line_id = request.env['sale.order.line'].sudo().browse(int(order_line_id))
            default_code = order_line_id.product_id.default_code
            product_uom_name = order_line_id.product_uom.name
        if qty:
            product_uom_qty = qty
        
        if name:
            title += f'{name}'
        if default_code:
            title += f'-{default_code}'
        if product_uom_qty:
            product_uom_qty = 0 if product_uom_qty == -1 else product_uom_qty
            title += f'-{product_uom_qty}'
        if product_uom_name:
            title += f'-{product_uom_name}'
        return title
    
    @http.route('/dispatch/get_cantidad', type='json', auth="public", methods=['POST'], website=True)
    def get_cantidad(self, order_line_id=False, **kw):
        cantidad = 0
        if order_line_id:
            order_line_id = request.env['sale.order.line'].sudo().browse(int(order_line_id))
            moves = request.env['stock.move'].sudo().search(
                [('state', '!=', 'cancel'), ('sale_line_id', '=', order_line_id.id)])
            sum_qty = sum(moves.mapped('product_uom_qty'))
            cantidad = order_line_id.product_uom_qty - sum_qty
        return abs(cantidad)
    
    @http.route('/dispatch/validate', type='http', auth="user", website=True)
    def dispatch_validate(self, page=0, category=None, topic=None, search='', ppg=False, **post):
        default = request.env['res.config.settings'].sudo().get_values()
        errors, error_msg = self.checkout_form_validate(post)
        
        partner_id = request.env.user.partner_id.id
        if errors:
            sale_order_lines = request.env['sale.order.line'].search(
                [('order_id.state', '=', 'sale'), ('order_id.partner_id', '=', partner_id)]
            ).filtered(lambda r: r.qty_delivered < r.product_uom_qty)
            product_ids = sale_order_lines.mapped('product_id')
            sale_order_ids = sale_order_lines.mapped('order_id')
            
            vals = {
                'search': search,
                'sale_order_ids': sale_order_ids,
                'product_ids': product_ids,
                'sale_order_lines': sale_order_lines,
                'partner_id': partner_id,
                'error': errors,
                'checkout': post,
            }
            errors['error_message'] = error_msg
            return request.render("website_dispatch_requests.dispatch_form", vals)
        
        task = request.env['project.task'].create_project_task(post)
        if task:
            return request.render(
                "website_dispatch_requests.task_created", task)
        
        return request.render("website_dispatch_requests.dispatch_form", {})
    
    @http.route('/dispatch', type='http', auth="user", website=True)
    def dispatch(self, page=0, category=None, topic=None, search='', ppg=False, **post):
        _logger.info("Entrando al controlador")
        default = request.env['res.config.settings'].sudo().get_values()
        request.context = dict(request.context, partner=request.env.user.partner_id)
        Partner = request.env['res.partner'].with_context(show_address=1).sudo()
        mode = False
        checkout_values, errors = {}, {}
        partner_id = request.env.user.partner_id.id
        # if request.env.user.partner_id.id == request.website.user_id.sudo().partner_id.id:
        #     return request.render("website_helpdesk_system.login_required", {})
        request.context = dict(request.context, partner=request.env.user.partner_id)
        
        sale_order_lines = request.env['sale.order.line'].search(
            [('order_id.state', '=', 'sale'), ('order_id.partner_id', '=', partner_id)]
        ).filtered(lambda r: r.qty_delivered < r.product_uom_qty)
        product_ids = sale_order_lines.mapped('product_id')
        sale_order_ids = sale_order_lines.mapped('order_id')
        
        cantidad = cantidad_pendiente = 0
        checkout_values.update({
            'cantidad_pendiente': cantidad_pendiente,
            'cantidad': cantidad
        })
        
        keep = QueryURL('/dispatch')
        values = {
            'search': search,
            'sale_order_ids': sale_order_ids,
            'product_ids': product_ids,
            'sale_order_lines': sale_order_lines,
            'partner_id': request.env.user.partner_id.id,
            'keep': keep,
            'error': errors,
            'checkout': checkout_values,
            # 'recaptcha_security_enable': default.get('enabled_recaptcha')
        }
        
        return request.render("website_dispatch_requests.dispatch_form", values)
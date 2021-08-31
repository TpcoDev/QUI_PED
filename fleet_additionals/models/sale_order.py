# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    dispatch_name = fields.Char(compute='_compute_dispatch_name', string='Nombre del pedido')
    
    @api.depends('name', 'client_order_ref')
    def _compute_dispatch_name(self):
        for rec in self:
            var_name = rec.name
            if rec.client_order_ref:
                var_name += f' - {rec.client_order_ref}'
            
            rec.dispatch_name = var_name

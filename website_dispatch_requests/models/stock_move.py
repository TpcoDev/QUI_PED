# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class StockMove(models.Model):
    _inherit = 'stock.move'

    sale_order_id = fields.Many2one(comodel_name='sale.order', string=_('Orden'), required=False)
    partner_name = fields.Char(related='partner_id.name', string=_('Nombre del cliente'))
    partner_codigo_sap = fields.Char(related='partner_id.vat', string=_('Código SAP'))
    line_price_unit = fields.Float(related='sale_line_id.price_unit', string=_('Precio unitario de venta'))
    total_reserved = fields.Float(compute='_compute_total', string=_('Total Reservado'))
    total_demanded = fields.Float(compute='_compute_total', string=_('Total Demandado'))

    @api.depends('reserved_availability', 'product_uom_qty', 'line_price_unit')
    def _compute_total(self):
        for rec in self:
            rec.total_reserved = rec.reserved_availability * rec.line_price_unit
            rec.total_demanded = rec.product_uom_qty * rec.line_price_unit

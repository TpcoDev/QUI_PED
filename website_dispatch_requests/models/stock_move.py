# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class StockMove(models.Model):
    _inherit = 'stock.move'

    sale_order_id = fields.Many2one(comodel_name='sale.order', string=_('Orden'), required=False)
    partner_name = fields.Char(related='partner_id.name', string=_('Nombre del cliente'))
    partner_codigo_sap = fields.Char(related='partner_id.vat', string=_('Código SAP'))
    line_price_unit = fields.Float(related='sale_line_id.price_unit', string=_('Precio unitario de venta'))
    total_reserved = fields.Monetary(compute='_compute_total', string=_('Total Reservado'), currency_field='company_currency')
    total_demanded = fields.Monetary(compute='_compute_total', string=_('Total Demandado'), currency_field='company_currency')

    company_currency = fields.Many2one(
        comodel_name="res.currency", string='Currency', related='company_id.currency_id',
        readonly=True
    )

    @api.depends('reserved_availability', 'product_uom_qty', 'line_price_unit')
    def _compute_total(self):
        for rec in self:
            rec.total_reserved = rec.reserved_availability * rec.line_price_unit
            rec.total_demanded = rec.product_uom_qty * rec.line_price_unit

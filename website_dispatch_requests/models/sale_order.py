# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    dispatch_name = fields.Char(compute='_compute_dispatch_name', string='Nombre del pedido')
    codigo_sap = fields.Char(related='partner_id.vat', string='Cod SAP')
    lc_verificacion = fields.Selection(
        selection=[('pendiente', _('Pendiente')), ('aprobado', _('Aprobado')), ('no_aprueba', _('No Aprueba'))],
        default='pendiente', string=_('Verificación LC')
    )

    lc_fecha_hora_verificacion = fields.Datetime(string=_('Fecha y hora Verificación'))
    lc_fecha_hora = fields.Datetime(related='partner_id.lc_fecha_hora', string=_('Fecha y hora LC'))
    lc_disponible = fields.Monetary(related='partner_id.lc_disponible', currency_field='company_currency',
                                    tracking=True)
    company_currency = fields.Many2one(
        comodel_name="res.currency", string='Currency', related='company_id.currency_id',
        readonly=True
    )

    move_ids = fields.One2many(
        comodel_name='stock.move',
        inverse_name='sale_order_id', string=_('Detalle Ordenes Pendientes')
    )

    @api.depends('name', 'client_order_ref')
    def _compute_dispatch_name(self):
        for rec in self:
            var_name = rec.name
            if rec.client_order_ref:
                var_name += f' - {rec.client_order_ref}'

            rec.dispatch_name = var_name

    @api.onchange('partner_id')
    def _onchange_moves(self):
        if self.partner_id:
            moves = self.env['stock.move'].search([('partner_id', '=', self.partner_id.id)])
            self.move_ids = [(6, 0, moves.ids)]

# -*- coding: utf-8 -*-

from itertools import groupby
from odoo import fields, models, api, _


class StockMove(models.Model):
    _inherit = 'stock.move'

    sale_order_id = fields.Many2one(comodel_name='sale.order', string=_('Orden'), required=False)
    task_id = fields.Many2one(comodel_name='project.task', string=_('Tarea'), required=False)
    partner_name = fields.Char(related='partner_id.name', string=_('Nombre del cliente'))
    partner_codigo_sap = fields.Char(related='partner_id.vat', string=_('Código SAP'))
    line_price_unit = fields.Float(related='sale_line_id.price_unit', string=_('Precio unitario de venta'))
    total_reserved = fields.Monetary(compute='_compute_total', string=_('Total Reservado'),
                                     currency_field='company_currency')
    total_demanded = fields.Monetary(compute='_compute_total', string=_('Total Demandado'),
                                     currency_field='company_currency')

    company_currency = fields.Many2one(
        comodel_name="res.currency", string='Currency', related='company_id.currency_id',
        readonly=True
    )

    @api.depends('reserved_availability', 'product_uom_qty', 'line_price_unit')
    def _compute_total(self):
        for rec in self:
            rec.total_reserved = rec.reserved_availability * rec.line_price_unit
            rec.total_demanded = rec.product_uom_qty * rec.line_price_unit

    def _assign_picking(self):
        """ Try to assign the moves to an existing picking that has not been
        reserved yet and has the same procurement group, locations and picking
        type (moves should already have them identical). Otherwise, create a new
        picking to assign them to. """
        Picking = self.env['stock.picking']
        grouped_moves = groupby(sorted(self, key=lambda m: [f.id for f in m._key_assign_picking()]),
                                key=lambda m: [m._key_assign_picking()])
        for group, moves in grouped_moves:
            moves = self.env['stock.move'].concat(*list(moves))
            new_picking = False
            # Could pass the arguments contained in group but they are the same
            # for each move that why moves[0] is acceptable
            picking = moves[0]._search_picking_for_assignation()
            if picking and not self.env.context.get('dispatch_qty', False):
                if any(picking.partner_id.id != m.partner_id.id or
                       picking.origin != m.origin for m in moves):
                    # If a picking is found, we'll append `move` to its move list and thus its
                    # `partner_id` and `ref` field will refer to multiple records. In this
                    # case, we chose to  wipe them.
                    picking.write({
                        'partner_id': False,
                        'origin': False,
                    })
            else:
                new_picking = True
                picking = Picking.create(moves._get_new_picking_values())

            moves.write({'picking_id': picking.id})
            moves._assign_picking_post_process(new=new_picking)
        return True

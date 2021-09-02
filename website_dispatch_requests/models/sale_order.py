# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    d_state = fields.Char(compute='_search_available_orders', string='Estado de despacho')

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

    move_ids = fields.Many2many(
        comodel_name='stock.move', string=_('Detalle Ordenes Pendientes')
    )

    total_reserved = fields.Monetary(compute='_compute_total', string=_('Total Reservado'),
                                     currency_field='company_currency')
    total_demanded = fields.Monetary(compute='_compute_total', string=_('Total Demandado'),
                                     currency_field='company_currency')

    @api.depends('order_line')
    def _search_available_orders(self):
        for rec in self:
            lines = rec.order_line.filtered(lambda r: r.state == 'sale' and r.qty_delivered < r.product_uom_qty)
            rec.d_state = _('opened') if len(lines) > 0 else _('closed')

    @api.depends('move_ids.reserved_availability', 'move_ids.product_uom_qty', 'move_ids.line_price_unit')
    def _compute_total(self):
        self.ensure_one()
        if len(self.move_ids):
            for rec in self.move_ids:
                self.total_reserved += rec.reserved_availability * rec.line_price_unit
                self.total_demanded += rec.product_uom_qty * rec.line_price_unit
        else:
            self.total_demanded = 0.0
            self.total_reserved = 0.0

    @api.depends('name', 'client_order_ref')
    def _compute_dispatch_name(self):
        for rec in self:
            var_name = ''
            if rec.client_order_ref:
                var_name += f'{rec.client_order_ref} -'
            var_name += f'{rec.name}'
            rec.dispatch_name = var_name

    @api.returns('mail.message', lambda value: value.id)
    def message_chatter(self, **kwargs):
        return super(SaleOrder, self).message_post(**kwargs)

    @api.onchange('lc_verificacion')
    def _onchange_lc_verificacion(self):
        self.ensure_one()
        if self.lc_verificacion == 'aprobado':
            self.lc_fecha_hora_verificacion = fields.Datetime.now()
            display_msg = (
                f"LC Disponible {self.lc_disponible} \n"
                f"Verificación LC {self.lc_verificacion} \n"
                f"Fecha y hora Verificación {self.lc_fecha_hora_verificacion} \n"
                f"Fecha y hora LC {self.lc_fecha_hora} \n"
            )
            order = self.env['sale.order'].search([('id', 'in', self.ids)], limit=1)
            if order:
                order.message_chatter(
                    subject="LC Verificacion -> Aprobada",
                    body=display_msg
                )
        elif self.lc_verificacion == 'pendiente':
            self.lc_fecha_hora_verificacion = False

    def load_moves(self, partner):
        if self.partner_id:
            moves = self.env['stock.move'].search(
                [('partner_codigo_sap', '=', self.partner_id.vat), ('state', 'not in', ('cancel', 'done'))])
            self.move_ids = [(6, 0, moves.ids)]

    @api.model
    def default_get(self, fields):
        res = super(SaleOrder, self).default_get(fields)
        self.load_moves(self.partner_id)
        return res

    @api.onchange('partner_id')
    def _onchange_moves(self):
        self.load_moves(self.partner_id)

    def _action_confirm(self):
        ctx = self.env.context.copy()
        ctx.update({'no_create_picking': True})
        self = self.with_context(ctx)
        return super(SaleOrder, self)._action_confirm()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _get_qty_procurement(self, previous_product_uom_qty=False):
        self.ensure_one()

        if self.env.context.get('dispatch_qty', False):
            return self.env.context['dispatch_qty']
        return super(SaleOrderLine, self)._get_qty_procurement(previous_product_uom_qty=previous_product_uom_qty)

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        if self.env.context.get('no_create_picking', False) == True:
            return True
        return super(SaleOrderLine, self)._action_launch_stock_rule(previous_product_uom_qty)

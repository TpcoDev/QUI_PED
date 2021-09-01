# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    lc_fecha_hora = fields.Datetime(string=_('Fecha y hora LC'))
    lc_disponible = fields.Monetary(currency_field='company_currency', tracking=True)

    company_currency = fields.Many2one(
        comodel_name="res.currency", string='Currency', related='company_id.currency_id',
        readonly=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('parent_id', False):
                parent_id = self.browse(vals['parent_id'])
                vals.update({
                    'lc_fecha_hora': parent_id.lc_fecha_hora,
                    'lc_disponible': parent_id.lc_disponible
                })
        return super(ResPartner, self).create(vals_list)

    def write(self, vals):
        lc_fecha_hora = self.lc_fecha_hora
        lc_disponible = self.lc_disponible

        if 'lc_fecha_hora' in vals:
            lc_fecha_hora = vals['lc_fecha_hora']
        if 'lc_disponible' in vals:
            lc_disponible = vals['lc_disponible']

        if self.child_ids:
            self.child_ids.write({
                'lc_fecha_hora': lc_fecha_hora,
                'lc_disponible': lc_disponible
            })

        return super(ResPartner, self).write(vals)

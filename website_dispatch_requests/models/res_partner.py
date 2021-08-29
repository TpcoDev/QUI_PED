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

    def write(self, vals):
        if self.parent_id:
            vals.update({
                'lc_fecha_hora': self.parent_id.lc_fecha_hora,
                'lc_disponible': self.parent_id.lc_disponible
            })
        if self.child_ids:
            self.child_ids.write({
                'lc_fecha_hora': self.lc_fecha_hora,
                'lc_disponible': self.lc_disponible
            })

        return super(ResPartner, self).write(vals)

from odoo import fields, models, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    partner_request_ids = fields.Many2many(comodel_name="res.partner", string='Cientes permitidos')

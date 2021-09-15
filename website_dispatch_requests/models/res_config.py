from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    horas_diferencias = fields.Integer()

    @api.model
    def get_values(self):
        res = super().get_values()
        res.update(
            horas_diferencias=self.env["ir.config_parameter"].sudo().get_param("horas_diferencias"),
        )
        return res

    def set_values(self):
        super().set_values()
        for record in self:
            self.env['ir.config_parameter'].sudo().set_param("horas_diferencias", record.horas_diferencias)
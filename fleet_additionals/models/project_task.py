# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta,date
import logging
import pytz

_logger = logging.getLogger(__name__)


class ProjectTask(models.Model):
    _inherit = 'project.task'

    dia_operacion = fields.Date('Fecha operación')
    chofer_camion = fields.Char('Chofer')
    patente_remolque = fields.Char('Patente Remolque')
    patente_camion_tracto = fields.Char('Patente Camion Tracto')
    modelo_remolque = fields.Char('Nombre vehículo')
    status = fields.Char('Estado')

    remolques_ids = fields.One2many(comodel_name="remolque_dia", inverse_name="task_id", string="Remolques")

    asignar_remolque_id = fields.One2many(comodel_name="asignar_remolque", inverse_name="task_id", string="Remolque asignado")

    mostrar_page = fields.Boolean(compute='_compute_mostrar_page')

    @api.onchange('planned_date_begin')
    def _onchange_planned_date_begin(self):
        ids = []
        remolques = self.env['remolque_dia'].search([])
        fecha = datetime.strptime(str(self.planned_date_begin),'%Y-%m-%d %H:%M:%S').strftime("%Y-%m-%d")
        for remolque in remolques:
            if str(fecha) == str(remolque.dia_operacion):
                ids.append(remolque.id)
        self.remolques_ids = [(6, 0, ids)]

    @api.depends('stage_id','planification','partner_id','picking_id')
    def _compute_mostrar_page(self):
        res = False
        for task in self:
            if task.stage_id:
                if (task.stage_id.name == 'Nuevo' or task.stage_id.name == 'New')\
                        and task.planification == 'planifica' and \
                        task.partner_id:
                    res = True
                else:
                    res = False

                if task.picking_id:
                    if task.state_oe == 'assigned':
                        res = True
                    else:
                        res = False

            task.mostrar_page = res



# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _, exceptions
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta, date
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
    capacidad_carga = fields.Float('Capacidad carga', digits=(16, 3))

    remolque_ids = fields.Many2many(comodel_name="remolque_dia", string='Remolques')

    # remolque_ids = fields.One2many(comodel_name="remolque_dia",inverse_name="task_id", string='Remolques')

    asignar_remolque_id = fields.One2many(comodel_name="asignar_remolque", inverse_name="task_id",
                                          string="Remolque asignado")

    mostrar_page = fields.Boolean(compute='_compute_mostrar_page')

    @api.onchange('planned_date_begin', 'stage_id')
    def _onchange_planned_date_begin(self):
        ids = []
        remolques = self.env['remolque_dia']
        for task in self:
            if task.planned_date_begin:
                # fecha = datetime.strptime(str(self.planned_date_begin),'%Y-%m-%d %H:%M:%S').strftime("%Y-%m-%d")
                fecha = fields.Datetime.context_timestamp(self, datetime.strptime(str(task.planned_date_begin),
                                                                                  '%Y-%m-%d %H:%M:%S')).strftime(
                    "%Y-%m-%d")
                remolques = remolques.search([('dia_operacion', '=', fecha)])
                for remolque in remolques:
                    # if type(task.id.origin) == int:
                    #     remolque.task_id = task.id.origin
                    ids.append(remolque.id)
                    # else:
                    #     raise exceptions.ValidationError(u'La solicitud debe estar guardada.')

            task.remolque_ids = [(6, 0, ids)]

    @api.depends('stage_id', 'planification', 'partner_id', 'picking_id')
    def _compute_mostrar_page(self):
        res = False
        for task in self:
            if task.stage_id:
                if (task.stage_id.name == 'Solicitado' or task.stage_id.name == 'New') \
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
            if res and len(task.asignar_remolque_id) > 0:
                self.cargar_remolques_asignados()
            task.mostrar_page = res

    def cargar_remolques_asignados(self):
        ids = []
        remolque_asignado = self.env['asignar_remolque']
        tasks = self.env['project.task']
        for tarea in self:
            if tarea.dia_operacion and tarea.patente_remolque:
                tasks = tasks.search(
                    [('dia_operacion', '=', tarea.dia_operacion), ('patente_remolque', '=', tarea.patente_remolque)])
                for task in tasks:
                    res = remolque_asignado.create({
                        'dia_operacion': task.dia_operacion,
                        'solicitud_despacho': task.name,
                        'patente_remolque': task.patente_remolque,
                        'modelo_remolque': task.modelo_remolque,
                        'status_remolque': task.status,
                        'capacidad_carga': task.capacidad_carga,
                        'cantidad_despachar': task.cantidad_despachar,
                        'cliente': task.partner_id.id if task.partner_id else False,
                        'pedido_venta': task.sale_order_id.id if task.sale_order_id else False,
                        'orden_entrega': task.picking_id.id if task.picking_id else False,
                        'asignada': task.user_id.id if task.user_id else False
                    })
                    ids.append(res.id)
        tarea.asignar_remolque_id = [(6, 0, ids)]

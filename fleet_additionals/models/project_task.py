# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _, exceptions
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
    capacidad_carga = fields.Float('Capacidad carga', digits=(16, 3))


    remolque_ids = fields.Many2many(comodel_name="remolque_dia",string='Remolques')

    #remolque_ids = fields.One2many(comodel_name="remolque_dia",inverse_name="task_id", string='Remolques')

    asignar_remolque_id = fields.One2many(comodel_name="asignar_remolque", inverse_name="task_id", string="Remolque asignado")

    mostrar_page = fields.Boolean(compute='_compute_mostrar_page')

    def desasignar_remolque(self):
        for task in self:
            task.dia_operacion = None
            task.chofer_camion = None
            task.patente_remolque = None
            task.patente_camion_tracto = None
            task.modelo_remolque = None
            task.status = None
            task.capacidad_carga = 0


    @api.onchange('planned_date_begin','stage_id')
    def _onchange_planned_date_begin(self):
        ids = []
        remolques = self.env['remolque_dia']
        for task in self:
            if task.planned_date_begin:
                #fecha = datetime.strptime(str(self.planned_date_begin),'%Y-%m-%d %H:%M:%S').strftime("%Y-%m-%d")
                fecha = fields.Datetime.context_timestamp(self, datetime.strptime(str(task.planned_date_begin),
                                                                                      '%Y-%m-%d %H:%M:%S')).strftime("%Y-%m-%d")
                remolques = remolques.search([('dia_operacion','=',fecha),('status_trailer_day','=','disponible')])
                for remolque in remolques:
                    # if type(task.id.origin) == int:
                    #     remolque.task_id = task.id.origin
                    ids.append(remolque.id)
                    # else:
                    #     raise exceptions.ValidationError(u'La solicitud debe estar guardada.')

            task.remolque_ids = [(6, 0, ids)]

    @api.depends('stage_id','planification','partner_id','picking_id')
    def _compute_mostrar_page(self):
        res = False
        for task in self:
            if task.stage_id:
                if (task.stage_id.name == 'Solicitado' or task.stage_id.name == 'New')\
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
            print(len(task.asignar_remolque_id))
            if len(task.asignar_remolque_id) > 0:
                self.cargar_remolques_asignados()
            if task.planned_date_begin:
                self._onchange_planned_date_begin()
            task.mostrar_page = res


    def cargar_remolques_asignados(self):
        ids = []
        tasks = self.env['project.task']
        remolque = self.env['remolque_dia']
        for tarea in self:
            if tarea.dia_operacion and tarea.patente_remolque:
                tasks = tasks.search([('dia_operacion', '=', tarea.dia_operacion),
                                      ('patente_remolque', '=', tarea.patente_remolque)])
                remolque = remolque.search([('dia_operacion', '=', tarea.dia_operacion),
                                      ('patente_remolque', '=', tarea.patente_remolque)])
                tarea.status = dict(self.env['remolque_dia'].fields_get(allfields=['status_trailer_day'])
                                                   ['status_trailer_day']['selection'])[remolque.status_trailer_day]
                for task in tasks:
                    res = self.crear_remolque_asiganado(task)
                    ids.append(res.id)
            elif tarea.asignar_remolque_id:
                tasks = tasks.search([('dia_operacion','=',tarea.asignar_remolque_id[0].dia_operacion),('patente_remolque','=',tarea.asignar_remolque_id[0].patente_remolque)])
                for task in tasks:
                    res = self.crear_remolque_asiganado(task)
                    ids.append(res.id)
            else:
                res = self.crear_remolque_asiganado(tarea)
                ids.append(res.id)

            if not ids:
                res = self.crear_remolque_asiganado(tarea)
                ids.append(res.id)
        tarea.asignar_remolque_id = [(6, 0, ids)]


    def crear_remolque_asiganado(self,task):
        remolque_asignado = self.env['asignar_remolque']
        res = remolque_asignado.create({
            'dia_operacion': task.dia_operacion if task.dia_operacion else task.asignar_remolque_id[0].dia_operacion if task.asignar_remolque_id else False,
            'solicitud_despacho': task.name,
            'patente_remolque': task.patente_remolque if task.patente_remolque else task.asignar_remolque_id[0].patente_remolque if task.asignar_remolque_id else False,
            'modelo_remolque': task.modelo_remolque if task.modelo_remolque else task.asignar_remolque_id[0].modelo_remolque if task.asignar_remolque_id else False,
            'status_remolque': task.status if task.status else task.asignar_remolque_id[0].status_remolque if task.asignar_remolque_id else False,
            'capacidad_carga': task.capacidad_carga if task.capacidad_carga else task.asignar_remolque_id[0].capacidad_carga if task.asignar_remolque_id else False,
            'cantidad_despachar': task.cantidad_despachar,
            'cliente': task.partner_id.name if task.partner_id else False,
            'pedido_venta': task.sale_order_id.id if task.sale_order_id else False,
            'orden_entrega': task.picking_id.id if task.picking_id else False,
            'asignada': task.user_id.id if task.user_id else False
        })
        return res



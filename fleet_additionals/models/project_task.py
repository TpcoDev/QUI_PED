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

    remolque_id = fields.Many2one('remolque_dia', string='Remolque_dia', ondelete='cascade')

    dia_operacion = fields.Date('Fecha operación', related='remolque_id.dia_operacion')
    chofer_camion = fields.Char('Chofer', related='remolque_id.chofer_camion')
    patente_remolque = fields.Char('Patente Remolque', related='remolque_id.patente_remolque',store=True)
    patente_camion_tracto = fields.Char('Patente Camion Tracto', related='remolque_id.patente_camion_tracto')
    modelo_remolque = fields.Char('Nombre vehículo', related='remolque_id.modelo_remolque')
    # status = fields.Char('Estado')
    status = fields.Selection([
        ('completado', 'Completado'),
        ('mantenimiento', 'Mantenimiento'),
        ('disponible', 'Disponible'),
    ], string='Estado', related='remolque_id.status_trailer_day')
    capacidad_carga = fields.Float('Capacidad carga', digits=(16, 3))


    remolque_ids = fields.Many2many(comodel_name="remolque_dia",string='Remolques')

    #remolque_ids = fields.One2many(comodel_name="remolque_dia",inverse_name="task_id", string='Remolques')

    asignar_remolque_id = fields.One2many(comodel_name="asignar_remolque", inverse_name="task_id",string="Remolque asignado")

    # remolque_ids_show = fields.One2many(comodel_name="remolque_dia",compute='compute_remolques', readonly=False, inverse_name="task_id",
    #                                       string="Remolque asignado")
    mostrar_page = fields.Boolean(compute='_compute_mostrar_page')
    btn_asignar = fields.Boolean()

    def desasignar_remolque(self):
        for task in self:
            task.remolque_id = None
            task.dia_operacion = None
            task.chofer_camion = None
            task.patente_remolque = None
            task.patente_camion_tracto = None
            task.modelo_remolque = None
            task.status = None
            task.capacidad_carga = 0

    @api.onchange('planned_date_begin')
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
            # self.compute_remolques()

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

            if len(task.asignar_remolque_id):
                self.cargar_remolques_asignados()
            if task.planned_date_begin:
                self._onchange_planned_date_begin()
            task.mostrar_page = res

    def cargar_remolques_asignados(self):
        ids = []
        tasks = self.env['project.task']
        remolque = self.env['remolque_dia']

        if self.btn_asignar:
            self.btn_asignar = False
            for tarea in self:
                # if tarea.dia_operacion and tarea.patente_remolque:
                #     tasks = tasks.search([('dia_operacion', '=', tarea.dia_operacion),
                #                           ('patente_remolque', '=', tarea.patente_remolque)])
                #     remolque = remolque.search([('dia_operacion', '=', tarea.dia_operacion),
                #                           ('patente_remolque', '=', tarea.patente_remolque)])
                #     tarea.status = remolque.status_trailer_day
                #         # dict(self.env['remolque_dia'].fields_get(allfields=['status_trailer_day'])
                #         #                                ['status_trailer_day']['selection'])[remolque.status_trailer_day]
                #     for task in tasks:
                #         res = self.crear_remolque_asiganado(task)
                #         ids.append(res.id)
                if tarea.asignar_remolque_id:
                    tasks = tasks.search([('dia_operacion','=',tarea.asignar_remolque_id[0].dia_operacion),('patente_remolque','=',tarea.asignar_remolque_id[0].patente_remolque)])
                    for task in tasks:
                        res = self.crear_remolque_asiganado(task)
                        ids.append(res.id)
                # else:
                #     res = self.crear_remolque_asiganado(tarea)
                #     ids.append(res.id)
                #
                # if not ids:
                #     res = self.crear_remolque_asiganado(tarea)
                #     ids.append(res.id)
        self.asignar_remolque_id = [(6, 0, ids)]

    def crear_remolque_asiganado(self,task):
        remolque_asignado = self.env['asignar_remolque']
        res = remolque_asignado.create({
            'task_ref': task.id,
            'dia_operacion': task.dia_operacion if task.dia_operacion else task.asignar_remolque_id[0].dia_operacion if task.asignar_remolque_id else False,
            'solicitud_despacho': task.name,
            'patente_remolque': task.patente_remolque if task.patente_remolque else task.asignar_remolque_id[0].patente_remolque if task.asignar_remolque_id else False,
            'modelo_remolque': task.modelo_remolque if task.modelo_remolque else task.asignar_remolque_id[0].modelo_remolque if task.asignar_remolque_id else False,
            'status_remolque': task.status if task.status else task.asignar_remolque_id[0].status_remolque if task.asignar_remolque_id else False,
            'capacidad_carga': task.capacidad_carga if task.capacidad_carga !=0 else task.asignar_remolque_id[0].capacidad_carga if task.asignar_remolque_id else 0,
            'cantidad_despachar': task.cantidad_despachar,
            'cliente': task.partner_id.name if task.partner_id else False,
            'pedido_venta': task.sale_order_id.id if task.sale_order_id else False,
            'orden_entrega': task.picking_id.id if task.picking_id else False,
            'asignada': task.user_id.id if task.user_id else False
        })
        return res

    @api.onchange('remolque_ids')
    def _onchange_remolque_ids(self):
        self._onchange_planned_date_begin()
        if self.patente_remolque:
            remolques = self.remolque_ids
            for remolque in remolques:
                if self.patente_remolque == remolque.patente_remolque:
                    self.chofer_camion = remolque.chofer_camion
                    self.patente_camion_tracto = remolque.patente_camion_tracto
                    self.status = remolque.status_trailer_day

                        # dict(self.env['remolque_dia'].fields_get(allfields=['status_trailer_day'])
                        #                            ['status_trailer_day']['selection'])[remolque.status_trailer_day]

    # def compute_remolques(self):
    #     ids = []
    #     if self.remolque_ids:
    #         for remolque in self.remolque_ids:
    #             ids.append(remolque.id)
    #     self.remolque_ids_show = [(6, 0, ids)]


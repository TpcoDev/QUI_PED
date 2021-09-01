from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _, exceptions
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class RemolqueDia(models.Model):
    _name = "remolque_dia"

    name = fields.Char(string='Nombre',default='Nuevo')

    status_trailer_day = fields.Selection([
        ('completado', 'Completado'),
        ('mantenimiento', 'Mantenimiento'),
        ('disponible', 'Disponible'),
        ], string='Estado del remolque', default='disponible')
    dia_operacion = fields.Date('Fecha operación',required=True)
    creador = fields.Many2one('res.users', 'Responsable', default=lambda self: self.env.user, readonly=True)

    patente_remolque = fields.Char('Patente del remolque')
    modelo_remolque = fields.Char('Nombre vehículo',required=True)
    chofer_camion = fields.Char('Chofer')
    rut_chofer_camion = fields.Char('Rut Chofer')
    patente_camion_tracto = fields.Char('Patente Camion Tracto')
    capacidad_carga = fields.Float('Capacidad carga', digits=(16, 3))

    task_id = fields.Many2one(
        comodel_name='project.task',
        string=u'Proyecto',
        ondelete='cascade',
        index=True,
        required=False)

    def action_update_fields(self):
        for remolque in self:
            if remolque.task_id:
                print(remolque.task_id)
                remolque.task_id.dia_operacion = remolque.dia_operacion
                remolque.task_id.patente_remolque = remolque.patente_remolque
                remolque.task_id.modelo_remolque = remolque.modelo_remolque
                remolque.task_id.chofer_camion = remolque.chofer_camion
                remolque.task_id.patente_camion_tracto = remolque.patente_camion_tracto
                remolque.task_id.status = dict(self.env['remolque_dia'].fields_get(allfields=['status_trailer_day'])
                                               ['status_trailer_day']['selection'])[remolque.status_trailer_day]

    def action_asignar_remolque(self):
        ids = []
        remolque_asignado = self.env['asignar_remolque']
        tasks = self.env['project.task']
        for remolque in self:
            if remolque.patente_remolque != remolque.task_id.patente_remolque:
                raise exceptions.ValidationError(
                    u'El remolque que intenta asignar no es el mismo del cual visualizó la información.')
            tasks = tasks.search([('dia_operacion','=',remolque.task_id.dia_operacion),('patente_remolque','=',remolque.task_id.patente_remolque)])

            for task in tasks:
                res=remolque_asignado.create({
                    'dia_operacion': task.dia_operacion,
                    'solicitud_despacho': task.name,
                    'patente_remolque': task.patente_remolque,
                    'modelo_remolque': task.modelo_remolque,
                    'status_remolque': task.status,
                    'capacidad_carga': task.capacidad_carga,
                    'cantidad_despachar': task.cantidad_despachar,
                    'cliente': task.partner_id.id if task.partner_id else False,
                    'pedido_venta': task.sale_order_id.id if task.sale_order_id else False,
                    'orden_entrega':  task.picking_id.id if task.picking_id else False,
                    'asignada':  task.user_id.id if task.user_id else False
                })

        remolque.task_id.asignar_remolque_id = [(6, 0, ids)]


    def name_get(self):
        if self._context is None:
            self._context = {}
        res = []
        for remolque_dia in self:
            fecha = datetime.strptime(str(remolque_dia.dia_operacion),'%Y-%m-%d').strftime("%d/%m/%Y")
            res.append(
                    (remolque_dia.id, ("%(modelo_remolque)s - %(dia_operacion)s") % {
                        'modelo_remolque': remolque_dia.modelo_remolque,
                        'dia_operacion': fecha
                    }))
        return res

    @api.constrains('patente_remolque', 'dia_operacion')
    def _check_validations(self):
        remolque_dia = self.env['remolque_dia']
        for rec in self:
            if len(remolque_dia.search([('patente_remolque','=',rec.patente_remolque),('dia_operacion','=',rec.dia_operacion)])) > 1:
                raise exceptions.ValidationError(
                    u'Ya existe un egistro para este remolque en la fecha seleccionada.')


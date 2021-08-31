from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _, exceptions
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class AsignarRemolque(models.Model):
    _name = "asignar_remolque"

    dia_operacion = fields.Date('Fecha operación')
    solicitud_despacho = fields.Char('Solicitud de despacho')
    patente_remolque = fields.Char('Patente remolque')
    modelo_remolque = fields.Char('Nombre vehículo')
    status_remolque = fields.Char('Estado remolque')
    capacidad_carga = fields.Float('Capacidad carga', digits=(16, 3))
    cantidad_despachar = fields.Float('Cantidad a despachar', digits=(16, 3))
    # cliente = fields.Many2one('res.partner', 'Cliente')
    cliente = fields.Char('Cliente')
    pedido_venta = fields.Many2one('sale.order', 'Pedido de venta')
    orden_entrega = fields.Many2one('stock.picking', 'Orden de entrega')
    asignada = fields.Many2one('res.users', 'Asignada')

    task_id = fields.Many2one(
        comodel_name='project.task',
        string=u'Proyecto',
        ondelete='cascade',
        index=True,
        required=False)



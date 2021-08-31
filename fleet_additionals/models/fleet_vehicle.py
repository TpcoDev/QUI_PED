from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta, date
import logging
import pytz

_logger = logging.getLogger(__name__)


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    capacidad_carga = fields.Float('Capacidad carga', digits=(16, 3))

    @api.model
    def create(self, vals):
        remolque_dia = self.env['remolque_dia']
        vehicle = super(FleetVehicle, self).create(vals)

        today = datetime.today().date()
        end_date = self.suma_annos(today, 2)
        cant_days = (end_date - today).days

        day = 0
        while day <= cant_days:
            fecha = today + timedelta(days=day)

            remolque_dia.create({
                'patente_remolque': vehicle.license_plate,
                'modelo_remolque': vehicle.model_id.name,
                'capacidad_carga':vehicle.capacidad_carga,
                'dia_operacion':fecha
            })

            day+=1

        return vehicle

    def suma_annos(self,fecha,cant_annos):
        try:
            return fecha.replace(year = fecha.year + cant_annos)
        except ValueError:
            return fecha + (date(fecha.year+cant_annos,1,1)-date(fecha.year,1,1))
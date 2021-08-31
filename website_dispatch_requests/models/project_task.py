# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
import pytz

_logger = logging.getLogger(__name__)


class ProjectTask(models.Model):
    _inherit = 'project.task'

    picking_id = fields.Many2one(comodel_name='stock.picking', string=_('Albarán'))
    state_oe = fields.Selection(related='picking_id.state', string=_('Estado de OE'))
    cantidad_reservada = fields.Float(related='picking_id.move_ids_without_package.reserved_availability')
    cantidad_despachar = fields.Float(string='Cantidad a despachar')

    partner_cod_sap = fields.Char(related='partner_id.vat', string='Cod SAP Cliente')
    lc_fecha_hora = fields.Datetime(string=_('Fecha y hora LC'), related='partner_id.lc_fecha_hora')
    lc_disponible = fields.Monetary(
        string=_('LC disponible'), currency_field='company_currency',
        related='partner_id.lc_disponible'
    )
    company_currency = fields.Many2one(
        comodel_name="res.currency", string='Currency', related='company_id.currency_id',
        readonly=True
    )

    planification_hora_date = fields.Datetime(string=_('Fecha y hora Planificación'))
    planification = fields.Selection(
        selection=[('planifica', _('Planifica')), ('no_planifica', _('No Planifica')), ('pendiente', _('Pendiente'))],
        string='Planificación', default='planifica'
    )

    def _prepare_task_value(self, values):
        vals = {}
        if values.get('task_title', False):
            vals.update({'name': values['task_title'], 'is_fsm': True})
        if values.get('dispatch_date', False):
            d, m, Y = values["dispatch_date"].split('/')
            tz = pytz.timezone(self.env.user.tz) if self.env.user.tz else pytz.utc

            planned_date_begin = fields.Datetime.from_string(f'{Y}-{m}-{d} 00:00:00') + relativedelta(hours=4)
            planned_date_end = fields.Datetime.from_string(f'{Y}-{m}-{d} 23:59:00') + relativedelta(hours=4)

            vals.update({
                'planned_date_begin': planned_date_begin,
                'planned_date_end': planned_date_end,
            })
        if values.get('sale_order_id', False):
            user_id = self.env['sale.order'].browse(int(values['sale_order_id'])).user_id
            vals.update({
                'sale_order_id': int(values['sale_order_id']),
                'user_id': user_id.id
            })
        if values.get('line_id', False):
            vals.update({
                'sale_line_id': int(values['line_id']),
            })
        if values.get('cantidad', False):
            vals.update({
                'cantidad_despachar': values['cantidad'],
            })
        if values.get('partner_id', False):
            project_id = self.env['project.project'].search([
                ('is_fsm', '=', True), ('partner_id', '=', int(values['partner_id']))
            ], limit=1)
            vals.update({
                'partner_id': int(values['partner_id']),
                'project_id': project_id.id
            })
        vals.update({'planification': 'pendiente'})
        return vals

    @api.model
    def create_project_task(self, vals):
        _logger.info('==== create a task ==== %r', vals)
        values = self._prepare_task_value(vals)
        task = ''
        try:
            task = self.sudo().with_context({'pass': True}).create(values)
            if task:
                dispatch_qty = task.sale_line_id.product_uom_qty - task.cantidad_despachar
                task.with_context({'dispatch_qty': dispatch_qty}).sale_line_id._action_launch_stock_rule()

                task.write({
                    'picking_id': task.sale_line_id.move_ids[0].picking_id.id,
                    'description': f'{task.sale_order_id.name}-{task.sale_line_id.product_id.name}-{task.sale_line_id.product_uom_qty}-{task.sale_line_id.product_uom.name}-{vals["dispatch_date"]}-{vals["horarios_recepcion"]}'
                })

                return {
                    'title': _('Task Created'),
                    'message': _('Su solicitud de despacho %s ha sido enviada con exito') % (task.name),
                    'task': task
                }
        except Exception as e:
            _logger.info('=======%r', e)
            return {
                'title': _('Tarea creada'),
                'message': _('Su solicitud de despacho %s ha sido enviada con exito') % (vals['task_title'])
            }
            # return {'title': 'Error', 'message': f'{e}'}

    @api.constrains('sale_line_id')
    def _check_sale_line_type(self):
        if self.env.context.get('pass', False):
            return True

        for task in self.sudo():
            if task.sale_line_id:
                if not task.sale_line_id.is_service or task.sale_line_id.is_expense:
                    raise ValidationError(_(
                        'You cannot link the order item %(order_id)s - %(product_id)s to this task because it is a re-invoiced expense.',
                        order_id=task.sale_line_id.order_id.name,
                        product_id=task.sale_line_id.product_id.display_name,
                    ))

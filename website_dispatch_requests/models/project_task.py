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

    planification_hora_date = fields.Datetime(string=_('Fecha y hora Planificación'), default=fields.Datetime.now())
    planification = fields.Selection(
        selection=[('planifica', _('Planifica')), ('no_planifica', _('No Planifica')), ('pendiente', _('Pendiente'))],
        string='Planificación', default='planifica'
    )

    move_ids = fields.Many2many(
        comodel_name='stock.move', string=_('Detalle Ordenes Pendientes')
    )

    def load_moves(self, partner):
        if self.partner_id:
            moves = self.env['stock.move'].search(
                [('partner_codigo_sap', '=', self.partner_id.vat), ('state', 'not in', ('cancel', 'done'))])
            self.move_ids = [(6, 0, moves.ids)]

    @api.model
    def default_get(self, fields):
        res = super(ProjectTask, self).default_get(fields)
        self.load_moves(self.partner_id)
        return res

    @api.onchange('partner_id')
    def _onchange_moves(self):
        self.load_moves(self.partner_id)

    def _prepare_task_value(self, values):
        vals = {}
        # By default get a user to create a stock.picking
        partner = self.env.user.partner_id.id

        if values.get('partner_id', False):
            project_id = self.env['project.project'].search([
                ('is_fsm', '=', True), ('partner_id', '=', int(values['partner_id']))
            ], limit=1)
            vals.update({
                'project_id': project_id.id,
                'partner_id': int(values['partner_id'])
            })

        if values.get('task_title', False):
            vals.update({'name': values['task_title'], 'is_fsm': True})
        if values.get('dispatch_date', False):
            d, m, Y = values["dispatch_date"].split('/')
            tz = pytz.timezone(self.env.user.tz) if self.env.user.tz else pytz.utc
            hours = self.env["ir.config_parameter"].sudo().get_param("horas_diferencias")
            planned_date_begin = fields.Datetime.from_string(f'{Y}-{m}-{d} 00:00:00') + relativedelta(hours=int(hours))
            planned_date_end = fields.Datetime.from_string(f'{Y}-{m}-{d} 23:59:00') + relativedelta(hours=int(hours))

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

        vals.update({'planification': 'pendiente'})
        return vals

    @api.returns('mail.message', lambda value: value.id)
    def message_chatter(self, **kwargs):
        return super(ProjectTask, self).message_post(**kwargs)

    @api.onchange('planification')
    def _onchange_planification(self):
        self.ensure_one()
        if self.planification == 'planifica':
            self.planification_hora_date = fields.Datetime.now()
            display_msg = (
                f"LC Disponible {self.lc_disponible} \n"
                f"Planificacion {self.planification} \n"
                f"Fecha y hora Planificacion {self.planification_hora_date} \n"
                f"Fecha y hora LC {self.lc_fecha_hora} \n"
            )

            task = self.env['project.task'].search([('id', 'in', self.ids)], limit=1)
            if task:
                task.message_chatter(
                    subject="Pendiente -> Planifica",
                    body=display_msg
                )

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

                wrtVals = {
                    'description': f'{task.sale_order_id.name}-{task.sale_line_id.product_id.name}-{task.cantidad_despachar}-{task.sale_line_id.product_uom.name}-{vals["dispatch_date"]}-{vals["horarios_recepcion"]}'
                }

                if len(task.sale_line_id.move_ids):
                    wrtVals.update({'picking_id': task.sale_line_id.move_ids[-1].picking_id.id})

                    if vals.get('delivery_ids', False) and vals['delivery_ids']:
                        partner = int(vals['delivery_ids'])
                        task.sale_line_id.move_ids[-1].picking_id.write({'partner_id': partner})

                task.write(wrtVals)

                return {
                    'title': _('Task Created'),
                    'message': _('Su solicitud de despacho %s ha sido enviada con exito') % (task.name),
                    'task': task
                }
        except Exception as e:
            _logger.info('=======%r', e)
            return {
                'title': _('Tarea no creada'),
                'message': _('Su solicitud de despacho %s no ha sido enviada con exito') % (vals['task_title'])
            }
            # return {'title': 'Error', 'message': f'{e}'}

    @api.constrains('sale_line_id')
    def _check_sale_line_type(self):
        # if self.env.context.get('pass', False):
        #     return True
        #
        # for task in self.sudo():
        #     if task.sale_line_id:
        #         if not task.sale_line_id.is_service or task.sale_line_id.is_expense:
        #             raise ValidationError(_(
        #                 'You cannot link the order item %(order_id)s - %(product_id)s to this task because it is a re-invoiced expense.',
        #                 order_id=task.sale_line_id.order_id.name,
        #                 product_id=task.sale_line_id.product_id.display_name,
        #             ))
        return True
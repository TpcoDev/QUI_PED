from odoo import fields, models, api, exceptions


class ReportProjectTaskCargo(models.AbstractModel):
    _name = 'report.fleet_additionals.report_project_task_cargo'
    _description = 'Project task cargo report with planned planning'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['project.task'].browse(docids)
        ids_to_print = []

        for task in docs:
            if task.planification == 'planifica' and task.patente_remolque and task.status == 'completado':
                ids_to_print.append(task.id)
        docs = self.env['project.task'].browse(ids_to_print)

        if len(ids_to_print) > 0:
            return {
                'doc_ids': ids_to_print,
                'doc_model': 'project.task',
                'docs': docs,

            }
        else:
            raise exceptions.ValidationError(u'No existen datos para mostrar.')

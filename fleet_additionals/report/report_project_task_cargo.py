from odoo import fields, models, api


class ReportProjectTaskCargo(models.AbstractModel):
    _name = 'report.fleet_additionals.report_project_task_cargo'
    _description = 'Project task cargo report with planned planning'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['project.task'].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': 'project.task',
            'docs': docs,

        }

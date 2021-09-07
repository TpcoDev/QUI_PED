from odoo import fields, models, api, exceptions
from collections import Counter
from collections import defaultdict


class ReportProjectTaskCargo(models.AbstractModel):
    _name = 'report.fleet_additionals.report_project_task_cargo'
    _description = 'Project task cargo report with planned planning'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['project.task'].browse(docids)
        ids_to_print = []
        remolques = []
        pages = []
        primera_tabla = []
        segunda_tabla = []
        tercera_tabla = []
        cuarta_tabla = []
        res = []
        for task in docs:
            if task.planification == 'planifica' and task.patente_remolque and task.status == 'completado':
                ids_to_print.append(task.id)
                remolques.append(task.patente_remolque)
        docs = self.env['project.task'].browse(ids_to_print)

        ubicaciones = defaultdict(list)
        for index in range(len(remolques)):
            ubicaciones[remolques[index]].append(index)

        cant_pages = 0
        for element in ubicaciones.items():
            pages.append(cant_pages)
            primera_tabla.append(
                (docs[element[1][0]].dia_operacion, docs[element[1][0]].chofer_camion, docs[element[1][0]].remolque_id.rut_chofer_camion,
                 docs[element[1][0]].patente_camion_tracto, docs[element[1][0]].patente_remolque,cant_pages))
            for pos in element[1]:
                # sale_order_line = []
                # contactos = []
                for sale_order in docs[pos].sale_order_id.order_line:
                    segunda_tabla.append((sale_order.product_id.default_code, sale_order.product_id.name, docs[pos].cantidad_despachar,
                                              sale_order.product_id.uom_id.name, docs[pos].partner_id.display_name,
                                              docs[pos].sale_order_id.client_order_ref,cant_pages))
                    tercera_tabla.append((sale_order.product_id.default_code,cant_pages))
                # segunda_tabla.append(sale_order_line)
                for contact in docs[pos].partner_id.child_ids:
                    if contact.mobile:
                        name = contact.name + ' '+ contact.mobile
                    else:
                        name = contact.name
                    cuarta_tabla.append((name,cant_pages))
            cant_pages += 1

        res.append(pages)
        res.append(primera_tabla)
        res.append(segunda_tabla)
        res.append(tercera_tabla)
        res.append(cuarta_tabla)

        if len(ubicaciones.items()) > 0:
            return {
                'doc_ids': ids_to_print,
                'doc_model': 'project.task',
                'docs': res,

            }
        else:
            raise exceptions.ValidationError(u'No existen datos para mostrar.')

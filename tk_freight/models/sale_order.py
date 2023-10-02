
from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        if self.freight_id:
            res['freight_operation_id'] = self.freight_id.id
        return res

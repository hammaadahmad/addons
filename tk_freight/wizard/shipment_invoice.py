from odoo import fields, api, models


class ShipmentInvoice(models.TransientModel):
    _name = "shipment.invoice"
    _description = "Shipment Invoice to Shipper or Consignee"

    invoice_to = fields.Selection([('shipper', 'Shipper'), ('consignee', 'Consignee')], string="Invoice To")
    shipment_id = fields.Many2one('freight.shipment', string="Shipment")

    def action_create_invoice(self):
        for rec in self:
            sale_order = True
            for record in rec.shipment_id.freight_services:
                if record.service_type == 'customer':
                    if not record.sale_order_id:
                        sale_order = False
            if not sale_order:
                if rec.invoice_to == "consignee":
                    if rec.shipment_id.total_service_charge > 0:
                        invoice_lines = []
                        for service in rec.shipment_id.freight_services:
                            if not service.sale_order_id:
                                if service.service_type == 'customer':
                                    service.status = 'quotation'
                                    record = {
                                        'product_id': service.service_id.id,
                                        'name': service.name,
                                        'product_uom_qty': service.qty,
                                        'price_unit': service.sale,
                                    }
                                    invoice_lines.append((0, 0, record))
                        data = {
                            'partner_id': rec.shipment_id.consignee_id.id,
                            'order_line': invoice_lines,
                            'freight_id': rec.shipment_id.id
                        }
                        sale_order_id = self.env['sale.order'].create(data)
                        for service in rec.shipment_id.freight_services:
                            if service.service_type == 'customer':
                                if not service.sale_order_id:
                                    service.sale_order_id = sale_order_id.id

                        return {
                            'type': 'ir.actions.act_window',
                            'name': 'Sale Order',
                            'res_model': 'sale.order',
                            'res_id': sale_order_id.id,
                            'view_mode': 'form',
                            'target': 'current'
                        }
                    else:
                        message = {
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'type': 'danger',
                                'title': ('Add Services !'),
                                'message': "Service Charge cannot be Zero",
                                'sticky': False,
                            }
                        }
                        return message
                elif rec.invoice_to == "shipper":
                    if rec.shipment_id.total_service_charge > 0:
                        invoice_lines = []
                        for service in rec.shipment_id.freight_services:
                            if not service.sale_order_id:
                                if service.service_type == 'customer':
                                    service.status = 'quotation'
                                    record = {
                                        'product_id': service.service_id.id,
                                        'name': service.name,
                                        'product_uom_qty': service.qty,
                                        'price_unit': service.sale,
                                    }
                                    invoice_lines.append((0, 0, record))
                        data = {
                            'partner_id': rec.shipment_id.shipper_id.id,
                            'order_line': invoice_lines,
                            'freight_id': rec.shipment_id.id
                        }
                        sale_order_id = self.env['sale.order'].create(data)
                        for service in rec.shipment_id.freight_services:
                            if service.service_type == 'customer':
                                if not service.sale_order_id:
                                    service.sale_order_id = sale_order_id.id
                        return {
                            'type': 'ir.actions.act_window',
                            'name': 'Sale Order',
                            'res_model': 'sale.order',
                            'res_id': sale_order_id.id,
                            'view_mode': 'form',
                            'target': 'current'
                        }
                    else:
                        message = {
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'type': 'danger',
                                'title': ('Add Services !'),
                                'message': "Service Charge cannot be Zero",
                                'sticky': False,
                            }
                        }
                        return message
            else:
                message = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'type': 'info',
                        'title': ('No New Service Add for Shipper / Consignee'),
                        'sticky': False,
                    }
                }
                return message

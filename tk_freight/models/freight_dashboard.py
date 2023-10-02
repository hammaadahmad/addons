# -*- coding: utf-8 -*-
# Copyright 2020 - Today Techkhedut.
# Part of Techkhedut. See LICENSE file for full copyright and licensing details.
import datetime
from odoo import models, fields, api
from datetime import timedelta, datetime


class DashboardDetails(models.Model):
    _name = 'dashboard.details'
    _description = 'Freight Dashboard'

    name = fields.Char("")

    @api.model
    def get_freight_info(self):
        fright_shipment = self.env['freight.shipment'].sudo()
        direct_count = fright_shipment.search_count(
            [('operation', '=', 'direct')])
        house_count = fright_shipment.search_count(
            [('operation', '=', 'house')])
        master_count = fright_shipment.search_count(
            [('operation', '=', 'master')])
        pending_booking = self.env['shipment.freight.booking'].search_count(
            [('state', '=', 'draft')])
        total_port = self.env['freight.port'].search_count([])
        total_packages = self.env['freight.package'].search_count([])
        air = fright_shipment.search_count([('transport', '=', 'air')])
        ocean = fright_shipment.search_count([('transport', '=', 'ocean')])
        land = fright_shipment.search_count([('transport', '=', 'land')])
        import_count = fright_shipment.search_count(
            [('direction', '=', 'import')])
        export_count = fright_shipment.search_count(
            [('direction', '=', 'export')])
        freight_direction = [['Import', 'Export'],
                             [import_count, export_count]]
        data = {
            'direct_count': direct_count,
            'house_count': house_count,
            'master_count': master_count,
            'pending_booking': pending_booking,
            'total_port': total_port,
            'total_packages': total_packages,
            'transport': [['Air Shipment', 'Ocean Shipment', 'Land Shipment'], [air, ocean, land]],
            'fright_operation': [[direct_count, house_count, master_count],
                                 ['Direct Shipment', 'House Shipment', 'Master Shipment']],
            'top_consign': self.get_top_consignee(),
            'move_type': self.get_move_type(),
            'freight_direction': freight_direction,
            'get_shipment_month': [self.get_shipment_month(), self.get_air_shipment_month(),
                                   self.get_land_shipment_month(), self.get_ocean_shipment_month()],
            'top_shipper': self.get_top_shipper(),
            'get_bill_invoice': [self.get_shipment_month(), self.get_freight_bills(), self.get_freight_invoice()],
        }

        stages, shipment_counts = [], []
        stage_ids = self.env['freight.shipment.stages'].search(
            [], order='sequence asc')
        if not stage_ids:
            data['shipment_stages'] = [[], []]
        for stg in stage_ids:
            shipment_data = fright_shipment.search_count(
                [('stage_id', '=', stg.id)])
            shipment_counts.append(shipment_data)
            stages.append(stg.name)

        data['shipment_stages'] = [stages, shipment_counts]

        return data

    def get_top_consignee(self):
        partner, amount, data = [], [], []
        consignee = self.env['res.partner'].search(
            [('consignee', '=', True)]).mapped('id')
        for group in self.env['account.move'].read_group([('partner_id', 'in', consignee)],
                                                         ['amount_total',
                                                             'partner_id'],
                                                         ['partner_id'],
                                                         orderby="amount_total DESC", limit=5):
            if group['partner_id']:
                name = self.env['res.partner'].sudo().browse(
                    int(group['partner_id'][0])).name
                partner.append(name)
                amount.append(group['amount_total'])

        data = [partner, amount]
        return data

    def get_move_type(self):
        move_type, counts, data = [], [], []
        move_types = self.env['freight.move.type'].search([])
        if not move_types:
            move_type, counts = [], []
        for type in move_types:
            rec = self.env['freight.shipment'].search_count(
                [('move_type', '=', type.id)])
            counts.append(rec)
            move_type.append(type.name)
        data = [move_type, counts]
        return data

    def get_shipment_month(self):
        data_dict = {'January': 0,
                     'February': 0,
                     'March': 0,
                     'April': 0,
                     'May': 0,
                     'June': 0,
                     'July': 0,
                     'August': 0,
                     'September': 0,
                     'October': 0,
                     'November': 0,
                     'December': 0,
                     }
        return list(data_dict.keys())

    def get_air_shipment_month(self):
        year = fields.date.today().year
        data_dict = {'January': 0,
                     'February': 0,
                     'March': 0,
                     'April': 0,
                     'May': 0,
                     'June': 0,
                     'July': 0,
                     'August': 0,
                     'September': 0,
                     'October': 0,
                     'November': 0,
                     'December': 0,
                     }
        shipment = self.env['freight.shipment'].search([])
        for data in shipment:
            if data.create_datetime.year == year:
                if data.transport == 'air':
                    data_dict[data.create_datetime.strftime(
                        "%B")] = data_dict[data.create_datetime.strftime("%B")] + 1
        return list(data_dict.values())

    def get_ocean_shipment_month(self):
        year = fields.date.today().year
        data_dict = {'January': 0,
                     'February': 0,
                     'March': 0,
                     'April': 0,
                     'May': 0,
                     'June': 0,
                     'July': 0,
                     'August': 0,
                     'September': 0,
                     'October': 0,
                     'November': 0,
                     'December': 0,
                     }
        shipment = self.env['freight.shipment'].search([])
        for data in shipment:
            if data.create_datetime.year == year:
                if data.transport == 'ocean':
                    data_dict[data.create_datetime.strftime(
                        "%B")] = data_dict[data.create_datetime.strftime("%B")] + 1
        return list(data_dict.values())

    def get_land_shipment_month(self):
        year = fields.date.today().year
        data_dict = {'January': 0,
                     'February': 0,
                     'March': 0,
                     'April': 0,
                     'May': 0,
                     'June': 0,
                     'July': 0,
                     'August': 0,
                     'September': 0,
                     'October': 0,
                     'November': 0,
                     'December': 0,
                     }
        shipment = self.env['freight.shipment'].search([])
        for data in shipment:
            if data.create_datetime.year == year:
                if data.transport == 'land':
                    data_dict[data.create_datetime.strftime(
                        "%B")] = data_dict[data.create_datetime.strftime("%B")] + 1
        return list(data_dict.values())

    def get_top_shipper(self):
        shipper = {}
        for group in self.env['freight.shipment'].read_group([], ['shipper_id'],
                                                             ['shipper_id'], limit=10):
            if group['shipper_id']:
                name = self.env['res.partner'].sudo().browse(
                    int(group['shipper_id'][0])).name
                shipper[name] = group['shipper_id_count']

        shipper = dict(
            sorted(shipper.items(), key=lambda x: x[1], reverse=True))
        return [list(shipper.keys()), list(shipper.values())]

    def get_freight_bills(self):
        year = fields.date.today().year
        bill_dict = {'January': 0,
                     'February': 0,
                     'March': 0,
                     'April': 0,
                     'May': 0,
                     'June': 0,
                     'July': 0,
                     'August': 0,
                     'September': 0,
                     'October': 0,
                     'November': 0,
                     'December': 0,
                     }
        bill = self.env['account.move'].search([])
        for data in bill:
            if data.invoice_date:
                if data.invoice_date.year == year and data.move_type == 'in_invoice' and data.freight_operation_id:
                    bill_dict[data.invoice_date.strftime("%B")] = bill_dict[data.invoice_date.strftime(
                        "%B")] + data.amount_total
        return list(bill_dict.values())

    def get_freight_invoice(self):
        year = fields.date.today().year
        invoice_dict = {'January': 0,
                        'February': 0,
                        'March': 0,
                        'April': 0,
                        'May': 0,
                        'June': 0,
                        'July': 0,
                        'August': 0,
                        'September': 0,
                        'October': 0,
                        'November': 0,
                        'December': 0,
                        }
        bill = self.env['account.move'].search([])
        for data in bill:
            if data.invoice_date:
                if data.invoice_date.year == year and data.move_type == 'out_invoice' and data.freight_operation_id:
                    invoice_dict[data.invoice_date.strftime("%B")] = invoice_dict[data.invoice_date.strftime(
                        "%B")] + data.amount_total

        return list(invoice_dict.values())

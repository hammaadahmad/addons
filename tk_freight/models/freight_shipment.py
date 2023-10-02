# -*- coding: utf-8 -*-
# Copyright 2020 - Today Techkhedut.
# Part of Techkhedut. See LICENSE file for full copyright and licensing details.
import logging
from odoo import api, fields, models, _
from random import choice
from string import digits
import json
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class FreightShipment(models.Model):
    _name = 'freight.shipment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Freight Shipment'

    def _get_default_stage_id(self):
        return self.env['freight.shipment.stages'].search([], order='sequence', limit=1)

    def _default_random_barcode(self):
        return "".join(choice(digits) for i in range(8))

    barcode = fields.Char(string="Barcode", help="ID used for shipment identification.",
                          default=_default_random_barcode, copy=False)
    color = fields.Integer('Color')
    stage_id = fields.Many2one('freight.shipment.stages', 'Stage', default=_get_default_stage_id,
                               group_expand='_read_group_stage_ids')
    create_datetime = fields.Datetime(string='Create Date', default=fields.Datetime.now())
    name = fields.Char(string='Name', copy=False, default=lambda self: ('New'))
    direction = fields.Selection(([('import', 'Import'), ('export', 'Export')]), string='Direction')
    transport = fields.Selection(([('air', 'Air'), ('ocean', 'Ocean'), ('land', 'Land')]), string='Transport Via')
    operation = fields.Selection(
        [('direct', 'Direct Shipment'), ('house', 'House Shipment'), ('master', 'Master Shipment')], string='Operation')
    ocean_shipment_type = fields.Selection(([('fcl', 'Full Container(FCL)'), ('lcl', 'Less Container(LCL)')]),
                                           string='Ocean Shipment Type')
    inland_shipment_type = fields.Selection(([('ftl', 'Full Truckload(FTL)'), ('ltl', 'Less than Truckload(LTL)')]),
                                            string='Land Shipment Type')
    address_to = fields.Selection(
        [('sc_address', 'Contact Address'), ('location_address', 'Location Address')], string="Address",
        default="sc_address")
    operator_id = fields.Many2one(
        'res.users', default=lambda self: self.env.user, string='Responsible', required=True)

    dangerous_goods = fields.Boolean('Dangerous Goods')
    dangerous_goods_notes = fields.Text('Dangerous Goods Info')
    move_type = fields.Many2one('freight.move.type', 'Move Type')
    tracking_number = fields.Char('Tracking Number')
    incoterm = fields.Many2one('freight.incoterms', 'Incoterm')
    parent_id = fields.Many2one('freight.shipment', 'Parent')
    booking_id = fields.Many2one('shipment.freight.booking')
    all_shipment = fields.Boolean(string='All Shipment')
    pass_state = fields.Boolean(string='Pass state', compute="_compute_custom_check")
    term_condition = fields.Text(string='Term & Condition')
    shipment_add = fields.Boolean()
    route_add = fields.Boolean()
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    total_service_charge = fields.Monetary(string="Total Customer Service", store=True,
                                           compute="_compute_service_charges")
    total_vendor_service_charge = fields.Monetary(string="Total Vendor Service", store=True,
                                                  compute="_compute_service_charges")
    total_route_charge = fields.Monetary(string="Total Route Charges", store=True, compute="_compute_route_charges")
    frequent_location_id = fields.Many2one('freight.frequent.route', string='Frequent Route')

    # One2many
    freight_orders = fields.One2many('shipment.order', 'shipment_id')
    freight_packages = fields.One2many('shipment.package.line', 'shipment_id')
    freight_services = fields.One2many('freight.service', 'shipment_id')
    freight_routes = fields.One2many('freight.route', 'shipment_id')
    freight_log = fields.One2many('shipment.tracking', 'shipment_id')
    shipments_ids = fields.One2many('freight.shipment', 'parent_id')
    sale_orders = fields.One2many('sale.order', 'freight_id')
    document_ids = fields.One2many('freight.documents', 'freight_id', string='Documents')
    custom_ids = fields.One2many('custom.department', 'freight_id', string='Custom')

    # Count
    service_count = fields.Integer('Services Count', compute='_compute_invoice')
    invoice_count = fields.Integer('Invoice Count', compute='_compute_invoice')
    service_quote_count = fields.Integer('Quote Count', compute='_compute_invoice')
    service_booking_count = fields.Integer('Booking Count', compute='_compute_invoice')
    document_count = fields.Integer(string='Documents Count', compute='_compute_document_count')

    # Shipper
    shipper_id = fields.Many2one('res.partner', 'Shipper', domain=[('shipper', '=', True)])
    shipper_email = fields.Char(related='shipper_id.email', string="Email ")
    shipper_phone = fields.Char(related='shipper_id.phone', string="Phone ")

    # Consignee
    consignee_id = fields.Many2one('res.partner', 'Consignee', domain=[('consignee', '=', True)])
    consignee_email = fields.Char(related='consignee_id.email')
    consignee_phone = fields.Char(related='consignee_id.phone')

    # Datetime / Common Field / Carriage Details
    pickup_datetime = fields.Datetime('Estimate Pickup Time')
    arrival_datetime = fields.Datetime('Estimate Arrival Time')
    distance = fields.Integer(string='Distance')
    contact_place_of_receipt = fields.Selection([('Shipper', 'Shipper'), ('Consignee', 'Consignee')],
                                                string="Place of Receipt", default="Consignee")
    contact_place_of_delivery = fields.Selection([('Shipper', 'Shipper'), ('Consignee', 'Consignee')],
                                                 string="Place of Delivery", default="Consignee")
    location_place_of_receipt = fields.Many2one('freight.port', string="Place of Receipt ")
    location_place_of_delivery = fields.Many2one('freight.port', string="Place of Delivery ")
    freight_collect_prepaid = fields.Selection([('Collect', 'Collect'), ('Prepaid', 'Prepaid')], string="Bill",
                                               default="Collect")
    final_charges = fields.Monetary(string='Total Charges', store=True, compute="_compute_final_charges")
    notes = fields.Text('Notes')
    bl_number = fields.Char(string="B/L")
    special_instruction = fields.Text(string="Special Instruction")

    # Air
    mawb_no = fields.Char('MAWB No')
    flight_no = fields.Char('Flight No')
    airline_owner_id = fields.Many2one('res.partner', string="Airline Owner")
    airline_id = fields.Many2one('freight.airline', 'Airline', domain="[('owner_id','=',airline_owner_id)]")

    # Ocean
    ship_owner_id = fields.Many2one('res.partner', string="Shipping Line")
    obl = fields.Char('OBL No.', help='Original Bill Of Landing')
    voyage_no = fields.Char('Voyage No')
    vessel_id = fields.Many2one('freight.vessel', 'Vessel', domain="[('owner_id','=',ship_owner_id)]")
    transhipment_port = fields.Many2one('freight.port', string="Transhipment Port")

    # Land
    truck_owner_id = fields.Many2one('res.partner', string="Owner")
    truck_ref = fields.Char('CMR/RWB')
    trucker = fields.Many2one('fleet.vehicle', 'Vehicle',
                              domain="[('is_freight_shipment','=',True),('owner_id','=',truck_owner_id)]")
    trucker_number = fields.Char('Reference')

    # Agent
    agent_id = fields.Many2one('res.partner', 'S/I Agent', domain=[('agent', '=', True)])
    bl_document_type = fields.Selection(
        [('Draft', 'DRAFT'), ('Copy', 'COPY NON NEGOTIABLE '), ('original', 'ORIGINAL')], string="B/L Document Type")
    freight_payable = fields.Char(string="Freight Payable At")
    no_bill = fields.Selection([('zero', '(0) ZERO'), ('three', '(3) THREE'), ('surrender', 'SURRENDER')])
    freight_amount = fields.Monetary(string="Freight Amount")
    si_issue_date = fields.Date(string="S/I Issue Date")

    # Source Address
    source_location_id = fields.Many2one('freight.port', 'Source Location', index=True)
    s_zip = fields.Char()
    s_street = fields.Char()
    s_street2 = fields.Char()
    s_city = fields.Char()
    s_country_id = fields.Many2one('res.country')
    s_state_id = fields.Many2one('res.country.state')

    # Destinations Address
    destination_location_id = fields.Many2one('freight.port', 'Destination Location', index=True)
    d_zip = fields.Char()
    d_street = fields.Char()
    d_street2 = fields.Char()
    d_city = fields.Char()
    d_country_id = fields.Many2one('res.country')
    d_state_id = fields.Many2one('res.country.state')

    # Accountancy
    vendor_bill_count = fields.Integer('Vendor Bill Count', compute='_compute_invoice')
    total_invoiced = fields.Float('Total Invoiced(Receivables', compute='_compute_total_amount')
    total_bills = fields.Float('Total Bills(Payable)', compute='_compute_total_amount')
    margin = fields.Float("Margin", compute='_compute_total_amount')
    invoice_residual = fields.Float('Invoice Residual', compute='_compute_total_amount')
    bills_residual = fields.Float('Bills Residual', compute='_compute_total_amount')
    invoice_paid_amount = fields.Float('Invoice', compute='_compute_total_amount')
    bills_paid_amount = fields.Float('Bills', compute='_compute_total_amount')
    actual_margin = fields.Float('Actual Margin', compute='_compute_total_amount')

    # Insurance
    is_freight_insurance = fields.Boolean(string='Is Freight Insurance')
    policy_no = fields.Char(string='Policy No.')
    policy_company_id = fields.Many2one('res.partner',
                                        domain=[('company_type', '=', 'company'), ('is_policy', '=', True)])
    date = fields.Date(string='Issue Date')
    issue_by = fields.Char(string='Issued By')
    policy_name = fields.Char(string='Policy Name')
    policy_holder_id = fields.Many2one(related="consignee_id", string="Policy Holder")
    total_charge = fields.Monetary(string='Total Charge')
    term = fields.Html(string='Insurance Terms')
    risk_ids = fields.Many2many('policy.risk', string='Risk Covered')
    policy_added = fields.Boolean(string='Policy Added')

    # Mask And Numbers
    mask_numbers = fields.Text(string="Mask and Numbers")
    desc_pkg = fields.Text(string="Description and Packages & Goods Particulars Furnished by Shipper")

    # Total Net, Gross and Volume
    package_total_gross = fields.Float(compute="_compute_total_gross_net_volume")
    package_total_net = fields.Float(compute="_compute_total_gross_net_volume")
    package_total_volume = fields.Float(compute="_compute_total_gross_net_volume")

    # Freight Package
    vendor_id = fields.Many2one('res.partner', domain="[('shipper','=',False),('consignee','=',False)]")
    vendor = fields.Selection([('single', 'Single Vendor'), ('multiple', 'Multiple Vendor')], string='Vendor ',
                              default="single")

    # Constrains
    @api.constrains('source_location_id', 'destination_location_id', 'address_to')
    def _check_source_destination_location(self):
        for record in self:
            if record.address_to == "location_address":
                if record.source_location_id.id == record.destination_location_id.id:
                    raise ValidationError("Source and Destination Location are not Same !")

    @api.constrains('shipper_id', 'consignee_id')
    def _check_shipper_consignee(self):
        for record in self:
            if record.shipper_id.id == record.consignee_id.id:
                raise ValidationError("Shipper and Consignee are not Same !")

    # Accountancy
    @api.depends('freight_services')
    def _compute_total_amount(self):
        for order in self:
            invoices = self.env['account.move'].sudo().search(
                [('freight_operation_id', '=', order.id), ('move_type', '=', 'out_invoice'), ('state', '=', 'posted')])
            invoice_amount = 0.0
            bill_amount = 0.0
            invoice_residual = 0.0
            bills_residual = 0.0
            invoice_paid_amount = 0.0
            bills_paid_amount = 0.0
            for invoice in invoices:
                invoice_amount += invoice.amount_total
                invoice_residual += invoice.amount_residual
                reconciled_payments_widget_vals = invoice.invoice_payments_widget
                if reconciled_payments_widget_vals:
                    paid_amount_dict = {vals['move_id']: vals['amount'] for vals in
                                        reconciled_payments_widget_vals['content']}
                else:
                    paid_amount_dict = 0.0
                invoice_paid_amount += sum(list(paid_amount_dict.values())) if type(paid_amount_dict) == dict else 0.0

            bills = self.env['account.move'].sudo().search(
                [('freight_operation_id', '=', order.id), ('move_type', '=', 'in_invoice'), ('state', '=', 'posted')])
            for bill in bills:
                bill_amount += bill.amount_total
                bills_residual += bill.amount_residual
                reconciled_payments_widget_vals_bill = bill.invoice_payments_widget
                if reconciled_payments_widget_vals_bill:
                    paid_bill_amount_dict = {vals['move_id']: vals['amount'] for vals in
                                             reconciled_payments_widget_vals_bill['content']}
                else:
                    paid_bill_amount_dict = 0.0
                bills_paid_amount += sum(list(paid_bill_amount_dict.values())) if type(
                    paid_bill_amount_dict) == dict else 0.0

            order.total_invoiced = invoice_amount
            order.invoice_residual = invoice_residual
            order.invoice_paid_amount = invoice_paid_amount
            order.total_bills = bill_amount
            order.bills_residual = bills_residual
            order.bills_paid_amount = bills_paid_amount
            order.actual_margin = invoice_paid_amount - bills_paid_amount
            order.margin = invoice_amount - bill_amount

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        stage_ids = self.env['freight.shipment.stages'].search([])
        return stage_ids

    @api.depends('freight_services')
    def _compute_invoice(self):
        for order in self:
            order.service_count = len(order.freight_services)
            order.service_quote_count = len(order.sale_orders)
            order.invoice_count = self.env['account.move'].sudo().search_count(
                [('freight_operation_id', '=', order.id), ('move_type', '=', 'out_invoice')])
            order.vendor_bill_count = self.env['account.move'].sudo().search_count(
                [('freight_operation_id', '=', order.id), ('move_type', '=', 'in_invoice')])
            order.service_booking_count = 1 if self.booking_id else 0

    @api.depends('freight_packages')
    def _compute_total_gross_net_volume(self):
        for rec in self:
            net = 0.0
            gross = 0.0
            volume = 0.0
            if rec.freight_packages:
                for data in rec.freight_packages:
                    net = net + data.net_weight
                    gross = gross + data.gross_weight
                    volume = volume + data.volume
            rec.package_total_volume = volume
            rec.package_total_net = net
            rec.package_total_gross = gross

    def button_services(self):
        services = self.mapped('freight_services')
        action = self.env["ir.actions.actions"]._for_xml_id("tk_freight.freight_service_action")
        action['context'] = {'default_shipment_id': self.id}
        action['domain'] = [('id', 'in', services.ids)]
        return action

    @api.onchange('total_service_charge')
    def _onchange_freight_amount(self):
        self.freight_amount = self.total_service_charge

    def button_services_quotes(self):
        action = {'name': _('Sales Order(s)'),
                  'type': 'ir.actions.act_window',
                  'res_model': 'sale.order',
                  'target': 'current',
                  'context': {'default_freight_id': self.id}}
        sale_order_ids = self.sale_orders.ids
        if len(sale_order_ids) == 1:
            action['res_id'] = sale_order_ids[0]
            action['view_mode'] = 'form'
        else:
            action['view_mode'] = 'tree,form'
            action['domain'] = [('id', 'in', sale_order_ids)]
        return action

    def button_services_bookings(self):
        action = {'name': _('Booking'),
                  'type': 'ir.actions.act_window',
                  'res_model': 'shipment.freight.booking',
                  'target': 'current',
                  'domain': [('id', '=', self.booking_id.id)]}
        booking_id = self.booking_id.id
        action['res_id'] = booking_id
        action['view_mode'] = 'form'
        return action

    def button_customer_invoices(self):
        invoices = self.env['account.move'].sudo().search(
            [('freight_operation_id', '=', self.id), ('move_type', '=', 'out_invoice')])
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        action['context'] = {'default_freight_operation_id': self.id, 'default_move_type': 'out_invoice', }
        if len(invoices) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.id
        else:
            action['domain'] = [('id', 'in', invoices.ids)]
        return action

    def button_vendor_bills(self):
        invoices = self.env['account.move'].sudo().search(
            [('freight_operation_id', '=', self.id), ('move_type', '=', 'in_invoice')])
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_in_invoice_type")
        action['context'] = {'default_freight_operation_id': self.id, 'default_move_type': 'in_invoice', }
        if len(invoices) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.id
        else:
            action['domain'] = [('id', 'in', invoices.ids)]
        return action

    @api.model
    def create(self, values):
        if values.get('name', ('New')) == ('New'):
            if values.get('operation') == 'master':
                values['name'] = self.env['ir.sequence'].next_by_code('operation.master') or _('New')
            elif values.get('operation') == 'house':
                values['name'] = self.env['ir.sequence'].next_by_code('operation.house') or _('New')
            elif values.get('operation') == 'direct':
                values['name'] = self.env['ir.sequence'].next_by_code('operation.direct') or _('New')
        if values.get('name', False) and not values.get('tracking_number', False):
            values['tracking_number'] = values.get('name', False)
        id_data = super(FreightShipment, self).create(values).id
        id = self.env['freight.shipment'].browse(id_data)
        if id.transport == 'air':
            route_id = self.env['freight.route'].create({'source_location_id': id.source_location_id.id,
                                                         'destination_location_id': id.destination_location_id.id,
                                                         'main_carriage': True,
                                                         'transport': id.transport,
                                                         'mawb_no': id.mawb_no,
                                                         'airline_id': id.airline_id.id,
                                                         'flight_no': id.flight_no,
                                                         'shipment_id': id.id,
                                                         'pickup_datetime': id.pickup_datetime,
                                                         'arrival_datetime': id.arrival_datetime,
                                                         'address_to': id.address_to,
                                                         'shipper_id': id.shipper_id.id,
                                                         'consignee_id': id.consignee_id.id,
                                                         'charge_type': 'f',
                                                         'inland_shipment_type': id.inland_shipment_type,
                                                         'ocean_shipment_type': id.ocean_shipment_type
                                                         })
            if route_id:
                route_id._onchange_address()
        if id.transport == 'ocean':
            route_id = self.env['freight.route'].create({'source_location_id': id.source_location_id.id,
                                                         'destination_location_id': id.destination_location_id.id,
                                                         'main_carriage': True,
                                                         'transport': id.transport,
                                                         'vessel_id': id.vessel_id.id,
                                                         'obl': id.obl,
                                                         'shipment_id': id.id,
                                                         'pickup_datetime': id.pickup_datetime,
                                                         'arrival_datetime': id.arrival_datetime,
                                                         'address_to': id.address_to,
                                                         'shipper_id': id.shipper_id.id,
                                                         'consignee_id': id.consignee_id.id,
                                                         'charge_type': 'f',
                                                         'inland_shipment_type': id.inland_shipment_type,
                                                         'ocean_shipment_type': id.ocean_shipment_type
                                                         })
            if route_id:
                route_id._onchange_address()
        if id.transport == 'land':
            route_id = self.env['freight.route'].create({'source_location_id': id.source_location_id.id,
                                                         'destination_location_id': id.destination_location_id.id,
                                                         'main_carriage': True,
                                                         'transport': id.transport,
                                                         'truck_ref': id.truck_ref,
                                                         'trucker': id.trucker.id,
                                                         'trucker_number': id.trucker_number,
                                                         'shipment_id': id.id,
                                                         'pickup_datetime': id.pickup_datetime,
                                                         'arrival_datetime': id.arrival_datetime,
                                                         'address_to': id.address_to,
                                                         'shipper_id': id.shipper_id.id,
                                                         'consignee_id': id.consignee_id.id,
                                                         'charge_type': 'f',
                                                         'inland_shipment_type': id.inland_shipment_type,
                                                         'ocean_shipment_type': id.ocean_shipment_type
                                                         })
            if route_id:
                route_id._onchange_address()
        return id

    @api.onchange('source_location_id', 'transport')
    def onchange_source_location_id(self):
        for line in self:
            if line.transport == 'air':
                return {'domain': {'source_location_id': [('air', '=', True)]}}
            elif line.transport == 'ocean':
                return {'domain': {'source_location_id': [('ocean', '=', True)]}}
            elif line.transport == 'land':
                return {'domain': {'source_location_id': [('land', '=', True)]}}

    @api.onchange('destination_location_id', 'transport')
    def onchange_destination_location_id(self):
        for line in self:
            if line.transport == 'air':
                return {'domain': {'destination_location_id': [('air', '=', True)]}}
            elif line.transport == 'ocean':
                return {'domain': {'destination_location_id': [('ocean', '=', True)]}}
            elif line.transport == 'land':
                return {'domain': {'destination_location_id': [('land', '=', True)]}}

    def action_freight_document(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Document',
            'res_model': 'freight.documents',
            'domain': [('freight_id', '=', self.id)],
            'context': {'default_freight_id': self.id},
            'view_mode': 'tree',
            'target': 'current'
        }

    @api.onchange('frequent_location_id')
    def _onchange_frequent_route(self):
        for rec in self:
            if rec.frequent_location_id:
                rec.destination_location_id = rec.frequent_location_id.destination_location_id.id
                rec.source_location_id = rec.frequent_location_id.source_location_id.id

    @api.depends('document_ids')
    def _compute_document_count(self):
        for rec in self:
            rec.document_count = self.env['freight.documents'].search_count([('freight_id', '=', rec.id)])

    @api.depends('freight_services')
    def _compute_service_charges(self):
        for rec in self:
            total = 0.0
            vendor_total = 0.0
            if rec.freight_services:
                for data in rec.freight_services:
                    if data.service_type == 'customer':
                        total = total + (data.sale * data.qty)
                    else:
                        vendor_total = vendor_total + (data.sale * data.qty)
                rec.total_service_charge = total
                rec.total_vendor_service_charge = vendor_total
            else:
                rec.total_service_charge = 0
                rec.total_vendor_service_charge = 0

    @api.depends('freight_routes')
    def _compute_route_charges(self):
        for rec in self:
            total = 0
            if rec.freight_routes:
                for data in rec.freight_routes:
                    if data.charge_type == 'p':
                        total = total + data.total_charge
                rec.total_route_charge = total
            else:
                rec.total_route_charge = 0

    @api.depends('custom_ids')
    def _compute_custom_check(self):
        for rec in self:
            if rec.custom_ids:
                for data in rec.custom_ids:
                    if not data.state == 'pass':
                        rec.pass_state = False
                    else:
                        rec.pass_state = True
            else:
                rec.pass_state = False

    def add_policy(self):
        for rec in self:
            if rec.total_charge and rec.policy_no and rec.policy_name and rec.date:
                self.policy_added = True
                data = {'service_id': self.env.ref('tk_freight.policy_product_1').id,
                        'name': self.policy_name + " - " + self.policy_no,
                        'qty': 1.0,
                        'sale': rec.total_charge,
                        'cost': rec.total_charge,
                        'shipment_id': rec.id
                        }
                self.freight_services.create(data)
            else:
                message = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'type': 'danger',
                        'title': ('Policy Information Missing !'),
                        'message': " Please Enter Policy No, Policy Name, Issue Date and Total Charge",
                        'sticky': False,
                    }
                }
                return message

    @api.depends('freight_packages')
    def _compute_final_charges(self):
        total = 0
        for rec in self:
            if rec.freight_packages:
                for data in rec.freight_packages:
                    total = total + (data.qty * data.charges)
                rec.final_charges = total
            else:
                rec.final_charges = 0.0

    def action_add_shipment(self):
        record = ""
        for rec in self:
            if rec.freight_packages:
                for data in rec.freight_packages:
                    if data.package_type == "item":
                        type = 'Box / Cargo'
                    else:
                        type = "Container / Box"
                    record = record + "{} - {} - {} \n".format(type, data.name, data.package.name)
        self.shipment_add = True
        self.freight_services.create({'service_id': self.env.ref('tk_freight.charges_product_1').id,
                                      'name': record,
                                      'qty': 1.0,
                                      'sale': self.final_charges,
                                      'cost': self.final_charges,
                                      'shipment_id': self.id})

    def action_add_route(self):
        record = ""
        for rec in self:
            if rec.freight_routes:
                for data in rec.freight_routes:
                    name = data.name
                    record = record + "{} - {}\n ".format(data.transport, name)
        self.route_add = True
        self.freight_services.create({
            'service_id': self.env.ref('tk_freight.route_product_1').id,
            'name': record,
            'qty': 1.0,
            'sale': self.total_route_charge,
            'cost': self.total_route_charge,
            'shipment_id': self.id
        })

    def action_create_vendor_bill(self):
        for rec in self:
            vendor_invoice = True
            bill_line = []
            if rec.freight_services:
                if rec.vendor == 'single':
                    for record in rec.freight_services:
                        if record.service_type == 'vendor':
                            if not record.vendor_invoice:
                                vendor_invoice = False
                    if not vendor_invoice:
                        for data in rec.freight_services:
                            if data.service_type == 'vendor':
                                if not data.vendor_invoice:
                                    data.status = 'bill'
                                    record = {
                                        'product_id': data.service_id.id,
                                        'name': "Services",
                                        'quantity': data.qty,
                                        'price_unit': data.sale
                                    }
                                    bill_line.append((0, 0, record))
                        main_data = {
                            'partner_id': rec.vendor_id.id,
                            'move_type': 'in_invoice',
                            'invoice_date': fields.date.today(),
                            'freight_operation_id': rec.id,
                            'invoice_line_ids': bill_line,
                        }
                        invoice_id = self.env['account.move'].create(main_data)
                        for invoice in rec.freight_services:
                            if invoice.service_type == 'vendor':
                                if not invoice.vendor_invoice:
                                    invoice.vendor_invoice = invoice_id.id
                elif rec.vendor == "multiple":
                    for data in rec.freight_services:
                        if data.service_type == 'vendor':
                            if not data.vendor_invoice:
                                data.status = 'bill'
                                record = {
                                    'product_id': data.service_id.id,
                                    'name': "Services",
                                    'quantity': data.qty,
                                    'price_unit': data.sale
                                }
                                bill_line.append((0, 0, record))
                                main_data = {
                                    'partner_id': data.vendor_id.id,
                                    'move_type': 'in_invoice',
                                    'invoice_date': fields.date.today(),
                                    'freight_operation_id': rec.id,
                                    'invoice_line_ids': bill_line,
                                }
                                bill_id = self.env['account.move'].create(main_data)
                                data.vendor_invoice = bill_id.id

    @api.onchange('address_to', 'source_location_id', 'destination_location_id', 'shipper_id', 'consignee_id')
    def _onchange_address(self):
        for rec in self:
            if rec in self:
                if rec.address_to == "sc_address":
                    if rec.shipper_id:
                        rec.s_zip = rec.shipper_id.zip
                        rec.s_street = rec.shipper_id.street
                        rec.s_street2 = rec.shipper_id.street2
                        rec.s_city = rec.shipper_id.city
                        rec.s_country_id = rec.shipper_id.country_id.id
                        rec.s_state_id = rec.shipper_id.state_id.id
                    if rec.consignee_id:
                        rec.d_zip = rec.consignee_id.zip
                        rec.d_street = rec.consignee_id.street
                        rec.d_street2 = rec.consignee_id.street2
                        rec.d_city = rec.consignee_id.city
                        rec.d_country_id = rec.consignee_id.country_id.id
                        rec.d_state_id = rec.consignee_id.state_id.id
                elif rec.address_to == "location_address":
                    if rec.source_location_id:
                        rec.s_zip = rec.source_location_id.zip
                        rec.s_street = rec.source_location_id.street
                        rec.s_street2 = rec.source_location_id.street2
                        rec.s_city = rec.source_location_id.city
                        rec.s_country_id = rec.source_location_id.country_id.id
                        rec.s_state_id = rec.source_location_id.state_id.id
                    if rec.destination_location_id:
                        rec.d_zip = rec.destination_location_id.zip
                        rec.d_street = rec.destination_location_id.street
                        rec.d_street2 = rec.destination_location_id.street2
                        rec.d_city = rec.destination_location_id.city
                        rec.d_country_id = rec.destination_location_id.country_id.id
                        rec.d_state_id = rec.destination_location_id.state_id.id

    @api.onchange('address_to', 'destination_location_id')
    def _onchange_port_location_delivery(self):
        for rec in self:
            if rec.address_to == "location_address" and rec.destination_location_id:
                rec.location_place_of_receipt = rec.destination_location_id.id
                rec.location_place_of_delivery = rec.destination_location_id.id

    def action_create_shipper_invoice(self):
        if not len(self.shipper_id.ids) == 1:
            raise ValidationError("Please select only one shipping provider. You have selected multiple shippers.")
        else:
            shipper_id = self.shipper_id.ids[0]
            shipment_ids = self.env['freight.shipment'].browse(self.ids)
            invoice_lines = []
            for data in shipment_ids:
                record = {
                    'product_id': self.env.ref('tk_freight.freight_order_1').id,
                    'name': data.name,
                    'quantity': 1,
                    'price_unit': data.total_service_charge,
                }
                invoice_lines.append((0, 0, record))
            data = {
                'partner_id': shipper_id,
                'invoice_line_ids': invoice_lines,
                'move_type': 'out_invoice',
            }
            invoice_id = self.env['account.move'].create(data)
            invoice_data = {
                'partner_id': shipper_id,
                'invoice_id': invoice_id.id,
                'amount': invoice_id.amount_total
            }
            self.env['freight.multiple.invoice'].create(invoice_data)
            return {
                'type': 'ir.actions.act_window',
                'name': 'Invoice',
                'res_model': 'account.move',
                'res_id': invoice_id.id,
                'view_mode': 'form',
                'target': 'current'
            }

    def action_create_consignee_invoice(self):
        if not len(self.consignee_id.ids) == 1:
            raise ValidationError("Please select only one consignee provider. You have selected multiple consignee.")
        else:
            consignee_id = self.consignee_id.ids[0]
            shipment_ids = self.env['freight.shipment'].browse(self.ids)
            invoice_lines = []
            for data in shipment_ids:
                record = {
                    'product_id': self.env.ref('tk_freight.freight_order_1').id,
                    'name': data.name,
                    'quantity': 1,
                    'price_unit': data.total_service_charge,
                }
                invoice_lines.append((0, 0, record))
            data = {
                'partner_id': consignee_id,
                'invoice_line_ids': invoice_lines,
                'move_type': 'out_invoice',
            }
            invoice_id = self.env['account.move'].create(data)
            invoice_data = {
                'partner_id': consignee_id,
                'invoice_id': invoice_id.id,
                'amount': invoice_id.amount_total
            }
            self.env['freight.multiple.invoice'].create(invoice_data)
            return {
                'type': 'ir.actions.act_window',
                'name': 'Invoice',
                'res_model': 'account.move',
                'res_id': invoice_id.id,
                'view_mode': 'form',
                'target': 'current'
            }


class FleetShipment(models.Model):
    _inherit = 'fleet.vehicle'

    is_freight_shipment = fields.Boolean()
    owner_id = fields.Many2one('res.partner', string="Owner")

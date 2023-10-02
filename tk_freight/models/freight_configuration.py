from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    shipper = fields.Boolean('Shipper')
    consignee = fields.Boolean('Consignee')
    agent = fields.Boolean('Agent')
    is_policy = fields.Boolean('Policy Company')
    multiple_invoice_ids = fields.One2many('freight.multiple.invoice', 'partner_id')


class CustomerInvoice(models.Model):
    _inherit = 'account.move'

    freight_operation_id = fields.Many2one(
        'freight.shipment', string='Freight Shipment')

    direction = fields.Selection(related="freight_operation_id.direction", string='Direction')
    transport = fields.Selection(related="freight_operation_id.transport", string='Transport Via')
    operation = fields.Selection(related="freight_operation_id.operation", string='Operation')
    shipper_id = fields.Many2one(related="freight_operation_id.shipper_id", string="Shipper")
    consignee_id = fields.Many2one(related="freight_operation_id.consignee_id", string="Consignee")
    agent_id = fields.Many2one(related="freight_operation_id.agent_id", string="Agent")
    source_location_id = fields.Many2one(related="freight_operation_id.source_location_id", string='Source Location')
    destination_location_id = fields.Many2one(related="freight_operation_id.source_location_id",
                                              string='Destination Location')

    @api.onchange('freight_operation_id')
    def _onchange_freight_operation_id(self):
        for rec in self:
            if rec.freight_operation_id:
                if rec.move_type == 'out_invoice':
                    rec.partner_id = rec.freight_operation_id.consignee_id.id
                if rec.move_type == 'in_invoice':
                    rec.partner_id = rec.freight_operation_id.agent_id.id


class CustomDepartment(models.Model):
    _name = 'custom.department'
    _description = 'Custom Department Services'

    freight_id = fields.Many2one('freight.shipment', string='Freight')
    declaration = fields.Char('Declaration No.')
    note = fields.Char(string='Note')
    date = fields.Date('Date')
    document = fields.Binary(string='Documents')
    file_name = fields.Char(string='File Name')
    state = fields.Selection([('pass', 'Pass'),
                              ('in_process', 'Processing'),
                              ('cancel', 'Cancel')],
                             string='State')

    def action_pass(self):
        for rec in self:
            rec.state = 'pass'

    def action_in_process(self):
        for rec in self:
            rec.state = 'in_process'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'


class ShipmentStages(models.Model):
    _name = 'freight.shipment.stages'
    _description = 'shipment Stage'
    _order = 'sequence, id'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer('Sequence', default=10)


class ShipmentTracking(models.Model):
    _name = 'shipment.tracking'
    _description = 'Shipment Stage'

    date = fields.Date('Date')
    time = fields.Float(string='Time')
    location_id = fields.Many2one('shipment.location', string="Location ")
    activity_id = fields.Many2one('shipment.location.activity', string="Activity")
    shipment_id = fields.Many2one('freight.shipment', string='Shipment ID')


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    freight_id = fields.Many2one('freight.shipment', string='Freight')
    direction = fields.Selection(related="freight_id.direction", string='Direction')
    transport = fields.Selection(related="freight_id.transport", string='Transport Via')
    operation = fields.Selection(related="freight_id.operation", string='Operation')
    shipper_id = fields.Many2one(related="freight_id.shipper_id", string="Shipper")
    consignee_id = fields.Many2one(related="freight_id.consignee_id", string="Consignee")
    agent_id = fields.Many2one(related="freight_id.agent_id", string="Agent")
    source_location_id = fields.Many2one(related="freight_id.source_location_id", string='Source Location')
    destination_location_id = fields.Many2one(related="freight_id.source_location_id", string='Destination Location')


class ShipmentPackageLine(models.Model):
    _name = 'shipment.package.line'
    _description = 'Freight Package Line'
    _rec_name = 'package'

    name = fields.Char(string='Container Number', required=True)
    package_type = fields.Selection([('item', 'Box / Cargo'), ('container', 'Container / Box')], string="Package Type")
    transport = fields.Selection(([('air', 'Air'), ('ocean', 'Ocean'), ('land', 'Land')]), string='Transport')
    shipment_id = fields.Many2one('freight.shipment', 'Shipment ID')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    package = fields.Many2one('freight.package', string='Size / Package', required=True)
    charges = fields.Monetary(related='package.charge', string='Charge')
    type = fields.Selection(([('dry', 'Dry'), ('reefer', 'Reefer')]), string="Type ")
    qty = fields.Float('Qty', required=True, default=1.0)
    harmonize = fields.Char('Harmonize')
    temperature = fields.Char('Temperature')
    vgm = fields.Char('VGM', help='Verified gross mass')
    carrier_seal = fields.Char('Carrier Seal')
    seal_number = fields.Char('Seal Number')
    reference = fields.Char('Reference')
    dangerous_goods = fields.Boolean('Dangerous Goods')
    class_number = fields.Char('Class Number')
    un_number = fields.Char('UN Number')
    Package_group = fields.Char('Packaging Group:')
    imdg_code = fields.Char('IMDG Code', help='International Maritime Dangerous Goods Code')
    flash_point = fields.Char('Flash Point')
    material_description = fields.Text('Material Description')
    freight_item_lines = fields.One2many('shipment.item', 'package_line_id')
    route_id = fields.Many2one('freight.route', 'Route')
    container_type = fields.Selection(
        [('GP', 'GP (General Purpose)'), ('HC', 'HC (High Cube)'),
         ('RF', 'RF (Reefer)'), ('FR', 'FR (Flat Rack)'),
         ('OT', 'OT (Open Top)'), ('GOH', 'GOH (Garment of Hanger)')], string="Type", default="GP")
    # Dimension
    volume = fields.Float('Volume (CBM)')
    gross_weight = fields.Float('Gross Weight (KG)')
    net_weight = fields.Float(string="Net Weight (KG)")
    height = fields.Float(string='Height(cm)')
    length = fields.Float(string='Length(cm)')
    width = fields.Float(string='Width(cm)')

    @api.onchange('package')
    def _onchange_package_dimension(self):
        for rec in self:
            if rec.package:
                rec.volume = rec.package.volume
                rec.gross_weight = rec.package.gross_weight
                rec.height = rec.package.height
                rec.length = rec.package.length
                rec.width = rec.package.width

    @api.onchange('package', 'package_type')
    def onchange_package_id(self):
        for line in self:
            if line.package_type == "item":
                if line.shipment_id.transport == 'air':
                    return {'domain': {'package': [('air', '=', True), ('item', '=', True), ('active', '=', True)]}}
                if line.shipment_id.transport == 'ocean':
                    return {'domain': {'package': [('ocean', '=', True), ('item', '=', True), ('active', '=', True)]}}
                if line.shipment_id.transport == 'land':
                    return {'domain': {'package': [('land', '=', True), ('item', '=', True), ('active', '=', True)]}}
            elif line.package_type == "container":
                if line.shipment_id.transport == 'air':
                    return {
                        'domain': {'package': [('air', '=', True), ('container', '=', True), ('active', '=', True)]}}
                if line.shipment_id.transport == 'ocean':
                    return {
                        'domain': {'package': [('ocean', '=', True), ('container', '=', True), ('active', '=', True)]}}
                if line.shipment_id.transport == 'land':
                    return {
                        'domain': {'package': [('land', '=', True), ('container', '=', True), ('active', '=', True)]}}


class ShipmentItem(models.Model):
    _name = 'shipment.item'
    _description = 'Shipment Item Line'

    name = fields.Char(string='Description')
    package_line_id = fields.Many2one('shipment.package.line', 'Shipment ID')
    package = fields.Many2one('freight.package', 'Item')
    type = fields.Selection(
        ([('dry', 'Dry'), ('reefer', 'Reefer')]), string="Operation")
    qty = fields.Float('Qty', default=1.0)
    # Dimension
    volume = fields.Float('Volume (CBM)')
    gross_weight = fields.Float('Gross Weight (KG)')
    height = fields.Float(string='Height(cm)')
    length = fields.Float(string='Length(cm)')
    width = fields.Float(string='Width(cm)')

    @api.onchange('package')
    def onchange_package_id(self):
        for line in self:
            if line.package_line_id.shipment_id.transport == 'air':
                return {'domain': {'package': [('air', '=', True), ('item', '=', True), ('active', '=', True)]}}
            if line.package_line_id.shipment_id.transport == 'ocean':
                return {'domain': {'package': [('ocean', '=', True), ('item', '=', True), ('active', '=', True)]}}
            if line.package_line_id.shipment_id.transport == 'land':
                return {'domain': {'package': [('land', '=', True), ('item', '=', True), ('active', '=', True)]}}

    @api.onchange('package')
    def _onchange_item_dimension(self):
        for rec in self:
            if rec.package:
                rec.volume = rec.package.volume
                rec.gross_weight = rec.package.gross_weight
                rec.height = rec.package.height
                rec.length = rec.package.length
                rec.width = rec.package.width
                rec.name = rec.package.desc


class ShipmentOrder(models.Model):
    _name = 'shipment.order'
    _description = 'Freight Order'

    shipment_id = fields.Many2one('freight.shipment', 'Shipment ID')
    transport = fields.Selection(([('air', 'Air'), ('ocean', 'Ocean'), ('land', 'Land')]), string='Transport')
    name = fields.Char(string='Description', required=True)
    package = fields.Many2one('freight.package', 'Package', required=True)
    type = fields.Selection(([('dry', 'Dry'), ('reefer', 'Reefer')]), string="Operation")
    volume = fields.Float('Volume (CBM)')
    gross_weight = fields.Float('Gross Weight (KG)')
    qty = fields.Float('Qty')

    @api.onchange('package')
    def onchange_package_id(self):
        for line in self:
            if line.shipment_id.transport == 'air':
                return {'domain': {'package': [('air', '=', True), ('container', '=', True)]}}
            if line.shipment_id.transport == 'ocean':
                return {'domain': {'package': [('ocean', '=', True), ('container', '=', True)]}}
            if line.shipment_id.transport == 'land':
                return {'domain': {'package': [('land', '=', True), ('container', '=', True)]}}


class FreightService(models.Model):
    _name = 'freight.service'
    _description = 'Freight Service'

    service_id = fields.Many2one('product.product', 'Service', domain="[('type','=','service')]")
    currency_id = fields.Many2one('res.currency', 'Currency')
    name = fields.Char(string='Description', required=1)
    service_type = fields.Selection([('customer', 'Shipper / Consignee'), ('vendor', 'Vendor')], default="customer",
                                    string="Service To")
    vendor = fields.Selection([('single', 'Single Vendor'), ('multiple', 'Multiple Vendor')], string='Vendor ', store=True)
    cost = fields.Float('Cost')
    sale = fields.Float('Sale', required=1)
    qty = fields.Float('Qty', default=1)
    route_id = fields.Many2one('freight.route', 'Route')
    shipment_id = fields.Many2one('freight.shipment', 'Shipment ID')
    customer_invoice = fields.Many2one('account.move')
    vendor_id = fields.Many2one('res.partner', domain="[('shipper','=',False),('consignee','=',False)]")
    vendor_invoice = fields.Many2one('account.move')
    invoiced = fields.Boolean('Invoiced')
    vendor_invoiced = fields.Boolean('Vendor Invoiced')
    status = fields.Selection([('bill', 'Bill Created'), ('quotation', 'Quotation Created'), ('pending', 'Pending')],
                              default="pending", readonly=True)
    sale_order_id = fields.Many2one('sale.order', string="Sale Order")

    @api.model
    def default_get(self, fields):
        res = super(FreightService, self).default_get(fields)
        vendor = self._context.get('vendor')
        res['vendor'] = vendor
        if res['vendor'] == 'single':
            res['vendor_id'] = self._context.get('vendor_id')
        return res

    # def _compute_vendor_bill(self):
    #     for rec in self:
    #         rec.vendor = self._context.get('vendor_id')


class FreightRoute(models.Model):
    _name = 'freight.route'
    _description = 'Freight Route'

    name = fields.Char('Route', compute='_compute_name')
    type = fields.Selection([('pickup', 'Pickup'), ('oncarriage', 'On Carriage'), ('precarriage', 'Pre Carriage'),
                             ('delivery', 'Delivery')], string='Type')
    shipment_id = fields.Many2one('freight.shipment', 'Shipment ID')
    transport = fields.Selection([('air', 'Air'), ('ocean', 'Ocean'), ('land', 'Land')], string='Transport')
    ocean_shipment_type = fields.Selection([('fcl', 'FCL'), ('lcl', 'LCL')], string='Ocean Shipment Type')
    inland_shipment_type = fields.Selection([('ftl', 'FTL'), ('ltl', 'LTL')], string='Inland Shipment Type')
    freight_services = fields.One2many('freight.service', 'route_id')
    main_carriage = fields.Boolean('Main Carriage')
    shipper_id = fields.Many2one('res.partner', 'Shipper', domain=[('shipper', '=', True)])
    consignee_id = fields.Many2one('res.partner', 'Consignee', domain=[('consignee', '=', True)])
    charge_type = fields.Selection([('f', 'Free'), ('p', 'Paid')], string='Charge Type')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    total_charge = fields.Monetary(string="Charges")
    address_to = fields.Selection([('sc_address', 'Contact Address'),
                                   ('location_address', 'Location Address')], string="Address", default="sc_address")
    # Datetime/Common Field
    pickup_datetime = fields.Datetime('Estimate Pickup Time')
    arrival_datetime = fields.Datetime('Estimate Arrival Time')
    final_charges = fields.Monetary(string='Total Charges')

    # Source Address
    source_location = fields.Char(string="Source")
    source_location_id = fields.Many2one('freight.port', 'Source Location', index=True)
    s_zip = fields.Char()
    s_street = fields.Char()
    s_street2 = fields.Char()
    s_city = fields.Char()
    s_country_id = fields.Many2one('res.country')
    s_state_id = fields.Many2one('res.country.state')
    # Destinations Address
    destination_location = fields.Char(string="Destination")
    destination_location_id = fields.Many2one('freight.port', 'Destination Location', index=True)
    d_zip = fields.Char()
    d_street = fields.Char()
    d_street2 = fields.Char()
    d_city = fields.Char()
    d_country_id = fields.Many2one('res.country')
    d_state_id = fields.Many2one('res.country.state')
    # Ocean
    obl = fields.Char('OBL No.', help='Original Bill Of Lading')
    voyage_no = fields.Char('Voyage No')
    vessel_id = fields.Many2one('freight.vessel', 'Vessel')

    # Air
    mawb_no = fields.Char('MAWB No')
    airline_id = fields.Many2one('freight.airline', 'Airline')
    flight_no = fields.Char('Flight No')

    # Land
    truck_ref = fields.Char('CMR/RWB#/PRO#:')
    trucker = fields.Many2one('fleet.vehicle', 'Trucker')
    trucker_number = fields.Char(string='Reference')

    @api.model
    def create(self, values):
        id = super(FreightRoute, self).create(values)
        id.freight_services.write({'shipment_id': id.shipment_id.id})
        return id

    def write(self, vals):
        res = super(FreightRoute, self).write(vals)
        self.freight_services.write({'shipment_id': self.shipment_id.id})
        return res

    def default_get(self, fields_list):
        res = super(FreightRoute, self).default_get(fields_list)
        res['shipper_id'] = self._context.get('shipper_id')
        res['consignee_id'] = self._context.get('consignee_id')
        return res

    @api.depends('address_to', 'source_location_id', 'destination_location_id', 'd_city', 's_city')
    def _compute_name(self):
        for rec in self:
            if rec.address_to == "sc_address":
                if rec.d_city and rec.s_city:
                    rec.name = rec.s_city + " to " + rec.d_city
                else:
                    rec.name = ""
            elif rec.address_to == "location_address":
                if rec.source_location_id and rec.destination_location_id:
                    rec.name = rec.source_location_id.name + " to " + rec.destination_location_id.name
                else:
                    rec.name = ""
            else:
                rec.name = ""

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


class FreightPort(models.Model):
    _name = 'freight.port'
    _description = 'Freight Port'

    code = fields.Char(string='Code')
    name = fields.Char(string='Name')
    air = fields.Boolean(string='Air')
    ocean = fields.Boolean(string='Ocean')
    land = fields.Boolean(string='Land')
    active = fields.Boolean(default=True, string='Active')
    # Address
    zip = fields.Char(string='Pin Code', size=6)
    street = fields.Char(string='Street1')
    street2 = fields.Char(string='Street2')
    city = fields.Char(string='City')
    country_id = fields.Many2one('res.country', 'Country')
    state_id = fields.Many2one(
        "res.country.state", string='State', readonly=False, store=True,
        domain="[('country_id', '=?', country_id)]")


class FreightVessel(models.Model):
    _name = 'freight.vessel'
    _description = 'Freight Vessel'

    code = fields.Char(string='Code')
    name = fields.Char(string='Name')
    global_zone = fields.Char(string='Global Zone')
    country = fields.Many2one('res.country', 'Country')
    active = fields.Boolean(default=True, string='Active')
    imo_number = fields.Char(string="IMO")
    flag_state = fields.Char(string="Flag state")
    port_of_registry = fields.Char(string="Port of Registry")
    capacity = fields.Char(string="Cargo Capacity")
    engine = fields.Char(string="Type")
    engine_power = fields.Char(string="Power")
    speed = fields.Char(string="Speed(Knots)")
    owner_id = fields.Many2one('res.partner', string='Shipping Line')


class FreightAirline(models.Model):
    _name = 'freight.airline'
    _description = 'Freight Airline'

    code = fields.Char(string='Code')
    name = fields.Char(string='Name')
    icao = fields.Char(string='ICAO')
    country = fields.Many2one('res.country', 'Country')
    active = fields.Boolean(default=True, string='Active')
    aircraft_type = fields.Char(string="Aircraft Type")
    capacity = fields.Char(string="Cargo Capacity")
    owner_id = fields.Many2one('res.partner', string='Owner')


class FreightIncoterms(models.Model):
    _name = 'freight.incoterms'
    _description = 'Freight Incoterms'

    code = fields.Char(string='Code')
    name = fields.Char(string='Name',
                       help="International Commercial Terms are a series of predefined commercial terms used in international transactions.")
    active = fields.Boolean(default=True, string='Active')


class FreightPackage(models.Model):
    _name = 'freight.package'
    _description = 'Freight Package'

    code = fields.Char(string='Code')
    name = fields.Char(string='Name / Size')
    container = fields.Boolean('Container/Box')
    item = fields.Boolean(string='Is Item')
    other = fields.Boolean('Other')
    active = fields.Boolean(default=True, string='Active')
    air = fields.Boolean(string='Air')
    ocean = fields.Boolean(string='Ocean')
    land = fields.Boolean(string='Land')
    desc = fields.Char(string="Description")
    height = fields.Float(string='Height(cm)')
    length = fields.Float(string='Length(cm)')
    width = fields.Float(string='Width(cm)')
    volume = fields.Float('Volume (CBM)')
    gross_weight = fields.Float('Gross Weight (KG)')

    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', string='Currency')
    charge = fields.Monetary(string='Charges')


class FreightMoveType(models.Model):
    _name = 'freight.move.type'
    _description = 'Freight Move Type'

    code = fields.Char(string='Code')
    name = fields.Char(string='Name')
    active = fields.Boolean(default=True, string='Active')


class FreightDocuments(models.Model):
    _name = 'freight.documents'
    _description = 'Document related to Freight Shipment'
    _rec_name = 'type_id'

    freight_id = fields.Many2one(
        'freight.shipment', string='Shipment', readonly=True)
    type_id = fields.Many2one('certificate.type', string='Type')
    document_date = fields.Date(string='Date', default=fields.Date.today())
    document = fields.Binary(string='Documents', required=True)
    file_name = fields.Char(string='File Name')


class CertificateType(models.Model):
    _name = 'certificate.type'
    _description = 'Type Of Certificate'
    _rec_name = 'type'

    type = fields.Char(string='Type')


class PolicyRisk(models.Model):
    _name = 'policy.risk'
    _description = 'Policy Risk Details'

    name = fields.Char(string='Title')
    desc = fields.Char(string='Description')


class FrequentRoute(models.Model):
    _name = 'freight.frequent.route'
    _description = 'Frequent Route'

    name = fields.Char(string='Name')
    source_location_id = fields.Many2one(
        'freight.port', string="Source Location")
    destination_location_id = fields.Many2one(
        'freight.port', string="Destination Location")

    @api.onchange('source_location_id', 'destination_location_id')
    def _onchage_source_destination(self):
        for rec in self:
            if rec.source_location_id and rec.destination_location_id:
                rec.name = rec.source_location_id.name + \
                           " - " + rec.destination_location_id.name


class FreightMultipleInvoice(models.Model):
    _name = "freight.multiple.invoice"
    _description = "Multiple Invoice"

    partner_id = fields.Many2one('res.partner')
    invoice_id = fields.Many2one('account.move', string="Invoice")
    date = fields.Date(string="Date", default=fields.Date.today())
    amount = fields.Float(string="Amount")


class ShipmentLocation(models.Model):
    _name = "shipment.location"
    _description = "Shipment Location"

    name = fields.Char(string="Title")


class ShipmentActivity(models.Model):
    _name = "shipment.location.activity"
    _description = "Shipment Location Activity"

    name = fields.Char(string="Activity")

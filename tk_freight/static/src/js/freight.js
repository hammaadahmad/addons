odoo.define('tk_freight.FreightDashboard', function (require) {
  'use strict';
  const AbstractAction = require('web.AbstractAction');
  const ajax = require('web.ajax');
  const core = require('web.core');
  const rpc = require('web.rpc');
  const session = require('web.session')
  const web_client = require('web.web_client');
  const _t = core._t;
  const QWeb = core.qweb;

  const ActionMenu = AbstractAction.extend({

    template: 'freightDashboard',

    events: {
      'click .house-shipment': 'view_house_shipment',
      'click .direct-shipment': 'view_direct_shipment',
      'click .master-shipment': 'view_master_shipment',
      'click .pending-booking': 'view_pending_booking',
      'click .total-port': 'view_total_port',
      'click .total-packages': 'view_total_packages',
    },
    renderElement: function (ev) {
      const self = this;
      $.when(this._super())
        .then(function (ev) {
          rpc.query({
            model: "dashboard.details",
            method: "get_freight_info",
          }).then(function (result) {
            $('#direct_count').empty().append(result['direct_count']);
            $('#house_count').empty().append(result['house_count']);
            $('#master_count').empty().append(result['master_count']);
            $('#pending_booking').empty().append(result['pending_booking']);
            $('#total_port').empty().append(result['total_port']);
            $('#total_packages').empty().append(result['total_packages']);
            self.freightTransportInfo(result['transport']);
            self.freightOperationInfo(result['fright_operation']);
            self.freightStageInfo(result['shipment_stages']);
            self.freightTopConsignee(result['top_consign']);
            self.freightMoveType(result['move_type']);
            self.freightDirection(result['freight_direction']);
            self.freightMonthShipment(result['get_shipment_month']);
            self.freightTopShipper(result['top_shipper']);
            self.freightBillInvoice(result['get_bill_invoice']);
          });
        });
    },
    view_house_shipment: function (ev) {
      ev.preventDefault();
      return this.do_action({
        name: _t('House Shipment'),
        type: 'ir.actions.act_window',
        res_model: 'freight.shipment',
        domain: [['operation', '=', 'house']],
        context: { 'default_operation': 'house' },
        views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
        target: 'current'
      });
    },
    view_direct_shipment: function (ev) {
      ev.preventDefault();
      return this.do_action({
        name: _t('Direct Shipment'),
        type: 'ir.actions.act_window',
        res_model: 'freight.shipment',
        domain: [['operation', '=', 'direct']],
        context: { 'default_operation': 'direct' },
        views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
        target: 'current'
      });
    },
    view_master_shipment: function (ev) {
      ev.preventDefault();
      return this.do_action({
        name: _t('Master Shipment'),
        type: 'ir.actions.act_window',
        res_model: 'freight.shipment',
        domain: [['operation', '=', 'master']],
        context: { 'default_operation': 'master' },
        views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
        target: 'current'
      });
    },
    view_pending_booking: function (ev) {
      ev.preventDefault();
      return this.do_action({
        name: _t('Draft Booking'),
        type: 'ir.actions.act_window',
        res_model: 'shipment.freight.booking',
        domain: [['state', '=', 'draft']],
        views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
        target: 'current'
      });
    },
    view_total_port: function (ev) {
      ev.preventDefault();
      return this.do_action({
        name: _t('Total Port'),
        type: 'ir.actions.act_window',
        res_model: 'freight.port',
        views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
        target: 'current'
      });
    },
    view_total_packages: function (ev) {
      ev.preventDefault();
      return this.do_action({
        name: _t('Packages'),
        type: 'ir.actions.act_window',
        res_model: 'freight.package',
        views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
        target: 'current'
      });
    },

    get_action: function (ev, name, res_model) {
      ev.preventDefault();
      return this.do_action({
        name: _t(name),
        type: 'ir.actions.act_window',
        res_model: res_model,
        views: [[false, 'tree'], [false, 'form']],
        target: 'current'
      });
    },
    //Graph-start
    apexGraph: function () {
      Apex.grid = {
        padding: {
          right: 0,
          left: 0,
          top: 10,
        }
      }
      Apex.dataLabels = {
        enabled: false
      }
    },
    freightOperationInfo: function (data) {

      const options = {
        title: {
          text: 'Operations'
        },
        series: [{
          name: "Shipments",
          data: data[0]
        }],
        chart: {
          type: 'bar',
          height: 410
        },
        plotOptions: {
          bar: {
            borderRadius: 4,
            distributed: true,
          }
        },
        dataLabels: {
          enabled: false,
        },
        colors: ['#B4F8C8', '#A0E7E5', '#FFAEBC'],
        xaxis: {
          categories: data[1],
        },
      };
      this.renderGraph("#freight_operation", options);
    },
    freightTransportInfo: function (data) {
      const options = {
        series: data[1],
        chart: {
          type: 'donut',
          height: 410
        },
        colors: ['#6dd5ed', '#06beb6', '#b9e769'],
        dataLabels: {
          enabled: false
        },
        labels: data[0],
        legend: {
          position: 'bottom',
        },

      };
      this.renderGraph("#freight_transport", options);
    },
    freightStageInfo: function (data) {
      const options = {
        series: [{
          name: "Shipments",
          data: data[1]
        }],
        chart: {
          height: 350,
          type: 'bar',
          events: {
            click: function (chart, w, e) {
            }
          }
        },
        colors: ['#ff9999', '#99ff99', '#facd60', '#7EC8E3', '#1ac0c6'],
        plotOptions: {
          bar: {
            columnWidth: '45%',
            distributed: true,
          }
        },
        dataLabels: {
          enabled: false
        },
        legend: {
          show: false
        },
        xaxis: {
          categories: data[0],
          labels: {
            style: {
              colors: '#000C66',
              fontSize: '12px'
            }
          }
        }
      };
      this.renderGraph("#freight_stage", options);
    },
    freightTopConsignee: function (data) {
      const options = {
        series: [{
          name: "Amount",
          data: data[1]
        }],
        chart: {
          height: 350,
          type: 'bar',
          events: {
            click: function (chart, w, e) {
            }
          }
        },
        colors: ['#f29e4c', '#f1c453', '#efea5a', '#b9e769', '#83e377', '#16db93', '#0db39e', '#048ba8', '#2c699a', '#54478c'],
        plotOptions: {
          bar: {
            columnWidth: '45%',
            distributed: true,
          }
        },
        dataLabels: {
          enabled: false
        },
        legend: {
          show: false
        },
        xaxis: {
          categories: data[0],
          labels: {
            style: {
              colors: '#000C66',
              fontSize: '12px'
            }
          }
        }
      };
      this.renderGraph("#top_consignee", options);
    },

    freightTopShipper:function(data){
          const options = {
        series: [{
          name: "Shipments",
          data: data[1]
        }],
        chart: {
          height: 350,
          type: 'bar'
        },
        colors: ['#f29e4c', '#f1c453', '#efea5a', '#b9e769', '#83e377', '#16db93', '#0db39e', '#048ba8', '#2c699a', '#54478c'],
        plotOptions: {
          bar: {
            columnWidth: '45%',
            distributed: true,
          }
        },
        dataLabels: {
          enabled: false
        },
        legend: {
          show: false
        },
        xaxis: {
          categories: data[0],
          labels: {
            style: {
              colors: '#000C66',
              fontSize: '12px'
            }
          }
        }
      };
      this.renderGraph("#top_shipper", options);
    },

    freightMoveType: function (data) {
    const options = {
          series: data[1],
          chart: {
           height: 410,
          type: 'polarArea'
        },
        labels: data[0],
        fill: {
          opacity: 1
        },
        stroke: {
          width: 1,
           colors:['#46C2CB', '#54478c', '#0db39e',  '#b9e769',  '#83e377', '#16db93', '#D09CFA', '#048ba8', '#2c699a', '#FFFFD0'],
        },
        yaxis: {
          show: false
        },
        legend: {
          position: 'bottom'
        },
        theme: {
         colors:['#46C2CB', '#54478c', '#0db39e',  '#b9e769',  '#83e377', '#16db93', '#D09CFA', '#048ba8', '#2c699a', '#FFFFD0'],
        }
        };
    this.renderGraph("#move_type", options);
    },

     freightDirection: function (data) {
         const options = {
        series: data[1],
        chart: {
          type: 'donut',
          height: 410
        },
        colors: ['#6dd5ed', '#06beb6'],
        dataLabels: {
          enabled: false
        },
        labels: data[0],
        legend: {
          position: 'bottom',
        },
      };
      this.renderGraph("#direction", options);
      },

      freightMonthShipment: function (data) {
       const options = {
          series: [{
          name: 'Air',
          data: data[1]
        }, {
          name: 'Ocean',
          data: data[3]
        }, {
          name: 'Land',
          data: data[2]
        }],
          chart: {
          type: 'bar',
          height: 350,
          stacked: true,
          toolbar: {
            show: true
          },
          zoom: {
            enabled: true
          }
        },
        responsive: [{
          breakpoint: 480,
          options: {
            legend: {
              position: 'bottom',
              offsetX: -10,
              offsetY: 0
            }
          }
        }],
        plotOptions: {
          bar: {
            horizontal: false,
            borderRadius: 10,
            dataLabels: {
              total: {
                enabled: true,
                style: {
                  fontSize: '13px',
                  fontWeight: 900
                }
              }
            }
          },
        },
        xaxis: {
          categories: data[0]
        },
        legend: {
          position: 'right',
          offsetY: 40
        },
        fill: {
          opacity: 1
        }
        };

       this.renderGraph("#shipment_month", options);
      },

      freightBillInvoice: function (data) {
       const options = {
          series: [{
          name: 'Bills',
          data: data[1]
        }, {
          name: 'Invoice',
          data: data[2]
        }],
          chart: {
          type: 'bar',
          height: 350,
          stacked: true,
          toolbar: {
            show: true
          },
          zoom: {
            enabled: true
          }
        },
        responsive: [{
          breakpoint: 480,
          options: {
            legend: {
              position: 'bottom',
              offsetX: -10,
              offsetY: 0
            }
          }
        }],
        plotOptions: {
          bar: {
            horizontal: false,
            borderRadius: 10,
            dataLabels: {
              total: {
                enabled: true,
                style: {
                  fontSize: '13px',
                  fontWeight: 900
                }
              }
            }
          },
        },
        xaxis: {
          categories: data[0]
        },
        legend: {
          position: 'right',
          offsetY: 40
        },
        fill: {
          opacity: 1
        }
        };

       this.renderGraph("#invoice_bill", options);
      },

    renderGraph: function (render_id, options) {
      $(render_id).empty();
      const graphData = new ApexCharts(document.querySelector(render_id), options);
      graphData.render();
    },
    //Graph-end
    willStart: function () {
          const self = this;
            return this._super()
            .then(function() {});
        },
  });
  core.action_registry.add('freight_dashboard', ActionMenu);
});

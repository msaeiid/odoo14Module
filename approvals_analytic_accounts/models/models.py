import datetime
from odoo.exceptions import UserError
from odoo import models, fields, api
from openerp.tools.translate import _

CATEGORY_SELECTION = [
    ('required', 'Required'),
    ('optional', 'Optional'),
    ('no', 'None')]


class ApprovalCategoryInherit(models.Model):
    _name = 'approval.category'
    _inherit = 'approval.category'
    _description = 'Approvals analytic accounts'

    approval_type = fields.Selection(selection_add=[('analytic_accounts', 'Analytic Accounts\'s')])
    has_analytic_accounts = fields.Selection(CATEGORY_SELECTION, string="Has Analytic Accounts", default="no",
                                             required=True)

    @api.onchange('approval_type')
    def _onchange_approval_type(self):
        super(ApprovalCategoryInherit, self)._onchange_approval_type()
        if self.approval_type == 'analytic_accounts':
            self.has_product = 'required'
            self.has_quantity = 'required'
            self.has_analytic_accounts = 'required'

    stock_picking_type = fields.Many2one('stock.picking.type', ondelete='set null')


class ApprovalRequestInherit(models.Model):
    _name = 'approval.request'
    _inherit = 'approval.request'
    _description = 'Approvals Request'

    analytic_accounts = fields.Many2one('account.analytic.account', ondelete='set null')
    # reflection field
    is_linked_to_inventory_operation = fields.Selection(related='category_id.approval_type',
                                                        readonly=True,
                                                        store=False)
    has_analytic_accounts = fields.Selection(related='category_id.has_analytic_accounts', store=False, readonly=True)
    is_inventory_operation_is_allowed = fields.Boolean(store=False, compute='_compute_inventory_operation_is_allowed')
    is_send_inventory_transfer = fields.Boolean(default=False)
    # reflect approval.category description field
    approval_category_description = fields.Char(related='category_id.description', store=False, readonly=False)

    def _compute_inventory_operation_is_allowed(self):
        if self.category_id.approval_type == 'analytic_accounts' and self.request_status == 'approved' and not self.is_send_inventory_transfer and (
                self.env.user in self.approver_ids.user_id):
            self.is_inventory_operation_is_allowed = True
        else:
            self.is_inventory_operation_is_allowed = False

    def send_inventory_transfer(self):
        move_ids_without_package = self.get_related_products()
        vals = {'is_locked': True,
                'immediate_transfer': False,
                'priority': '0',
                'partner_id': False,
                'picking_type_id': self.category_id.stock_picking_type.id,
                'location_id': self.category_id.stock_picking_type.default_location_src_id.id,
                'location_dest_id': self.category_id.stock_picking_type.default_location_dest_id.id,
                'scheduled_date': datetime.datetime.now(),
                'origin': self.name,
                'owner_id': False,
                'package_level_ids_details': [],
                'move_ids_without_package': move_ids_without_package,
                'package_level_ids': [],
                'move_type': 'direct',
                'user_id': self.env.user.id,
                'company_id': self.company_id.id,
                'note': False,
                'message_follower_ids': [],
                'activity_ids': [],
                'message_ids': [],
                # '_barcode_scanned': False
                }
        result = self.env['stock.picking'].create(vals)
        if result.product_id.id != 0:
            self.is_send_inventory_transfer = True
        result.action_confirm()
        result.analytic_accounts = self.analytic_accounts
        return result

    def get_related_products(self):
        result = []
        temp = 1026
        for product in self.product_line_ids:
            temp += 1
            result.append(
                [0,
                 f'virtual_{temp}',
                 {'company_id': product.company_id,
                  'name': product.product_id.name,
                  'state': 'draft',
                  'picking_type_id': self.category_id.stock_picking_type.id,
                  'location_id': self.category_id.stock_picking_type.default_location_src_id.id,
                  'location_dest_id': self.category_id.stock_picking_type.default_location_dest_id.id,
                  'additional': False,
                  'product_id': product.product_id.id,
                  'description_picking': False,
                  'date': datetime.datetime.now(),
                  'product_uom_qty': product.quantity,
                  'product_uom': self.product_line_ids.product_uom_id.id,
                  'lot_ids': [[6, False, []]]}])
        return result


class StockPickingInherit(models.Model):
    _name = 'stock.picking'
    _inherit = 'stock.picking'

    analytic_accounts = fields.Many2one('account.analytic.account', ondelete='set null')


class ApprovalProductLine(models.Model):
    _name = 'approval.product.line'
    _inherit = 'approval.product.line'

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id.id and not len(self.product_id.orderpoint_ids):
            val = {'product': self.product_id.name}
            message = {
                'title': _('User error'),
                'message': (_('Selected product %s doesnt have any order point rule') % (self.product_id.name))
            }
            return {'value': val,
                    'warning': message}
        else:
            super(ApprovalProductLine, self)._onchange_product_id()

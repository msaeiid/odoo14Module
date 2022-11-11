from odoo import models, fields


class DocumentTagExtend(models.Model):
    _name = 'documents.tag'
    _inherit = 'documents.tag'
    # add color field in kanban view
    color = fields.Integer(string="color")

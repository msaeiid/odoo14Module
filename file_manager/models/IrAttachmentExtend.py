from odoo import models, fields
from odoo.exceptions import MissingError


class IrAttachmentExtend(models.Model):
    _name = 'ir.attachment'
    _inherit = "ir.attachment"

    file_manager_id = fields.One2many('file.manager', 'attachment_id')

    def unlink(self):
        if len(self) == 1:
            in_use = False
            # Check for lock
            document = self.env['documents.document'].browse(self.res_id)
            # check for document lock status continue if possible
            try:
                document.is_permitted()
            except MissingError as e:
                return super(IrAttachmentExtend, self).unlink()

            # lock document temporary
            in_use = document.lock_unlock(True)
            result = super(IrAttachmentExtend, self).unlink()
            # check if this method locked the document if yes unlock the document
            if in_use and document.exists():
                document.lock_unlock(False)
            return result
        else:
            return super(IrAttachmentExtend, self).unlink()

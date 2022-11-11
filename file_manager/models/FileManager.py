from odoo import models, fields, api


class FileManager(models.Model):
    _name = 'file.manager'
    _description = "File Manager"
    _order = 'attachment_id desc'

    # preferences field
    title = fields.Char(string='Short message/Code')
    body = fields.Html(string='Body')
    tags_ids = fields.Many2many('documents.tag')
    # relation fields
    documents_id = fields.Many2one(
        'documents.document', string='Document', ondelete='cascade')
    attachment_id = fields.Many2one(
        'ir.attachment', string='IrAttachment', ondelete='cascade')
    # Fields that aren't saved
    datas = fields.Binary(related='attachment_id.datas',
                          related_sudo=True, readonly=False, store=False, required=True)
    mimetype = fields.Char(related='attachment_id.mimetype',
                           default='application/octet-stream', store=False)
    # Fields that aren't saved and reflection fields to show data in tree
    name = fields.Char('Name', copy=True, store=False,
                       related='attachment_id.name')
    type = fields.Selection(string='Type', store=False,
                            related='attachment_id.type')
    file_size = fields.Integer(related='attachment_id.file_size', store=False)
    id = fields.Integer(related='attachment_id.id', store=False)
    url = fields.Char('URL', index=True, size=1024,
                      store=False, related='attachment_id.url')
    is_main = fields.Boolean(default=False)
    get_name = fields.Char('GetName', copy=True,
                           store=False, related='attachment_id.name')

    # اضافه کردن مشخصه نوع مستند، پروژه و محصول به مدیریت مستندات (#17)

    connected_to_choices = ([
        ('project', 'Project'),
        ('product', 'Product'),
    ])
    connected_to = fields.Selection(connected_to_choices)
    product_template_id = fields.Many2many(
        'product.template', string='Product', required=False)
    project_project_id = fields.Many2many(
        'project.project', string='Project',  required=False)

    category = fields.Many2many(
        'file.manager.category',  required=False, string='category')
    # اضافه کردن مشخصه نوع مستند، پروژه و محصول به مدیریت مستندات (#17)

    @api.model
    def create(self, values):
        # if document is created or written
        # lock is guaranteed by write method of document when user trying to add revision
        if values.get('new') or values.get('revision'):
            file_manager = super(FileManager, self).create(
                [{
                    'documents_id': values.get('documents_id'),
                    'attachment_id': values.get('attachment_id')
                }])
            if file_manager.documents_id.file_manager_id == 1:
                file_manager.is_main = True
            return file_manager

        # add a revision with file manager
        in_use = False
        # check for document lock status continue if possible
        self.documents_id.is_permitted()
        # lock file temporary
        in_use = self.documents_id.lock_unlock(True)
        # get selected document
        document = self.env['documents.document'].browse(
            self._context.get('active_id'))

        # iterate in all revisions except newly added one to set is_main to False
        for item in document.file_manager_id:
            item.is_main = False

        # create revision with write method of document
        # revision type in file

        # get mimetype
        from mimetypes import MimeTypes
        mime = MimeTypes()
        if values.get('type') == 'binary':
            document_id = document.write(
                {
                    'type': values.get('type'),
                    'datas': values.get('datas'),
                    'mimetype': mime.guess_type(values.get('name'))[0],
                    'name': values.get('name'),
                })
            if len(document.file_manager_id.search([('attachment_id', '=', document.attachment_id.id)])) == 0:
                file_manager = super(FileManager, self).create({
                    'title': values.get('title'),
                    'body': values.get('body'),
                    'tags_ids': values.get('tags_ids'),
                    'attachment_id': document.attachment_id.id,
                    'documents_id': document.id,
                    'is_main': True
                })
            else:
                document.file_manager_id.search([('attachment_id', '=', document.attachment_id.id)])[0].write(
                    {
                        'title': values.get('title'),
                        'body': values.get('body'),
                        'tags_ids': values.get('tags_ids'),
                        'is_main': True
                    }
                )
                file_manager = document.file_manager_id.search(
                    [('attachment_id', '=', document.attachment_id.id)])[0]

            # check if this method locked the document if yes unlock the document
            if in_use:
                self.documents_id.lock_unlock(False)
            # return corresponding file_manager
            return file_manager
        document_id = document.write(
            {
                'datas': values.get('datas'),
                'mimetype': mime.guess_type(values.get('name'))[0],
                'name': values.get('name'),
            })
        # update created revision title,body,tags_ids
        document.file_manager_id.search([('attachment_id', '=', document.attachment_id.id)])[0].write(
            {
                'title': values.get('title'),
                'body': values.get('body'),
                'tags_ids': values.get('tags_ids'),
                # اضافه کردن مشخصه نوع مستند، پروژه و محصول به مدیریت مستندات (#17)
                'project_project_id': values.get('project_project_id'),
                'product_template_id': values.get('product_template_id'),
                'connected_to': values.get('connected_to'),
                'category': values.get('category'),
                # اضافه کردن مشخصه نوع مستند، پروژه و محصول به مدیریت مستندات (#17)
            }
        )
        # check if this method locked the document if yes unlock the document
        if in_use:
            self.documents_id.lock_unlock(False)
        # return corresponding file_manager
        return document.file_manager_id.search([('attachment_id', '=', document.attachment_id.id)])[0]

    def write(self, values):
        in_use = False
        # check for document lock status continue if possible
        self.documents_id.is_permitted()
        # lock document temporary
        in_use = self.documents_id.lock_unlock(True)

        status = super(FileManager, self).write(values)
        # if document updated file name will be renamed here
        if values.get('name', False):
            self.attachment_id.write({
                'name': values.get('name')
            })
            # update main document url
        if self.is_main and self.type == 'url':
            self.documents_id.url = self.url
        if status:
            # check if this method locked the document if yes unlock the document
            if in_use:
                self.documents_id.lock_unlock(False)
            return status

    def unlink(self):
        for item in self:
            # check if selected file is main file or not
            if item.is_main:
                item.documents_id.has_revision()
            elif item.type == 'binary':
                return self.attachment_id.unlink()
            # elif item.type == 'url':
            #     if item.is_main:
            #         return self.documents_id.unlink()
            #     return super(FileManager, self).unlink()

    # how object shown
    def name_get(self):
        result = []
        for item in self:
            result.append((item.id, item.name))
        return result


class category(models.Model):
    _name = 'file.manager.category'
    _description = "File manager Category"

    category_title = fields.Char(string='طبقه بندی موضوعی')

    def name_get(self):
        result = []
        for item in self:
            result.append((item.id, item.category_title))
        return result

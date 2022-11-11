from odoo import models, fields, api
from odoo.exceptions import Warning


class DocumentExtend(models.Model):
    _name = 'documents.document'
    _inherit = 'documents.document'
    # relation fields
    file_manager_id = fields.One2many('file.manager', 'documents_id')

    # if add button on kanban view clicked
    def add_revision(self):
        return {
            'name': 'Add Revision',
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'file.manager',
            'type': 'ir.actions.act_window',
            'target': 'new',
            # 'context': {'selected_doc': self['id']}
        }

    # if view button on kanban view clicked
    def view_revision_list(self):
        tree_view = {
            'name': self.name,
            'view_type': 'form',
            'view_mode': 'kanban,tree,form',
            'view_id': False,
            'res_model': 'file.manager',
            'type': 'ir.actions.act_window',
            'target': 'main',
            'domain': [
                # '&',
                ('documents_id', '=', self.id)
                # ,('attachment_id.id', '!=', self.attachment_id.id)
            ]
        }
        return tree_view

    @api.model
    def create(self, values):
        document = super(DocumentExtend, self).create(values)
        # because of some user problem new uploaded document will be lock automatically
        document.lock_uid = self.env.user
        return document

    def write(self, values):
        temp = False
        # update lock state doesn't need to lock document
        if 'lock_uid' in values.keys():
            # if admin tries to unlock the file
            if (self.env.is_admin() or self.user_has_groups('documents.group_documents_manager')) and self.lock_uid:
                temp = True
            self.is_permitted(temp)
            return super(DocumentExtend, self).write(values)

        # restore has been clicked
        if 'attachment_id' in values.keys() and values.get('attachment_id'):

            for record in self.file_manager_id.search([('is_main', '=', True)]):
                if record.is_main:
                    record.is_main = False
            self.file_manager_id.search(
                [('attachment_id', '=', values.get('attachment_id'))]).is_main = True

        # new document or revision
        document = super(DocumentExtend, self).write(values)
        if document:
            in_use = False
            input_value = {
                'documents_id': self.id,
            }
            # revision
            if len(self.file_manager_id) >= 1:
                # check for document lock status continue if possible
                self.is_permitted()
                # lock document temporary
                in_use = self.lock_unlock(True)
                input_value['attachment_id'] = self.attachment_id.id
                # this will be handy in file manager created method
                input_value['revision'] = True
                # global filemanager
                filemanager = False

                if len(self.previous_attachment_ids) > len(self.file_manager_id) - 1:
                    # create file_manager
                    filemanager = self.file_manager_id.create(input_value)
                    # two revision which need to substitute
                    first_current_file_manager = \
                        self.file_manager_id.search(
                            [('attachment_id', '=', self.attachment_id.id)])[0]
                    second_current_file_manager = \
                        self.file_manager_id.search(
                            [('attachment_id', '=', self.attachment_id.id)])[1]
                    # change two object title,comment,tags_ids together
                    first_current_file_manager.title, second_current_file_manager.title = \
                        second_current_file_manager.title, first_current_file_manager.title
                    first_current_file_manager.body, second_current_file_manager.body = \
                        second_current_file_manager.body, first_current_file_manager.body
                    first_current_file_manager.tags_ids, second_current_file_manager.tags_ids = \
                        second_current_file_manager.tags_ids, first_current_file_manager.tags_ids
                    # اضافه کردن مشخصه نوع مستند، پروژه و محصول به مدیریت مستندات (#17)
                    first_current_file_manager.product_template_id, second_current_file_manager.product_template_id =\
                        second_current_file_manager.product_template_id, first_current_file_manager.product_template_id
                    first_current_file_manager.project_project_id, second_current_file_manager.project_project_id =\
                        second_current_file_manager.project_project_id, first_current_file_manager.project_project_id
                    first_current_file_manager.connected_to, second_current_file_manager.connected_to =\
                        second_current_file_manager.connected_to, first_current_file_manager.connected_to
                    first_current_file_manager.category, second_current_file_manager.category =\
                        second_current_file_manager.category, first_current_file_manager.category
                    # اضافه کردن مشخصه نوع مستند، پروژه و محصول به مدیریت مستندات (#17)

                    # change attachment_id previous main file
                    self.file_manager_id[len(self.file_manager_id) - 1].attachment_id = self.previous_attachment_ids[
                        len(self.previous_attachment_ids) - 1]
            # new document is uploaded doesn't need to lock the document
            else:
                input_value['attachment_id'] = self.attachment_id.id
                # this will be handy in file manager created method
                input_value['new'] = True
                # global filemanager
                filemanager = False
                # here ther wasn't any control it made to revision with this control number of ir_attachment and file_manager are equal
                if len(self.previous_attachment_ids) > len(self.file_manager_id) - 1:
                    filemanager = self.file_manager_id.create(input_value)
                    # set main file to show in kanban and list view
                    filemanager.is_main = True
            # check if this method locked the document if yes unlock the document
            if in_use:
                self.lock_unlock(False)
            return self.id

    def unlink(self):
        for record in self:
            # check for permission
            record.is_permitted()
            # check if document has revision or not
            record.has_revision()
        return super(DocumentExtend, self).unlink()

    # check that user has permission to change the document
    # if parameter check_for_admin passed it check admin tries to unlock the file or not it'll happen in document write and unlock situation
    def is_permitted(self, check_for_admin=False):
        # if the user is admin
        if check_for_admin:
            # check to lock then if user who locked the file is not current user
            if self.lock_uid and not (
                    self.env.is_admin() or self.user_has_groups('documents.group_documents_manager')):
                raise Warning(
                    f'Dear {self.env.user.name}\n'
                    f' The {self.attachment_name} is locked by {self.lock_uid.name}\n'
                    f' Ask the system admin or {self.lock_uid.name} to unlock selected file.')

        else:
            # check to lock then if user who locked the file is not current user
            if self.lock_uid and self.env.user != self.lock_uid:
                raise Warning(
                    f'Dear {self.env.user.name}\n'
                    f' The file is locked by {self.lock_uid.name}\n'
                    f' Ask the system admin or {self.lock_uid.name} to unlock selected file.')

    # if status =True passed to method it tries to lock the file if not it tries to unlock the file
    def lock_unlock(self, status: bool):
        # lock file
        if status:
            if not self.lock_uid:
                self.lock_uid = self.env.user
                return True
        # unlock file
        else:
            self.lock_uid = False
        return False

    # check the selected document has revision or not to prevent of deleteing the document which has revision
    def has_revision(self):

        counted_file_manager = self.env['file.manager'].search_count(
            [('documents_id', '=', self.id)]) - 1

        # > 1 because dont count document it self
        if counted_file_manager > 0:
            raise Warning(
                f'Dear {self.env.user.name}\n'
                f'Selected document has {counted_file_manager} revisions')

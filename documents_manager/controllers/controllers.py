# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError
import os
from odoo.tools import image_process
import base64


class FileManager(http.Controller):
    # @http.route('/file_manager/file_manager/', auth='public')
    # def index(self, **kw):
    #     return "Hello, world"

    @http.route(['/file_manager/image/<int:id>', '/file_manager/image/<int:id>/<int:width>x<int:height>', ],
                type='http', auth="public")
    def content_image(self, id=None, field='datas', width=0, height=0, crop=False, share_token=None, unique=False,
                      **kwargs):
        status, headers, image_base64 = self.binary_content(id=id, field=field, share_token=share_token, unique=unique)

        if status != 200:
            return request.env['ir.http']._response_by_status(status, headers, image_base64)

        try:
            image_base64 = image_process(image_base64, size=(int(width), int(height)), crop=crop)
        except Exception:
            return request.not_found()

        if not image_base64:
            return request.not_found()

        content = base64.b64decode(image_base64)
        headers = http.set_safe_image_headers(headers, content)
        response = request.make_response(content, headers)
        response.status_code = status
        return response

    def binary_content(self, id, env=None, field='datas', share_id=None, share_token=None, download=False, unique=False,
                       filename_field='name'):
        env = env or request.env
        record = env['file.manager'].browse(int(id)).attachment_id
        filehash = None

        if not record or not record.exists():
            return (404, [], None)

        # check access right
        try:
            last_update = record['__last_update']
        except AccessError:
            return (404, [], None)

        mimetype = False
        if record.type == 'url' and record.url:
            module_resource_path = record.url
            filename = os.path.basename(module_resource_path)
            status = 301
            content = module_resource_path
        else:
            # field=field removed
            status, content, filename, mimetype, filehash = env['ir.http']._binary_record_content(
                record, filename=None, filename_field=filename_field,
                default_mimetype='application/octet-stream')
        status, headers, content = env['ir.http']._binary_set_headers(
            status, content, filename, mimetype, unique, filehash=filehash, download=download)

        return status, headers, content

#     @http.route('/file_manager/file_manager/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('file_manager.listing', {
#             'root': '/file_manager/file_manager',
#             'objects': http.request.env['file_manager.file_manager'].search([]),
#         })

#     @http.route('/file_manager/file_manager/objects/<model("file_manager.file_manager"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('file_manager.object', {
#             'object': obj
#         })

# -*- coding: utf-8 -*-
{
    'name': "documents_versioing",

    'summary': """ More fucntionality to Document""",

    'description': """
        More fucntionality to Document
    """,

    'author': "Mohammad Saeid Karbaschian",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Productivity/Documents',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'portal', 'web', 'attachment_indexation', 'digest', 'documents','project'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/DocumentsDocument_extend_view.xml',
        'views/FileManager_view.xml',
        'views/assets_extend_view.xml'
    ],
    'qweb': [
        'views/documents_inspector_extended_qweb.xml',
        'views/documents_views_extended_qweb.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}

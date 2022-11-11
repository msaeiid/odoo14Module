# -*- coding: utf-8 -*-
{
    'name': "Approvals Analytic Accounts",

    'summary': """ Consumer remittance request """,

    'description': """
Consumer remittance request
    """,

    'author': "Mohammad Saeid Karbaschian",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Human Resources/Approvals',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['approvals', 'account_accountant', 'stock', 'approvals_purchase'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
}

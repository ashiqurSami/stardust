# -*- coding: utf-8 -*-
{
    'name': "stardust",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
     Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','purchase'],

    # always loaded
    'data': [
        'security/stardust_security.xml',
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/purchase_order_views.xml',
        'views/portal_templates.xml',
        'views/mail_templates.xml',
        'views/res_partner_views.xml',
        'views/res_company_views.xml',
        'report/stardust_purchase_order_report_template.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}


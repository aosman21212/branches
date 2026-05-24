{
    'name': 'Branch Financial Reports',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Profit & Loss, Balance Sheet, Trial Balance and General Ledger filtered by Branch',
    'description': """
Branch Financial Reports
========================

This module allows companies to track journal entries by Branch and provides
four financial report wizards with branch filtering:

* Profit & Loss by Branch
* Balance Sheet by Branch
* Trial Balance by Branch
* General Ledger by Branch

All reports export as PDF using QWeb templates.
    """,
    'author': 'leapai.ai',
    'website': 'https://leapai.ai',
    'license': 'LGPL-3',
    'depends': ['account', 'mail', 'account_reports'],
    'data': [
        'security/branch_security.xml',
        'security/ir.model.access.csv',
        'views/branch_unit_views.xml',
        'views/account_move_views.xml',
        'views/branch_report_wizard_views.xml',
        'views/account_report_branch_enable.xml',
        'reports/branch_report_actions.xml',
        'reports/branch_pl_template.xml',
        'reports/branch_bs_template.xml',
        'reports/branch_tb_template.xml',
        'reports/branch_gl_template.xml',
        'views/branch_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'branch_finance_report/static/src/components/account_report/filters/filter_branch.xml',
        ],
    },
    'demo': [
        'demo/branch_demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

from odoo import models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    branch_id = fields.Many2one(
        'branch.unit',
        string='Branch',
        domain="[('company_id', '=', company_id)]",
        tracking=True,
    )


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    branch_id = fields.Many2one(
        'branch.unit',
        related='move_id.branch_id',
        string='Branch',
        store=True,
        readonly=True,
    )

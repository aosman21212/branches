from odoo import models, fields, api


class BranchUnit(models.Model):
    _name = 'branch.unit'
    _description = 'Branch Unit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'code, name'

    name = fields.Char(string='Branch Name', required=True, tracking=True)
    code = fields.Char(string='Branch Code', required=True, size=10, tracking=True)
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        default=lambda self: self.env.company,
    )
    manager_id = fields.Many2one('res.users', string='Branch Manager')
    street = fields.Char('Street')
    city = fields.Char('City')
    country_id = fields.Many2one('res.country', 'Country')
    phone = fields.Char('Phone')
    email = fields.Char('Email')
    active = fields.Boolean(default=True)
    note = fields.Text('Notes')

    move_count = fields.Integer(
        compute='_compute_move_count',
        string='Journal Entries',
    )

    def _compute_move_count(self):
        for rec in self:
            rec.move_count = self.env['account.move'].search_count(
                [('branch_id', '=', rec.id)]
            )

    def action_view_moves(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Journal Entries',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('branch_id', '=', self.id)],
        }

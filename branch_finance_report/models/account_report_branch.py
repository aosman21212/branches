from odoo import api, fields, models
from odoo.fields import Domain


class AccountReport(models.Model):
    _inherit = 'account.report'

    filter_branch = fields.Boolean(string='Branch Filter', default=False)

    def _init_options_branch(self, options, previous_options):
        """Add branch filter to the standard accounting report options."""
        if not self.filter_branch:
            return

        options['branch'] = True
        previous_branch_ids = previous_options.get('branch_ids') or []
        selected_branch_ids = [int(b) for b in previous_branch_ids]
        selected_branches = (
            self.env['branch.unit'].browse(selected_branch_ids)
            if selected_branch_ids else self.env['branch.unit']
        )
        options['selected_branch_names'] = selected_branches.mapped('name')
        options['branch_ids'] = selected_branches.ids

    @api.model
    def _get_options_branch_domain(self, options):
        """Return a domain to filter aml by branch."""
        if options.get('branch_ids'):
            return Domain('branch_id', 'in', [int(b) for b in options['branch_ids']])
        return Domain.TRUE

    def _get_options_domain(self, options, date_scope):
        domain = super()._get_options_domain(options, date_scope)
        return domain & self._get_options_branch_domain(options)

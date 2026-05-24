from odoo import models, fields, api

REPORT_TYPES = [
    ('profit_loss', 'Profit & Loss'),
    ('balance_sheet', 'Balance Sheet'),
    ('trial_balance', 'Trial Balance'),
    ('general_ledger', 'General Ledger'),
]

INCOME_TYPES = ['income', 'income_other']
EXPENSE_TYPES = [
    'expense', 'expense_other',
    'expense_depreciation', 'expense_direct_cost',
]
ASSET_TYPES = [
    'asset_receivable', 'asset_cash', 'asset_current',
    'asset_non_current', 'asset_prepayments', 'asset_fixed',
]
LIABILITY_TYPES = [
    'liability_payable', 'liability_credit_card',
    'liability_current', 'liability_non_current',
]
EQUITY_TYPES = ['equity', 'equity_unaffected']


class BranchReportWizard(models.TransientModel):
    _name = 'branch.report.wizard'
    _description = 'Branch Financial Report Wizard'

    report_type = fields.Selection(
        REPORT_TYPES,
        string='Report Type',
        required=True,
        default='profit_loss',
    )
    branch_ids = fields.Many2many(
        'branch.unit',
        string='Branches',
        domain="[('company_id', '=', company_id)]",
    )
    date_from = fields.Date(
        string='Start Date',
        required=True,
        default=lambda self: fields.Date.today().replace(month=1, day=1),
    )
    date_to = fields.Date(
        string='End Date',
        required=True,
        default=fields.Date.today,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )
    journal_ids = fields.Many2many('account.journal', string='Journals')
    account_ids = fields.Many2many('account.account', string='Accounts (filter)')
    include_unposted = fields.Boolean('Include Draft Entries', default=False)

    # ── Domain helpers ──────────────────────────────────────────────────

    def _get_domain(self):
        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('company_id', '=', self.company_id.id),
        ]
        if not self.include_unposted:
            domain.append(('move_id.state', '=', 'posted'))
        if self.branch_ids:
            domain.append(('branch_id', 'in', self.branch_ids.ids))
        if self.journal_ids:
            domain.append(('journal_id', 'in', self.journal_ids.ids))
        if self.account_ids:
            domain.append(('account_id', 'in', self.account_ids.ids))
        return domain

    # ── Print action ────────────────────────────────────────────────────

    def action_print_report(self):
        report_map = {
            'profit_loss': 'branch_finance_report.action_branch_pl_report',
            'balance_sheet': 'branch_finance_report.action_branch_bs_report',
            'trial_balance': 'branch_finance_report.action_branch_tb_report',
            'general_ledger': 'branch_finance_report.action_branch_gl_report',
        }
        return self.env.ref(report_map[self.report_type]).report_action(self)

    # ── Profit & Loss data ──────────────────────────────────────────────

    def get_pl_data(self):
        domain = self._get_domain()
        lines = self.env['account.move.line'].search(domain)

        income_lines = lines.filtered(
            lambda l: l.account_id.account_type in INCOME_TYPES
        )
        expense_lines = lines.filtered(
            lambda l: l.account_id.account_type in EXPENSE_TYPES
        )

        def group_income(move_lines):
            result = {}
            for line in move_lines:
                acc = line.account_id
                key = acc.id
                if key not in result:
                    result[key] = {
                        'account': acc.name,
                        'code': acc.code,
                        'balance': 0.0,
                    }
                result[key]['balance'] += (line.credit - line.debit)
            return sorted(result.values(), key=lambda x: x['code'])

        def group_expense(move_lines):
            result = {}
            for line in move_lines:
                acc = line.account_id
                key = acc.id
                if key not in result:
                    result[key] = {
                        'account': acc.name,
                        'code': acc.code,
                        'balance': 0.0,
                    }
                result[key]['balance'] += (line.debit - line.credit)
            return sorted(result.values(), key=lambda x: x['code'])

        income_data = group_income(income_lines)
        expense_data = group_expense(expense_lines)

        total_income = sum(d['balance'] for d in income_data)
        total_expense = sum(d['balance'] for d in expense_data)
        net_profit = total_income - total_expense

        branches = ', '.join(self.branch_ids.mapped('name')) if self.branch_ids else 'All Branches'
        return {
            'income': income_data,
            'expense': expense_data,
            'total_income': total_income,
            'total_expense': total_expense,
            'net_profit': net_profit,
            'branches': branches,
        }

    # ── Balance Sheet data ──────────────────────────────────────────────

    def get_bs_data(self):
        # Balance sheet uses ALL posted entries up to date_to (cumulative)
        domain = [
            ('date', '<=', self.date_to),
            ('company_id', '=', self.company_id.id),
            ('move_id.state', '=', 'posted'),
        ]
        if self.branch_ids:
            domain.append(('branch_id', 'in', self.branch_ids.ids))

        lines = self.env['account.move.line'].search(domain)

        def group_lines(move_lines, types, sign=1):
            result = {}
            for line in move_lines:
                if line.account_id.account_type not in types:
                    continue
                acc = line.account_id
                key = acc.id
                if key not in result:
                    result[key] = {
                        'account': acc.name,
                        'code': acc.code,
                        'balance': 0.0,
                    }
                result[key]['balance'] += sign * (line.debit - line.credit)
            return sorted(result.values(), key=lambda x: x['code'])

        asset_data = group_lines(lines, ASSET_TYPES, sign=1)
        liability_data = group_lines(lines, LIABILITY_TYPES, sign=-1)
        equity_data = group_lines(lines, EQUITY_TYPES, sign=-1)

        total_assets = sum(d['balance'] for d in asset_data)
        total_liabilities = sum(d['balance'] for d in liability_data)
        total_equity = sum(d['balance'] for d in equity_data)

        branches = ', '.join(self.branch_ids.mapped('name')) if self.branch_ids else 'All Branches'
        return {
            'assets': asset_data,
            'liabilities': liability_data,
            'equity': equity_data,
            'total_assets': total_assets,
            'total_liabilities': total_liabilities,
            'total_equity': total_equity,
            'total_liab_equity': total_liabilities + total_equity,
            'branches': branches,
        }

    # ── Trial Balance data ──────────────────────────────────────────────

    def get_tb_data(self):
        domain = self._get_domain()
        lines = self.env['account.move.line'].search(domain)

        result = {}
        for line in lines:
            acc = line.account_id
            key = acc.id
            if key not in result:
                result[key] = {
                    'account': acc.name,
                    'code': acc.code,
                    'type': acc.account_type,
                    'debit': 0.0,
                    'credit': 0.0,
                }
            result[key]['debit'] += line.debit
            result[key]['credit'] += line.credit

        rows = sorted(result.values(), key=lambda x: x['code'])
        for row in rows:
            row['balance'] = row['debit'] - row['credit']

        total_debit = sum(r['debit'] for r in rows)
        total_credit = sum(r['credit'] for r in rows)
        total_balance = total_debit - total_credit

        branches = ', '.join(self.branch_ids.mapped('name')) if self.branch_ids else 'All Branches'
        return {
            'rows': rows,
            'total_debit': total_debit,
            'total_credit': total_credit,
            'total_balance': total_balance,
            'branches': branches,
        }

    # ── General Ledger data ─────────────────────────────────────────────

    def get_gl_data(self):
        domain = self._get_domain()
        lines = self.env['account.move.line'].search(
            domain, order='account_id, date, id'
        )

        accounts = {}
        for line in lines:
            acc = line.account_id
            key = acc.id
            if key not in accounts:
                accounts[key] = {
                    'account': acc.name,
                    'code': acc.code,
                    'lines': [],
                    'total_debit': 0.0,
                    'total_credit': 0.0,
                }
            accounts[key]['lines'].append({
                'date': line.date,
                'move': line.move_id.name,
                'partner': line.partner_id.name or '',
                'label': line.name or '',
                'branch': line.branch_id.name or '',
                'debit': line.debit,
                'credit': line.credit,
                'balance': line.debit - line.credit,
            })
            accounts[key]['total_debit'] += line.debit
            accounts[key]['total_credit'] += line.credit

        result = sorted(accounts.values(), key=lambda x: x['code'])
        for acc in result:
            acc['total_balance'] = acc['total_debit'] - acc['total_credit']

        branches = ', '.join(self.branch_ids.mapped('name')) if self.branch_ids else 'All Branches'
        return {
            'accounts': result,
            'branches': branches,
        }

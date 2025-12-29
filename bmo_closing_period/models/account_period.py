from datetime import datetime
from dateutil.relativedelta import relativedelta
import odoo
from odoo import api, models, _, fields
from odoo.osv import expression
from odoo.exceptions import ValidationError

state_status = []
state_period = [('draft', 'Open'), ('done', 'Closed')]

class account_fiscalyear(models.Model):
    _name = "account.fiscalyear"
    _description = "Closing Period"
    _order = "date_start desc, id"

    name = fields.Char(
        'Fiscal Year', required=True)
    code = fields.Char(
        'Code', size=6, required=True)
    interval = fields.Char(
        'Interval')
    company_id = fields.Many2one(
        'res.company', 'Company', required=True, default=lambda self: self.env.user.company_id)
    date_start = fields.Date(
        'Start Date', required=True)
    date_stop = fields.Date(
        'End Date', required=True)
    state = fields.Selection(
        state_period, 'Status', readonly=True, copy=False, default='draft')
    type = fields.Selection(state_status, string='Type', required=False)
    period_ids = fields.One2many(
        'account.period', 'fiscalyear_id', 'Periods')
    closing_period_models_line = fields.One2many(comodel_name='closing.period.models', inverse_name='fiscalyear_id', string='Closing Period Models')
    
    @api.onchange('company_id')
    def _onchange_company_date(self):
        for budget in self:
            year_now = datetime.now().strftime('%Y')
            self.date_start = datetime(int(year_now), 1, 1)
            self.date_stop = self.date_start + relativedelta(months=12) - relativedelta(days=1)

    def update_models_closing(self):
        period_models_obj = self.env['closing.period.models']
        for rec in self:
            if rec.period_ids:
                for line in rec.period_ids:
                    if line.closing_period_models_line:
                        line.closing_period_models_line.unlink()
                    for i in rec.closing_period_models_line:
                        period_models_obj.create({
                            'model_id'          : i.model_id.id,
                            'field_id'          : i.field_id.id,
                            'period_id'         : line.id,
                            'state'             : 'done',
                        })
                    line.action_done()

    def action_done(self):
        for period in self:
            for line in period.period_ids:
                line.action_done()
            period.write({'state': 'done'})
        return True
    
    def action_draft(self):
        for period in self:
            period.write({'state': 'draft'})
        return True


    def create_period(self):
        if not hasattr(self,'interval'):
            self.interval = 1
        period_obj = self.env['account.period']
        for fy in self.browse(self.ids):
            if not fy.period_ids:
                ds = fy.date_start
                period_obj.create({
                        'name'          :  "%s %s" % (_('Opening Period'), ds.strftime('%Y')),
                        'code'          : ds.strftime('00/%Y'),
                        'date_start'    : ds,
                        'date_stop'     : ds,
                        'special'       : True,
                        'fiscalyear_id' : fy.id,
                        'state'         : 'done',
                    })
                date = fy.date_stop.month - ds.month
                for x in range(date+1):
                    de = ds + relativedelta(months=1) - relativedelta(days=1)
                    period_obj.create({
                        'name'          : ds.strftime('%m/%Y'),
                        'code'          : ds.strftime('%m/%Y'),
                        'date_start'    : ds.strftime('%Y-%m-%d'),
                        'date_stop'     : de.strftime('%Y-%m-%d'),
                        'fiscalyear_id' : fy.id,
                        'state'         : 'done',
                    })
                    ds = ds + relativedelta(months=1) 
                period_obj.create({
                    'name'          :  "%s %s" % (_('Ending Period'), de.strftime('%Y')),
                    'code'          : de.strftime('13/%Y'),
                    'date_start'    : ds - relativedelta(months=1),
                    'date_stop'     : de.strftime('%Y-%m-%d'),
                    'special'       : True,
                    'fiscalyear_id' : fy.id,
                    'state'         : 'done',
                })
            else:
                account_fiscal_obj = self.env['account.fiscal.year']
                company_all = self.env['res.company'].sudo().search([])
                for com in company_all:
                    account_fiscal_src = account_fiscal_obj.sudo().search([('company_id','=',com.id),('fiscalyear_id','=',fy.id)])
                    if not account_fiscal_src:
                        account_fiscal_obj.create({
                            'name'          : fy.name,
                            'date_from'     : fy.date_start,
                            'date_to'       : fy.date_stop,
                            'company_id'    : com.id,
                            'fiscalyear_id' : fy.id,
                        })
                    else:
                        account_fiscal_src.write({
                            'name'          : fy.name,
                            'date_from'     : fy.date_start,
                            'date_to'       : fy.date_stop,
                        })
            return True

class AccountFiscalYear(models.Model):
    _inherit = 'account.fiscal.year'

    fiscalyear_id = fields.Many2one('account.fiscalyear', 'Fiscal Year', index=True)

class AccountPeriod(models.Model):
    _name = "account.period"
    _description = "Closing Period Detail"
    _order = "code, special desc"

    name = fields.Char('Period Name', required=True)
    code = fields.Char('Code', size=12)
    special = fields.Boolean('Opening/Closing Period', help="These periods can overlap.")
    date_start = fields.Date('Start of Period', required=True,) 
        # states={'done': [('readonly', True)]})
    date_stop = fields.Date('End of Period', required=True,)
        # states={'done': [('readonly', True)]})
    fiscalyear_id = fields.Many2one('account.fiscalyear', 'Fiscal Year', ondelete='cascade', required=True,) 
        # states={'done': [('readonly', True)]}, index=True)
    state = fields.Selection(state_period, 'Status', readonly=True, copy=False, default='draft', help='When monthly periods are created. The status is \'Draft\'. At the end of monthly period it is in \'Done\' status.')
    company_id = fields.Many2one('res.company', related='fiscalyear_id.company_id', string='Company', store=True, readonly=True)
    type = fields.Selection(state_status, string='Type', required=False)
    user_ids = fields.Many2many(comodel_name='res.users', string='Allowed Users')
    closing_period_models_line = fields.One2many(comodel_name='closing.period.models', required=True, inverse_name='period_id', string='Closing Period Models')
    
    _sql_constraints = [
        ('name_company_uniq', 'unique(name, company_id)', 'The name of the period must be unique per company!'),
    ]

    
    def _check_duration(self):
        for period in self:
            if period.date_stop < period.date_start:
                return False
        return True

    
    def _check_year_limit(self):
        for period in self:
            if period.fiscalyear_id.date_stop < period.date_stop or \
               period.fiscalyear_id.date_stop < period.date_start or \
               period.fiscalyear_id.date_start > period.date_start or \
               period.fiscalyear_id.date_start > period.date_stop:
                return False
        return True

    @api.model
    def find(self, date=None):
        if not date:
            date = fields.Date.today(self)
            
        args = [('date_start', '<=', date), ('date_stop', '>=', date)]
        result = self.search(args, limit=1)
        if not result:
            result = False        
        return result

    @api.model
    def find_models(self, date=None, company_id=None, models=None):
        if not date:
            date = fields.Date.today(self)

        if not company_id:
            company_id = self.env.user.company_id.id
            
        result = self.find(date)
        msg = 'Not Models'
        if result:
            domain = [('period_id', '=', result.id), ('model_id', '=', models)]
            model_closing = self.env['closing.period.models'].sudo().search(domain, limit=1)
            if self.env.user.id in result.user_ids.ids:
                msg = 'success'
            elif model_closing:
                msg = 'success'
                if model_closing.state == 'done':
                    result = False
            else:
                msg = 'You cannot posted the journal, please re-open periods'
                result = False

        return result, msg
    
    def action_draft(self):
        for period in self:
            if period.fiscalyear_id.state == 'done':
                raise ValidationError(("Period cannot be opened again because the fiscal year has closed."))
            for line in period.closing_period_models_line:
                line.write({'state': 'draft'})
            period.write({'state': 'draft'})
        return True

    def action_done(self):
        for period in self:
            for line in period.closing_period_models_line:
                # journal_entries = self.env['account.move.line'].sudo().search(
                #     [
                #         ('parent_state','=','draft'), ('date', '>=', period.date_start), ('date', '<=', period.date_stop)
                #     ]
                # )
                # if journal_entries:
                #     raise ValidationError(_("There are journal entries in the period %s that are not posted. Please post them before closing the period.") % period.name)
                line.write({'state': 'done'})
            period.write({'state': 'done'})
        return True

    # @api.model
    # def name_search(self, name, args=None, operator='ilike', limit=100):
    #     args = args or []
    #     domain = ['|', ('code', operator, name), ('name', operator, name)]
    #     recs = self.search(domain + args, limit=limit)
    #     return recs.name_get()

class ClosingPeriodModels(models.Model):
    _name = "closing.period.models"
    _description = "Closing Period Models"

    fiscalyear_id = fields.Many2one('account.fiscalyear', 'Fiscal Year')
    company_id = fields.Many2one('res.company', 'Company', required=True)
    period_id = fields.Many2one('account.period', 'Period', index=True, ondelete='cascade')
    model_id = fields.Many2one(comodel_name="ir.model", string="Model", required=False, copy=False)
    model_name = fields.Char(string="Model Technical Name", related='model_id.model', store=True)
    field_id = fields.Many2one(comodel_name="ir.model.fields", string="Field", required=False)
    state = fields.Selection(state_period, 'Status', readonly=False, copy=False, default='draft')
    state_period = fields.Selection(related='period_id.state', string="Status Period", store=True)
    name_fy = fields.Char(compute='_compute_state_fy', string='Name Fiscal Years', store=True)
    state_fy = fields.Selection([('draft', 'Open'), ('done', 'Closed')], compute='_compute_state_fy', string='Status Fiscal Years', store=True)
    
    @api.depends('period_id', 'period_id.fiscalyear_id', 'period_id.fiscalyear_id.state')
    def _compute_state_fy(self):
        for line in self:
            if line.period_id and line.period_id.fiscalyear_id:
                line.state_fy = line.period_id.fiscalyear_id.state
                line.name_fy = line.period_id.fiscalyear_id.name
            else:
                line.state_fy = ''
                line.name_fy = ''
                
    
    def generate_fields(self):
        # TODO next version: handle case if there is module update and will add generated field
        if not hasattr(self.env[self.model_name], 'x_period_id'):
            field_obj = self.env['ir.model.fields']
            field_obj.create([
                {
                    'name': 'x_period_id',
                    'field_description': 'Period',
                    'model_id': self.model_id.id,
                    'ttype': 'many2one',
                    'relation' : 'account.period',
                    'index' : True,
                    'required': False,
                    'readonly': True,
                    'copied': False,
                }
            ])

    @api.model_create_multi
    def create(self, vals):
        for vals in vals:
            res = super(ClosingPeriodModels, self).create(vals)
        res.sudo().generate_fields()
        return res

    def write(self, vals):
        res = super(ClosingPeriodModels, self).write(vals)
        field_to_check = ['model_id']
        if list(set(field_to_check).intersection(vals.keys())):
            for rec in self:
                rec.sudo().generate_fields()
        return res
    
    def action_open(self):
        for line in self:
            line.write({'state' : 'draft'})
    
    def action_close(self):
        for line in self:
            line.write({'state' : 'done'})

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    x_period_id = fields.Many2one(comodel_name='account.period', string='Period')
    
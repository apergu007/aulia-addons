# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import date
import logging
_logger = logging.getLogger(__name__)


exlude_list_models = [
    'ir.ui.menu','ir.module.module', 'ir.ui.menu', 'ir.ui.view', 'base_import.import', 'ir.attachment',
    'ir.rule', 'res.users','change.password.user','base.module.uninstall',
    'ir.model.access','mail.message','mail.message.schedule','mail.tracking.value',
    'res.lang','base.language.import','base.language.export','mail.mail','mail.guest','ir.cron','mail.notification','zactivity.type',
    'zactivity.rate.sheet', 'ir.property', 'bus.bus', 'mail.followers', 'ir.sequence.date_range', 'account.edi.document', 'res.users.log',
    'mail.channel.member', 'mail.channel', 'res.users.settings', 'bus.presence','web.progress', 'hr.payroll.structure.type', 'ir.actions.act_window.view',
    'stock.location', 'stock.picking.type', 'res.company', 'module.update_list', 'module.button_upgrade', 'module.button_install', 'ir.actions.act_window',
    ' module.update_list', 'module.button_upgrade','module.button_install', 'studio.mixin', 'studio.approval.rule', 'dynamic.approval.wizard', 'Bus.loop',
    'studio.approval.request',
]

class BaseClosePeriod(models.AbstractModel):
    _inherit = 'base'

    def _get_zclosing_period(self, date, company_id, models):
        period, msg = self.env['account.period'].find_models(date=date, company_id=company_id, models=models)
        if period:
            period = period.id
        if not period and msg == 'success':
            raise ValidationError(('There is no period defined for this date: %s.\nPlease go to Configuration/Periods.' % date))
        elif not period:
            raise ValidationError(('%s' % msg))
        return period

    def write(self, vals):
        for rec in self:
            if rec._name not in exlude_list_models:
                model_id = self.env['ir.model'].sudo().search([('model', '=', rec._name)])
                model_closing = self.env['closing.period.models'].sudo().search([('model_id', '=', model_id.id)], limit=1)
                if model_closing and model_closing.field_id:
                    if rec._name == 'account.move' and 'state' in vals:
                        if rec.state != vals.get("state"):
                            for line in rec.line_ids:
                                period_id = self._get_zclosing_period(date=line.date, company_id=line.company_id.id, models=model_id.id)
                                line.sudo().write({'x_period_id' : period_id})
                        else:
                            continue
                    else:
                        field_name = model_closing.field_id.name
                        if rec._name != 'account.move':
                            if field_name in vals or rec.state != vals.get("state"):
                                date_record = rec.search_read([('id', '=', rec.id)], [field_name,'company_id'])
                                if date_record:
                                    record_date = vals.get(field_name)
                                    record_company_id = rec.company_id.id
                                else:
                                    record_date = date.today()
                                    record_company_id = self.env.user.company_id.id
                                vals['x_period_id'] = self._get_zclosing_period(date=record_date, company_id=record_company_id, odels=model_id.id)

        return super().write(vals)
    
    
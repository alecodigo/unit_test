# -*- coding: utf-8 -*-


from odoo import api, fields, models, _



class Lead(models.Model):
    _inherit = 'crm.lead'


    @api.model
    def create(self, vals):
        # This code block is added by Odoolibre
        seq = self.env['ir.sequence'].next_by_code('crm.lead') or _('New')
        vals['name'] = seq

        # set up used to find the lead's Sale Team which is needed
        # to correctly set the default stage_id
        context = dict(self._context or {})
        if vals.get('type') and not self._context.get('default_type'):
            context['default_type'] = vals.get('type')
        if vals.get('team_id') and not self._context.get('default_team_id'):
            context['default_team_id'] = vals.get('team_id')

        if vals.get('user_id') and 'date_open' not in vals:
            vals['date_open'] = fields.Datetime.now()

        partner_id = vals.get('partner_id') or context.get('default_partner_id')
        onchange_values = self._onchange_partner_id_values(partner_id)
        onchange_values.update(vals) # we don't want to overwirte any existing key
        vals = onchange_values
        return super(Lead, self.with_context(context,mail_create_nolog=True)).create(vals)






class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'


    parent = fields.Many2one('sale.order.line', string='Parent')
    child = fields.Boolean(string='Child')





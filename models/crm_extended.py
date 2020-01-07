# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


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



class SaleOrderNew(models.Model):
    _inherit = 'sale.order'

    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True, store=True, default=lambda self: _('Order'))
    parent_id = fields.Many2one('sale.order', string='Parent')
    child = fields.Boolean(string='Child')


    @api.multi
    def confirm_variant(self):
        records_id = self.env['sale.order'].search([('parent_id', '=', self.parent_id.id),('child', '=', True)])
        for record in records_id:
            record.write({'state': 'cancel'})


    @api.multi
    def _action_confirm(self):
        if self.child:
            raise UserError(_("Budget variants cannot be confirmed. Before confirm this variant"))
        else:
            return super()._action_confirm()



    @api.multi
    def variante(self):
        self.ensure_one()
        action = self.env.ref('crm_sale.sale_order_variant').read()[0]   

        return action



    @api.model
    def create(self, vals):

        # El campo child No esta establecido
        if vals['child'] == False:
            _logger.info("\n\n\nSe ejecuto el ir.sequence modificado\n\n")
            #if result.name == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('sale.order')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('sale.order')
            _logger.info("\n\n vals tiene: %s \n\n", vals)
            result = super().create(vals)
            _logger.info("\n\n\n result: %s \n\n\n", result.name)
            return result
        
        #El campo child esta establecido
        else:
            
            #parent = self.search([('parent_id', '=', self.parent_id.id),('child', '=', False)], limit=1)
            idx = vals['parent_id']
            _logger.info("\n\n id is %s\n\n", idx)
            parent = self.browse(idx)
            account = self.search_count([('parent_id', '=', idx),('child', '=', True)])
            _logger.info("\n\n parent is: %s\n\n", parent)
            _logger.info("\n\n parent name is: %s\n\n", parent.name)
            _logger.info("\n\n account is: %s\n\n", account)
            if parent and (account > 0):

                vals['name'] = parent.name + "/" + str(account + 1)
                return super().create(vals)
            
            else:
                vals['name'] = parent.name + "/" + "1"
                return super().create(vals)






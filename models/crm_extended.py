# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class Lead(models.Model):
    _inherit = 'crm.lead'


    @api.multi
    def action_set_won_rainbowman(self):
        self.ensure_one()
        if self.sale_number:
            super().action_set_won_rainbowman()
        else:
            raise UserError(_("You need to create an opportunity first."))


    @api.model
    def create(self, vals):
        # This code block is added by Odoolibre
        seq = self.env['ir.sequence'].next_by_code('crm.lead')
        vals['name'] = seq

        result = super().create(vals)
        
        return result


class SaleOrderNew(models.Model):
    _inherit = 'sale.order'


    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True, store=True, default=lambda self: _('Order'))
    parent_id = fields.Many2one('sale.order', string='Parent')
    child = fields.Boolean(string='Child')
    flag_child = fields.Boolean(string='Child')
    confirmed = fields.Boolean(string='Confirmed')
    child_passed = fields.Char(string='Child passed')


    @api.multi
    def action_draft(self):
        """ Sale order variant can't not be send to sale order draft again."""
        if self.child and self.confirmed:
            raise UserError(_("The sale order variant is confirmed."))
        else:
            return super().action_draft()


    @api.multi
    def confirm_variant(self):
        data = {}
        """ This function cancel everything variant and confirm the 
        variant sale order selected. """
        
        self.confirmed = True
        
        # testear que pasa si records_id es False
        # stage 1 cancel all child records
        records_id = self.env['sale.order'].search([('parent_id', '=', self.parent_id.id),('child', '=', True)])
        for record in records_id:
            record.write({'state': 'cancel'})
        
        # stage 2 search the father record
        parent_id = self.env['sale.order'].search([('id', '=', self.parent_id.id),('child', '=', False)]) 
        

        if self.order_line:
            res = []
            
            #parent_id = self.env['sale.order'].search([('id', '=', self.parent_id.id),('child', '=', False)]) 
            if self.order_line.tax_id:
                val = []
                for i in self.order_line.tax_id:
                    val.append((0,0, {'tax_id': i.id}))
            for item in self.order_line:
                res.append((0,0, {
                            'product_id': item.product_id.id,
                            'name': item.name,
                            'product_uom_qty': item.product_uom_qty,
                            'price_unit': item.price_unit,
                            #'tax_id': self.order_line.tax_id.id,
                            'price_subtotal': item.price_subtotal,

                }))
            data.update({'tax_id': val, 'child_passed': self.name})
            data.update({'order_line': res})
            parent_id.write(data)


    @api.multi
    def _action_confirm(self):
        if self.child:
            raise UserError(_("Budget variants cannot be confirmed. Before confirm this variant"))
        else:
            return super()._action_confirm()


    @api.multi
    def variante(self, context):
        #self.ensure_one()
        res = []
        action = self.env.ref('crm_sale.action_sale_order_variant').read()[0]

        if self.order_line:

            val = []
            for line in self.order_line:
                for tax in line.tax_id:
                    val.append((0,0, {'tax_id': tax.id})) 

            for item in self.order_line:
                res.append((0,0, {
                            'product_id': item.product_id.id,
                            'name': item.name,
                            'product_uom_qty': item.product_uom_qty,
                            'price_unit': item.price_unit,
                            'tax_id': val,
                            'price_subtotal': item.price_subtotal,
                }))



        action['context'] = {
            
            'default_parent_id': self.id,
            'default_partner_id': self.partner_id.id, 

            'default_child': True,
            'default_flag_child': True,
            'default_order_line': res,
            'default_note' : self.note,

            'default_client_order_ref': self.client_order_ref,

            'default_fiscal_position_id': self.fiscal_position_id,

            'default_origin': self.origin,
            'default_campaign_id': self.campaign_id.id,
            'default_medium_id': self.medium_id.id,
            'default_source_id': self.source_id.id,
            'default_opportunity_id': self.opportunity_id.id,
        }

        _logger.info("\n\n action['context'] {} \n\n".format(action['context']))

        return action



    @api.model
    def create(self, vals):

        # El campo child No esta establecido
        if vals['child'] == False:
            #if result.name == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('sale.order')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('sale.order')
            result = super().create(vals)
            return result
        
        #El campo child esta establecido
        else:
            
            #parent = self.search([('parent_id', '=', self.parent_id.id),('child', '=', False)], limit=1)
            idx = vals['parent_id']
            parent = self.browse(idx)
            account = self.search_count([('parent_id', '=', idx),('child', '=', True)])
            if parent and (account > 0):

                vals['name'] = parent.name + "/" + str(account + 1)
                return super().create(vals)
            
            else:
                vals['name'] = parent.name + "/" + "1"
                return super().create(vals)






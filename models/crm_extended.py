# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError



class Lead(models.Model):
    _inherit = 'crm.lead'


    @api.multi
    def action_set_won_rainbowman(self):
        self.ensure_one()
        if self.sale_number:
            super().action_set_won_rainbowman()
        else:
            raise UserError(_("You need to create an order sale first."))


    @api.model
    def create(self, vals):
        # This code block is added by Odoolibre
        seq = self.env['ir.sequence'].next_by_code('crm.lead')
        vals['name'] = seq

        result = super().create(vals)
        
        return result


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    id_inherit = fields.Integer(string='id_inherit')


class SaleOrderNew(models.Model):
    _inherit = 'sale.order'


    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True, store=True, default=lambda self: _('Order'))
    parent_id = fields.Many2one('sale.order', string='Parent')
    child = fields.Boolean(string='Child')
    flag_child = fields.Boolean(string='Child')
    confirmed = fields.Boolean(string='Confirmed')
    child_passed = fields.Char(string='Child passed')
    measure_date = fields.Date(string='Date Measure')
    deploy_date = fields.Date(string='Date of Production')


    @api.multi
    def action_draft(self):
        """ Sale order variant can't not be send to sale order draft again."""
        if self.child and self.confirmed:
            raise UserError(_("The sale order variant is confirmed."))
        else:
            return super().action_draft()


    @api.multi
    def confirm_variant(self):
        """ This function cancel everything variant and confirm the 
        variant sale order selected. """
        
        data = {}
        
        records_id = self.env['sale.order'].search([('parent_id', '=', self.parent_id.id),('child', '=', True)])
        if records_id:
            for record in records_id:
                record.write({'state': 'cancel'})
        
        # stage 2 search the parent record
        parent = self.env['sale.order'].search([('id', '=', self.parent_id.id),('child', '=', False)]) 

        if parent:
            if self.order_line:
                res = []
                for item in self.order_line:
                    # update
                    parent_id = self.env['sale.order'].browse(self.parent_id.id).order_line.ids
                    if item.id_inherit in parent_id:
                        res.append((1,item.id_inherit, {
                            'product_id': item.product_id.id,
                            'name': item.name,
                            'product_uom_qty': item.product_uom_qty,
                            'price_unit': item.price_unit,
                            #'tax_id': vals,
                            'price_subtotal': item.price_subtotal,
                        }))
                    else:
                        # create a new record
                        res.append((0,0, {
                                'product_id': item.product_id.id,
                                'name': item.name,
                                'product_uom_qty': item.product_uom_qty,
                                'price_unit': item.price_unit,
                                #'tax_id': vals,
                                'price_subtotal': item.price_subtotal,
                            }))

        data.update({
                       'order_line': res or False, 
                       'child_passed': self.name,
                       'note': self.note,
                       'tag_ids': [(6, 0, self.tag_ids.ids)],
                       'client_order_ref': self.client_order_ref,
                       'date_order': self.date_order,
                       'fiscal_position_id': self.fiscal_position_id,

                       'origin': self.origin,
                       'campaign_id': self.campaign_id.id,
                       'medium_id': self.medium_id.id,
                       'source_id': self.source_id.id,
                       'opportunity_id': self.opportunity_id.id,

                       })

        parent.write(data)

        self.confirmed = True



    @api.multi
    def _action_confirm(self):
        if self.child:
            raise UserError(_("Budget variants cannot be confirmed. Before confirm this variant"))
        else:
            return super()._action_confirm()


    @api.multi
    def create_variant(self, context):
        """This method create a new sale order variant."""
        res = []
        action = self.env.ref('crm_sale.action_sale_order_variant').read()[0]

        if self.order_line:


            for item in self.order_line:
                res.append((0,0, {
                            'id_inherit': item.id,
                            'product_id': item.product_id.id,
                            'name': item.name,
                            'product_uom_qty': item.product_uom_qty,
                            'price_unit': item.price_unit,
                            #'tax_id': [(6,0, item.tax_id.ids)],
                            'price_subtotal': item.price_subtotal,
                            'product_uom': item.product_uom.id,
                }))
  
        action['context'] = {
            
            'default_parent_id': self.id,
            'default_partner_id': self.partner_id.id, 

            'default_child': True,
            'default_flag_child': True,
            'default_order_line': res,
            'default_note': self.note,

            'default_tag_ids': [(6, 0, self.tag_ids.ids)],
            'default_client_order_ref': self.client_order_ref,

            'default_date_order': self.date_order,
            'default_fiscal_position_id': self.fiscal_position_id,

            'default_origin': self.origin,
            'default_campaign_id': self.campaign_id.id,
            'default_medium_id': self.medium_id.id,
            'default_source_id': self.source_id.id,
            'default_opportunity_id': self.opportunity_id.id,
        }
        

        return action



    @api.model
    def create(self, vals):

        # El campo child No esta establecido
        if vals['child'] == False:
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('sale.order')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('sale.order')
            result = super().create(vals)
            return result
        
        else:            
            idx = vals['parent_id']
            parent = self.browse(idx)
            account = self.search_count([('parent_id', '=', idx),('child', '=', True)])
            if parent and (account > 0):

                vals['name'] = parent.name + "/" + str(account + 1)
                return super().create(vals)
            
            else:
                vals['name'] = parent.name + "/" + "1"
                return super().create(vals)






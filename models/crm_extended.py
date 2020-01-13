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
        
        self.confirmed = True
        
        # testear que pasa si records_id es False
        # stage 1 cancel all child records
        records_id = self.env['sale.order'].search([('parent_id', '=', self.parent_id.id),('child', '=', True)])
        if records_id:
            for record in records_id:
                record.write({'state': 'cancel'})
        
        # stage 2 search the parent record
        parent = self.env['sale.order'].search([('id', '=', self.parent_id.id),('child', '=', False)]) 
        _logger.info("\n\n partner_id.order_line %s\n\n", parent.order_line)
        
        # stage 3 si es verdadero comienzo a verificar 
        # si actualizo o creo un registro
        # verifico si existe en verdad un registro padre
        if parent:
            if self.order_line:
                res = []    
                vals = []
                for line in self.order_line:
                    for tax in line.tax_id:
                        vals.append((0,0, {'tax_id': tax.id})) 

                for item in self.order_line:
                    _logger.info("\n\n item.id_inherit %s\n\n",item.id_inherit)
                    # update
                    if item.id_inherit > 0:
                        res.append((1,item.id_inherit, {
                            'product_id': item.product_id.id,
                            'name': item.name,
                            'product_uom_qty': item.product_uom_qty,
                            'price_unit': item.price_unit,
                            #'tax_id': vals,
                            'price_subtotal': item.price_subtotal,
                        }))
                    # creo el registro nuevo
                    else:
                        res.append((0,0, {
                            'product_id': item.product_id.id,
                            'name': item.name,
                            'product_uom_qty': item.product_uom_qty,
                            'price_unit': item.price_unit,
                            #'tax_id': vals,
                            'price_subtotal': item.price_subtotal,
                        }))


        #data.update({'tax_id': val or False, 'child_passed': self.name})
        data.update({
                       'order_line': res or False, 
                       'child_passed': self.name,
                       'note': self.note,
                       #'tag_ids': tags,
                       'client_order_ref': self.client_order_ref,
                       'date_order': self.date_order,
                       'fiscal_position_id': self.fiscal_position_id,

                       'origin': self.origin,
                       'campaign_id': self.campaign_id.id,
                       'medium_id': self.medium_id.id,
                       'source_id': self.source_id.id,
                       'opportunity_id': self.opportunity_id.id,

                       })

        _logger.info("Que mas contiene data %s", data)
        parent.write(data)



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

        _logger.info("\n\n product_uom %s\n\n", self)
        if self.order_line:

            val = []
            for line in self.order_line:
                for tax in line.tax_id:
                    val.append((0,0, {'tax_id': tax.id})) 

            for item in self.order_line:
                res.append((0,0, {
                            'id_inherit': item.id,
                            'product_id': item.product_id.id,
                            'name': item.name,
                            'product_uom_qty': item.product_uom_qty,
                            'price_unit': item.price_unit,
                            'tax_id': val,
                            'price_subtotal': item.price_subtotal,
                            'product_uom': item.product_uom.id,
                }))
            _logger.info("\n\n res %s\n\n", res)

        tags = []
        for tag in self.tag_ids:
            tags.append((0,0, {'tag_ids': tag.id}))


        action['context'] = {
            
            'default_parent_id': self.id,
            'default_partner_id': self.partner_id.id, 

            'default_child': True,
            'default_flag_child': True,
            'default_order_line': res,
            'default_note': self.note,

            'tag_ids': tags,
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






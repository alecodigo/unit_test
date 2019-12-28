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

    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True, store=True, default=lambda self: _('New'))
    parent_id = fields.Many2one('sale.order', string='Parent')
    child = fields.Boolean(string='Child')


    @api.multi
    @api.onchange('parent_id', 'child')
    def _sequence_for_variant(self):
        if self.parent_id and self.child:
            orders = self.search_count([('parent_id', '=', self.parent_id.id),('child', '=', True)])
            if orders:
                _logger.info("\n\n %s \n\n", orders)
                self.name = self.parent_id.name + "/" + str(orders)
            else:
                self.name = self.parent_id.name + "/" + "1"
                _logger.info("\n\n\n\n %s \n\n", orders)



    @api.multi
    def variante(self):
        self.ensure_one()
        action = self.env.ref('crm_sale_order_extended.sale_order_variant').read()[0]   

        _logger.info("\n\n action: %s \n\n", action)
        return action


    #@api.onchange('parent_id')
    #def set_child(self):
    #    if self.parent_id:
    #        self.child = True
    #    else:
    #        self.child = False


    @api.model
    def create(self, vals):

        # Makes sure partner_invoice_id, partner_shipping_id and pricelist_id are defined
        if any(f not in vals for f in ['partner_invoice_id', 'partner_shipping_id', 'pricelist_id']):
            partner = self.env['res.partner'].browse(vals.get('partner_id'))
            addr = partner.address_get(['delivery', 'invoice'])
            vals['partner_invoice_id'] = vals.setdefault('partner_invoice_id', addr['invoice'])

            vals['partner_shipping_id'] = vals.setdefault('partner_shipping_id', addr['delivery'])

            vals['pricelist_id'] = vals.setdefault('pricelist_id', partner.property_product_pricelist and partner.property_product_pricelist.id)

        _logger.info("\n\n\n vals antes de un super: %s \n\n\n", vals)
        result = super(SaleOrderNew, self).create(vals)
        _logger.info("\n\n\n result: %s \n\n\n", result.child)


        if result.child == False:
            _logger.info("\n\n\nSe ejecuto el ir.sequence modificado\n\n")
            if result.name == _('New'):
                if 'company_id' in result.company_id:
                    result.name = self.env['ir.sequence'].with_context(force_company=result.company_id).next_by_code('sale.order') or _('New')
                else:
                    result.name = self.env['ir.sequence'].next_by_code('sale.order') or _('New')



        return result




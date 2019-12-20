# -*- coding: utf-8 -*-


{
    'name': 'crm_sale.order_extended',
    'author': 'Odoolibre',
    'website': 'https://odoolibre.es',
    'description': """ """,
    'depends': [
                'crm',
                'sale',
        ],
 
    'data': [
        'data/ir_sequence_data.xml',
        'views/sale_order_inherit.xml',
        'views/sale_order_variant.xml',
        ],
    'installable': True,
    'auto_install': False,
        
}

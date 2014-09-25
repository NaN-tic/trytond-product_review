#This file is part product_review module for Tryton.
#The COPYRIGHT file at the top level of this repository contains
#the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta

__all__ = ['Template']
__metaclass__ = PoolMeta


class Template:
    __name__ = "product.template"
    review = fields.Boolean('Review')
    review_description = fields.Text('Review Description')

    @staticmethod
    def default_review():
        return True

# This file is part product_review module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import ModelSQL, ModelView, fields
from trytond.pool import PoolMeta
from trytond.pyson import Eval


__all__ = ['Template', 'ProductReviewType', 'TemplateProductReviewType']
__metaclass__ = PoolMeta


class Template:
    __name__ = 'product.template'
    review = fields.Boolean('Review')
    review_types = fields.Many2Many('product.template-product.review.type',
            'product_template', 'review_type', 'Review Types',
        states={
            'invisible': ~Eval('review'),
            },
        depends=['review'],
        )
    review_description = fields.Text('Review Description')

    @staticmethod
    def default_review():
        return True


class ProductReviewType(ModelSQL, ModelView):
    'Product Review Type'
    __name__ = 'product.review.type'
    name = fields.Char('Name', required=True)
    active = fields.Boolean('Active', select=True)


class TemplateProductReviewType(ModelSQL):
    'Template - Product Review Type'
    __name__ = 'product.template-product.review.type'
    _table = 'product_template_product_review_type_rel'
    product_template = fields.Many2One('product.template', 'Product Template',
            ondelete='CASCADE', select=True, required=True)
    review_type = fields.Many2One('product.review.type',
        'Review Type', ondelete='CASCADE', select=True, required=True)

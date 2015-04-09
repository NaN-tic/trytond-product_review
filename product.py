# This file is part product_review module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import ModelSQL, ModelView, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval


__all__ = ['Template', 'ProductReviewType', 'TemplateProductReviewType',
    'ProductReview']
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
    review_description = fields.Text('Review Description',
        states={
            'invisible': ~Eval('review'),
            },
        depends=['review'],
        )


class ProductReviewType(ModelSQL, ModelView):
    'Product Review Type'
    __name__ = 'product.review.type'
    name = fields.Char('Name', required=True)
    active = fields.Boolean('Active', select=True)

    @staticmethod
    def default_active():
        return True


class TemplateProductReviewType(ModelSQL):
    'Template - Product Review Type'
    __name__ = 'product.template-product.review.type'
    _table = 'product_template_product_review_type_rel'
    product_template = fields.Many2One('product.template', 'Product Template',
            ondelete='CASCADE', select=True, required=True)
    review_type = fields.Many2One('product.review.type',
        'Review Type', ondelete='CASCADE', select=True, required=True)


class ProductReview(ModelSQL, ModelView):
    'Product Review'
    __name__ = 'product.review'
    _rec_name = 'product'
    product = fields.Many2One('product.product', 'Product', required=True)
    review_type = fields.Many2One('product.review.type', 'Review Type',
        required=True)
    date = fields.Date('Date')
    state = fields.Selection([
            ('draft', 'Draft'),
            ('done', 'Done'),
            ], 'State')
    note = fields.Char('Note')

    @classmethod
    def __setup__(cls):
        super(ProductReview, cls).__setup__()
        cls._buttons.update({
                'done': {
                    'invisible': Eval('state') == 'done',
                    'icon': 'tryton-go-next',
                    },
                })

    @staticmethod
    def default_state():
        return 'draft'

    @classmethod
    def done(cls, reviews):
        Template = Pool().get('product.template')

        templates = []
        args = []
        for review in reviews:
            template = review.product.template
            args.append([template])
            args.append({
                'review_types': [
                    ('remove', [review.review_type.id])
                    ]
                })
            templates.append(template)
        Template.write(*args)

        args = []
        for template in templates:
            if not template.review_types:
                args.append([template])
                args.append({
                    'review': False
                    })
        if args:
            Template.write(*args)

        cls.write(reviews, {'state': 'done'})

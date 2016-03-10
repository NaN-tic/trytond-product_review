# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import ModelSQL, fields
from trytond.pool import PoolMeta
from trytond.pyson import Eval
from trytond import backend

__all__ = ['Configuration', 'ProductConfigurationReviewType']
__metaclass__ = PoolMeta


class Configuration:
    __name__ = 'product.configuration'
    review = fields.Boolean('Review',
        help='Default value for the review field in template form.')
    review_types = fields.Many2Many('product.configuration.product.review.type',
        'configuration', 'review_type', 'Review Types',
        states={
            'invisible': ~Eval('review', False),
        },
        help='Default value for review types when default review is activated')


class ProductConfigurationReviewType(ModelSQL):
    'Product Configuration - Product Review Type'
    __name__ = 'product.configuration.product.review.type'
    _table = 'product_config_product_review_type'
    configuration = fields.Many2One('product.configuration',
        'Product Configuration', ondelete='CASCADE', required=True)
    review_type = fields.Many2One('product.review.type', 'Review Type',
        ondelete='CASCADE', required=True)

    @classmethod
    def __register__(cls, module_name):
        TableHandler = backend.get('TableHandler')

        # Migration from 3.6: rename table
        old_table = 'product_configuration_product_review_type_rel'
        new_table = 'product_config_product_review_type'
        if TableHandler.table_exist(old_table):
            TableHandler.table_rename(old_table, new_table)

        super(ProductConfigurationReviewType, cls).__register__(module_name)

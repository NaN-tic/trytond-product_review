# This file is part product_review module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from . import configuration
from . import product


def register():
    Pool.register(
        configuration.Configuration,
        product.ProductReviewType,
        product.ProductReview,
        product.Template,
        product.TemplateProductReviewType,
        module='product_review', type_='model')

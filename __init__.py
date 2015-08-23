# This file is part product_review module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from .configuration import *
from .product import *

def register():
    Pool.register(
        Configuration,
        ProductReviewType,
        ProductConfigurationReviewType,
        ProductReview,
        Template,
        TemplateProductReviewType,
        module='product_review', type_='model')

# This file is part product_review module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from email.header import Header
from email.mime.text import MIMEText
from trytond.model import ModelSQL, ModelView, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval
from trytond.sendmail import SMTPDataManager, sendmail_transactional
import logging
from trytond.i18n import gettext

logger = logging.getLogger(__name__)

try:
    import emailvalid
except ImportError:
    emailvalid = None
    logger.error('Unable to import emailvalid. Install emailvalid package.')

__all__ = ['Template', 'ProductReviewType', 'TemplateProductReviewType',
    'ProductReview', 'Cron']

class Cron(metaclass=PoolMeta):
    __name__ = "ir.cron"

    @classmethod
    def __setup__(cls):
        super(Cron, cls).__setup__()
        cls.method.selection.extend([
            ('product.review|send_email',
                'Product Review'),
        ])


class Template(metaclass=PoolMeta):
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

    @staticmethod
    def default_review():
        pool = Pool()
        Config = pool.get('product.configuration')
        config = Config.get_singleton()
        if config:
            return config.review


class ProductReviewType(ModelSQL, ModelView):
    'Product Review Type'
    __name__ = 'product.review.type'
    name = fields.Char('Name', required=True, translate=True)
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
    product = fields.Many2One('product.product', 'Product', required=True)
    review_type = fields.Many2One('product.review.type', 'Review Type',
        required=True)
    date = fields.Date('Date', required=True)
    state = fields.Selection([
            ('draft', 'Draft'),
            ('done', 'Done'),
            ], 'State', readonly=True, required=True)
    note = fields.Char('Note')

    @classmethod
    def __setup__(cls):
        super(ProductReview, cls).__setup__()
        cls._order.insert(0, ('date', 'ASC'))
        cls._buttons.update({
                'done': {
                    'invisible': Eval('state') == 'done',
                    'icon': 'tryton-forward',
                    },
                })

    @staticmethod
    def default_state():
        return 'draft'

    @staticmethod
    def default_date():
        Date = Pool().get('ir.date')
        return Date.today()

    def get_rec_name(self, name):
        if self.product:
            return self.product.rec_name
        return '(%s)' % self.id

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

    @classmethod
    def send_email(cls, args=None):
        pool = Pool()
        SMTPServer = pool.get('smtp.server')
        ModelData = pool.get('ir.model.data')
        Model = pool.get('ir.model')
        Group = pool.get('res.group')
        Cron = pool.get('ir.cron')

        model, = Model.search([('model', '=', cls.__name__)])
        smtp_servers = SMTPServer.search([('models', '=', model.id)],
            limit=1)
        if not smtp_servers:
            smtp_servers = SMTPServer.search([('default', '=', True)], limit=1)
        if not smtp_servers:
            message = gettext('product_review.no_smtp_server_defined')
            logger.warning(message)
            return
        smtp_server, = smtp_servers

        # Search recipients of emails
        group = Group(ModelData.get_id(
                'product_review', 'product_review_group'))
        recipients = [u.email for u in group.users if u.email]
        if (not recipients
                or (emailvalid
                    and not any(map(emailvalid.check_email, recipients)))):
            message = gettext('product_review.check_user_emails')
            logger.warning(message)
            return

        # Search new reviews to send email
        model_data, = ModelData.search([
                ('fs_id', '=', 'cron_product_review'),
                ])
        cron, = Cron.search([('id', '=', model_data.db_id)])
        from_date = cron.write_date or cron.create_date
        reviews = cls.search([
                ('create_date', '>', from_date),
                ('write_date', '=', None),
                ('state', '=', 'draft'),
                ])
        if reviews:
            records = '\n'.join(['%s: %s %s' %
                    (r.date, r.product.name, r.review_type.name)
                    for r in reviews])
            message = gettext('product_review.body', message=records)
            subject = gettext('product_review.subject')

            from_ = smtp_server.smtp_email
            msg = MIMEText(message, _charset='utf-8')
            msg['Subject'] = Header(subject, 'utf-8')
            msg['From'] = from_
            msg['To'] = ', '.join(recipients)

            datamanager = SMTPDataManager()
            datamanager._server = smtp_server.get_smtp_server()
            sendmail_transactional(
                from_, recipients, msg, datamanager=datamanager)

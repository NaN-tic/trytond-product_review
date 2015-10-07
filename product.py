# This file is part product_review module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from _socket import gaierror, error
from email.header import Header
from email.mime.text import MIMEText
from smtplib import SMTPAuthenticationError, SMTPServerDisconnected
from trytond.model import ModelSQL, ModelView, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval
import logging

logger = logging.getLogger(__name__)

try:
    import emailvalid
    CHECK_EMAIL = True
except ImportError:
    logger.error('Unable to import emailvalid. Install emailvalid package.')

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

    @staticmethod
    def default_review():
        pool = Pool()
        Config = pool.get('product.configuration')
        config = Config.get_singleton()
        if config:
            return config.review

    @staticmethod
    def default_review_types():
        pool = Pool()
        Config = pool.get('product.configuration')
        Configuration = pool.get('product.configuration.product.review.type')

        config = Config.get_singleton()
        if config and config.review:
            configurations = Configuration.search([])
            return [c.review_type.id for c in configurations
                if c.review_type.active]
        return []


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
    _rec_name = 'product'
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
                    'icon': 'tryton-go-next',
                    },
                })
        cls._error_messages.update({
                'no_smtp_server_defined': 'You must define an SMTP server in '
                    'order to send scheduled emails warning of new product '
                    'reviews!',
                'check_user_emails': 'No users with email defined in group '
                    'product review!',
                'subject': 'New list of products to review',
                'body': 'Dear employee,\n\n'
                    'Here you have the new list of products to be reviewed:\n'
                    '\n%s\n\n'
                    'Thank you for your attention and good job!\n\n'
                    'Sincerely,\n\nthe Management Team.\n\n'
                    'Note: This messages has been generated and sent '
                    'automatically, please do not repply.',
                'smtp_error': 'Error connecting to SMTP server. '
                    'Emails have not been sent',
                })

    @staticmethod
    def default_state():
        return 'draft'

    @staticmethod
    def default_date():
        Date = Pool().get('ir.date')
        return Date.today()

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
            message = cls.raise_user_error('no_smtp_server_defined',
                raise_exception=False)
            logger.warning(message)
            return
        smtp_server, = smtp_servers

        # Search recipients of emails
        model_data, = ModelData.search([
                ('fs_id', '=', 'product_review_group'),
                ])
        group, = Group.search([('id', '=', model_data.db_id)])
        recipients = [u.email for u in group.users if u.email]
        if not recipients or not any(map(emailvalid.check_email, recipients)):
            message = cls.raise_user_error('check_user_emails',
                raise_exception=False)
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
            message = cls.raise_user_error('body', error_args=(records,),
                raise_exception=False)
            subject = cls.raise_user_error('subject', raise_exception=False)

            from_ = smtp_server.smtp_email
            msg = MIMEText(message, _charset='utf-8')
            msg['Subject'] = Header(subject, 'utf-8')
            msg['From'] = from_
            msg['To'] = ', '.join(recipients)

            try:
                smtp_server = smtp_server.get_smtp_server()
                smtp_server.sendmail(from_, recipients, msg.as_string())
                smtp_server.quit()
            except (SMTPAuthenticationError, SMTPServerDisconnected, gaierror,
                    error):
                message = cls.raise_user_error('smtp_error',
                    raise_exception=False)
                logger.info(message)
                cls.raise_user_error('smtp_error')

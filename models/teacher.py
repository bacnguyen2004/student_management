import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


EMAIL_PATTERN = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


class Teacher(models.Model):
    _name = 'student_management.teacher'
    _description = 'Teacher'
    _order = 'name'

    name = fields.Char(required=True)
    user_id = fields.Many2one(
        'res.users',
        string='User',
        help='Link to Odoo user for access rights and record rules.',
    )
    email = fields.Char()
    phone = fields.Char()
    specialization = fields.Char()
    active = fields.Boolean(default=True)
    course_ids = fields.One2many(
        'student_management.course',
        'teacher_id',
        string='Courses',
    )

    _sql_constraints = [
        (
            'teacher_user_unique',
            'unique(user_id)',
            'A user can be linked to only one teacher.',
        ),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._normalize_email_values(vals)
        return super().create(vals_list)

    def write(self, vals):
        self._normalize_email_values(vals)
        return super().write(vals)

    @staticmethod
    def _normalize_email_values(vals):
        if isinstance(vals.get('email'), str):
            vals['email'] = vals['email'].strip().lower() or False

    @api.constrains('email')
    def _check_email(self):
        for record in self:
            if record.email and not EMAIL_PATTERN.match(record.email):
                raise ValidationError(_('Please enter a valid teacher email address.'))
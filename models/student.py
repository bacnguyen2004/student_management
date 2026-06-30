import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


EMAIL_PATTERN = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


class Student(models.Model):
    _name = 'student_management.student'
    _description = 'Student'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    student_code = fields.Char(string='Student Code', copy=False)
    name = fields.Char(required=True, tracking=True)
    email = fields.Char(tracking=True)
    phone = fields.Char()
    date_of_birth = fields.Date()
    age = fields.Integer(compute='_compute_age')
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ])
    address = fields.Text()
    note = fields.Text()
    active = fields.Boolean(default=True)
    enrollment_ids = fields.One2many(
        'student_management.enrollment',
        'student_id',
        string='Enrollments',
    )
    classroom_ids = fields.Many2many(
        'student_management.classroom',
        string='Classes',
    )
    course_count = fields.Integer(
        string='Enrolled Courses',
        compute='_compute_course_count',
    )

    _sql_constraints = [
        (
            'student_code_unique',
            'unique(student_code)',
            'Student code must be unique.',
        ),
    ]

    @api.depends('date_of_birth')
    def _compute_age(self):
        today = fields.Date.today()
        for record in self:
            if record.date_of_birth:
                born = record.date_of_birth
                record.age = (
                    today.year - born.year
                    - ((today.month, today.day) < (born.month, born.day))
                )
            else:
                record.age = 0

    @api.depends('enrollment_ids.course_id', 'enrollment_ids.status')
    def _compute_course_count(self):
        for record in self:
            record.course_count = len(
                record.enrollment_ids.filtered(
                    lambda enrollment: enrollment.status != 'cancelled'
                )
            )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._normalize_email_values(vals)
            if not vals.get('student_code'):
                vals['student_code'] = (
                    self.env['ir.sequence'].next_by_code(
                        'student_management.student'
                    ) or 'New'
                )
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
            if not record.email:
                continue
            if not EMAIL_PATTERN.match(record.email):
                raise ValidationError(_('Please enter a valid student email address.'))
            duplicate = self.search([
                ('email', '=ilike', record.email),
                ('id', '!=', record.id),
            ], limit=1)
            if duplicate:
                raise ValidationError(
                    _('Email "%s" is already used by another student.') % record.email
                )

    @api.constrains('date_of_birth')
    def _check_date_of_birth(self):
        today = fields.Date.today()
        for record in self:
            if record.date_of_birth and record.date_of_birth > today:
                raise ValidationError(
                    _('Student "%s" cannot have a date of birth in the future.')
                    % record.name
                )

    def action_view_enrollments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Enrollments',
            'res_model': 'student_management.enrollment',
            'view_mode': 'list,form',
            'domain': [('student_id', '=', self.id)],
            'context': {'default_student_id': self.id},
        }
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class Course(models.Model):
    _name = 'student_management.course'
    _description = 'Course'
    _order = 'name'

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    teacher_id = fields.Many2one(
        'student_management.teacher',
        string='Teacher',
    )
    description = fields.Text()
    fee = fields.Float()
    duration = fields.Integer(string='Duration Hours')
    enrollment_ids = fields.One2many(
        'student_management.enrollment',
        'course_id',
        string='Enrollments',
    )
    classroom_ids = fields.One2many(
        'student_management.classroom',
        'course_id',
        string='Classes',
    )
    student_count = fields.Integer(
        string='Student Count',
        compute='_compute_student_count',
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        (
            'course_code_unique',
            'unique(code)',
            'Course code must be unique.',
        ),
    ]

    @api.depends('enrollment_ids.student_id', 'enrollment_ids.status')
    def _compute_student_count(self):
        for record in self:
            active_enrollments = record.enrollment_ids.filtered(
                lambda enrollment: enrollment.status != 'cancelled'
            )
            record.student_count = len(active_enrollments.mapped('student_id'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._normalize_code_values(vals)
        return super().create(vals_list)

    def write(self, vals):
        self._normalize_code_values(vals)
        return super().write(vals)

    @staticmethod
    def _normalize_code_values(vals):
        if isinstance(vals.get('code'), str):
            vals['code'] = vals['code'].strip().upper()

    @api.constrains('fee')
    def _check_fee(self):
        for record in self:
            if record.fee < 0:
                raise ValidationError(_('Course fee cannot be negative.'))

    @api.constrains('duration')
    def _check_duration(self):
        for record in self:
            if record.duration < 0:
                raise ValidationError(_('Course duration cannot be negative.'))

    def action_view_enrollments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Enrollments',
            'res_model': 'student_management.enrollment',
            'view_mode': 'list,form',
            'domain': [('course_id', '=', self.id)],
            'context': {'default_course_id': self.id},
        }

    def action_enroll_students(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Enroll Students',
            'res_model': 'student_management.enroll.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_course_id': self.id},
        }
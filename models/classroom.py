from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class Classroom(models.Model):
    _name = 'student_management.classroom'
    _description = 'Class'
    _order = 'start_date desc, name'

    name = fields.Char(required=True)
    code = fields.Char()
    course_id = fields.Many2one(
        'student_management.course',
        string='Course',
        required=True,
    )
    teacher_id = fields.Many2one(
        'student_management.teacher',
        string='Teacher',
        related='course_id.teacher_id',
        store=True,
    )
    student_ids = fields.Many2many(
        'student_management.student',
        string='Students',
    )
    student_count = fields.Integer(
        string='Student Count',
        compute='_compute_student_count',
    )
    max_students = fields.Integer(string='Max Students', default=30)
    start_date = fields.Date()
    end_date = fields.Date()
    active = fields.Boolean(default=True)

    _sql_constraints = [
        (
            'classroom_code_unique',
            'unique(code)',
            'Class code must be unique.',
        ),
    ]

    @api.depends('student_ids')
    def _compute_student_count(self):
        for record in self:
            record.student_count = len(record.student_ids)

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
            vals['code'] = vals['code'].strip().upper() or False

    @api.constrains('student_ids', 'max_students')
    def _check_max_students(self):
        for record in self:
            if record.max_students < 0:
                raise ValidationError(_('Max students cannot be negative.'))
            if record.max_students and len(record.student_ids) > record.max_students:
                raise ValidationError(
                    _('Class "%s" cannot have more than %s students.')
                    % (record.name, record.max_students)
                )

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise ValidationError(
                    _('Class "%s" has an invalid date range.') % record.name
                )
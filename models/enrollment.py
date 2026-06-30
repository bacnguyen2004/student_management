from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class Enrollment(models.Model):
    _name = 'student_management.enrollment'
    _description = 'Enrollment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'enrollment_date desc'
    _rec_name = 'name'

    name = fields.Char(
        compute='_compute_name',
        store=True,
    )
    student_id = fields.Many2one(
        'student_management.student',
        string='Student',
        required=True,
    )
    course_id = fields.Many2one(
        'student_management.course',
        string='Course',
        required=True,
    )
    enrollment_date = fields.Date(
        string='Enrollment Date',
        default=fields.Date.today,
    )
    status = fields.Selection(
        [
            ('draft', 'Draft'),
            ('studying', 'Studying'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
    )
    grade = fields.Float(string='Grade', default=False)
    result = fields.Char(
        string='Result',
        compute='_compute_result',
    )
    student_email = fields.Char(
        string='Student Email',
        related='student_id.email',
    )
    teacher_id = fields.Many2one(
        'student_management.teacher',
        string='Teacher',
        related='course_id.teacher_id',
    )
    course_fee = fields.Float(
        string='Course Fee',
        related='course_id.fee',
    )

    _sql_constraints = [
        (
            'unique_student_course',
            'unique(student_id, course_id)',
            'A student cannot enroll in the same course twice.',
        ),
    ]

    @api.depends('student_id.name', 'course_id.name')
    def _compute_name(self):
        for record in self:
            if record.student_id and record.course_id:
                record.name = '%s - %s' % (
                    record.student_id.name,
                    record.course_id.name,
                )
            elif record.student_id:
                record.name = record.student_id.name
            elif record.course_id:
                record.name = record.course_id.name
            else:
                record.name = _('New Enrollment')

    @api.constrains('grade', 'status')
    def _check_grade(self):
        for record in self:
            if record.grade is not False and (record.grade < 0 or record.grade > 10):
                raise ValidationError(_('Grade must be between 0 and 10.'))
            if record.status == 'completed' and record.grade is False:
                raise ValidationError(_('A completed enrollment must have a grade.'))

    @api.depends('grade')
    def _compute_result(self):
        for record in self:
            if record.grade is False:
                record.result = False
            elif record.grade >= 5:
                record.result = 'Pass'
            else:
                record.result = 'Fail'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._send_teacher_notification()
        studying_records = records.filtered(lambda record: record.status == 'studying')
        studying_records._send_studying_notification()
        return records

    def write(self, vals):
        studying_before = set()
        if vals.get('status') == 'studying':
            studying_before = set(self.filtered(lambda record: record.status == 'studying').ids)
        result = super().write(vals)
        if vals.get('status') == 'studying':
            newly_studying = self.filtered(
                lambda record: record.id not in studying_before
                and record.status == 'studying'
            )
            newly_studying._send_studying_notification()
        return result

    def _send_teacher_notification(self):
        template = self.env.ref(
            'student_management.mail_template_enrollment_teacher_notify',
            raise_if_not_found=False,
        )
        if not template:
            return
        for record in self:
            if record.teacher_id and record.teacher_id.email:
                template.send_mail(record.id, force_send=False)

    def _send_studying_notification(self):
        template = self.env.ref(
            'student_management.mail_template_enrollment_studying',
            raise_if_not_found=False,
        )
        if not template:
            return
        for record in self:
            if record.student_email:
                template.send_mail(record.id, force_send=False)

    @api.model
    def _cron_auto_complete_enrollments(self):
        """Complete studying enrollments older than 90 days with a grade."""
        deadline = fields.Date.today() - relativedelta(days=90)
        enrollments = self.search([
            ('status', '=', 'studying'),
            ('enrollment_date', '<=', deadline),
            ('grade', '!=', False),
        ])
        if enrollments:
            enrollments.action_complete()

    @api.onchange('student_id', 'course_id')
    def _onchange_student_course(self):
        if self.student_id and self.course_id:
            existing = self.search([
                ('student_id', '=', self.student_id.id),
                ('course_id', '=', self.course_id.id),
                ('id', '!=', self._origin.id),
            ], limit=1)
            if existing:
                return {
                    'warning': {
                        'title': _('Duplicate Enrollment'),
                        'message': _('This student is already enrolled in this course.'),
                    },
                }

    def action_start_studying(self):
        invalid = self.filtered(lambda record: record.status != 'draft')
        if invalid:
            raise UserError(_('Only draft enrollments can start studying.'))
        self.write({'status': 'studying'})

    def action_complete(self):
        missing_grade = self.filtered(lambda record: record.grade is False)
        if missing_grade:
            raise UserError(_('Please enter a grade before completing the enrollment.'))
        self.write({'status': 'completed'})

    def action_cancel(self):
        completed = self.filtered(lambda record: record.status == 'completed')
        if completed:
            raise UserError(_('Completed enrollments cannot be cancelled.'))
        self.write({'status': 'cancelled'})

    def action_reset_draft(self):
        invalid = self.filtered(lambda record: record.status != 'cancelled')
        if invalid:
            raise UserError(_('Only cancelled enrollments can be reset to draft.'))
        self.write({'status': 'draft'})
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class EnrollStudentsWizard(models.TransientModel):
    _name = 'student_management.enroll.wizard'
    _description = 'Enroll Students Wizard'

    course_id = fields.Many2one(
        'student_management.course',
        string='Course',
        required=True,
    )
    student_ids = fields.Many2many(
        'student_management.student',
        'sm_enroll_wiz_student_rel',
        'wizard_id',
        'student_id',
        string='Students',
    )
    enrollment_date = fields.Date(
        string='Enrollment Date',
        default=fields.Date.today,
    )
    status = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('studying', 'Studying'),
        ],
        string='Status',
        default='draft',
        required=True,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        course_id = self.env.context.get('default_course_id')
        if course_id:
            res['course_id'] = course_id
        return res

    def action_enroll(self):
        self.ensure_one()
        if not self.student_ids:
            raise UserError(_('Please select at least one student.'))
        self._check_teacher_course_access()

        Enrollment = self.env['student_management.enrollment']
        created = 0
        skipped = []

        for student in self.student_ids:
            existing = Enrollment.search([
                ('student_id', '=', student.id),
                ('course_id', '=', self.course_id.id),
            ], limit=1)
            if existing:
                skipped.append(student.name)
                continue
            Enrollment.create({
                'student_id': student.id,
                'course_id': self.course_id.id,
                'enrollment_date': self.enrollment_date,
                'status': self.status,
            })
            created += 1

        if not created and skipped:
            raise UserError(
                _('All selected students are already enrolled in %s.')
                % self.course_id.display_name
            )

        message = _('%s student(s) enrolled in %s.') % (
            created,
            self.course_id.display_name,
        )
        if skipped:
            message += ' ' + _('Skipped (already enrolled): %s') % ', '.join(skipped)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Enrollment'),
                'message': message,
                'type': 'success',
                'sticky': bool(skipped),
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }

    def _check_teacher_course_access(self):
        user = self.env.user
        is_manager = user.has_group('student_management.group_student_management_staff')
        is_admin = user.has_group('student_management.group_student_management_admin')
        is_teacher = user.has_group('student_management.group_student_management_teacher')
        if is_admin or is_manager or not is_teacher:
            return
        if self.course_id.teacher_id.user_id != user:
            raise UserError(_('You can only enroll students in your own courses.'))
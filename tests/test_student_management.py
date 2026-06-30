from datetime import date

from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestStudentManagement(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Student = cls.env['student_management.student']
        cls.Course = cls.env['student_management.course']
        cls.Enrollment = cls.env['student_management.enrollment']
        cls.Classroom = cls.env['student_management.classroom']
        cls.Teacher = cls.env['student_management.teacher']
        cls.EnrollWizard = cls.env['student_management.enroll.wizard']

        cls.teacher = cls.Teacher.create({'name': 'Test Teacher', 'email': 'teacher@test.com'})
        cls.course = cls.Course.create({
            'name': 'Test Course',
            'code': 'TST101',
            'teacher_id': cls.teacher.id,
        })
        cls.student_a = cls.Student.create({
            'name': 'Student A',
            'email': 'student.a@test.com',
        })
        cls.student_b = cls.Student.create({
            'name': 'Student B',
            'email': 'student.b@test.com',
        })

    def test_student_code_sequence(self):
        self.assertTrue(self.student_a.student_code)
        self.assertTrue(self.student_a.student_code.startswith('STD'))

    def test_student_email_is_normalized_and_validated(self):
        student = self.Student.create({
            'name': 'Email Normalize',
            'email': '  Mixed.Case@Test.COM  ',
        })
        self.assertEqual(student.email, 'mixed.case@test.com')
        with self.assertRaises(ValidationError):
            self.Student.create({
                'name': 'Bad Email',
                'email': 'not-an-email',
            })

    def test_unique_email_constraint(self):
        with self.assertRaises(ValidationError):
            self.Student.create({
                'name': 'Duplicate Email',
                'email': 'STUDENT.A@TEST.COM',
            })

    def test_date_of_birth_constraint(self):
        with self.assertRaises(ValidationError):
            self.Student.create({
                'name': 'Future Born',
                'email': 'future@test.com',
                'date_of_birth': date(2099, 1, 1),
            })

    def test_course_code_normalized_and_amounts_validated(self):
        course = self.Course.create({
            'name': 'Normalized Code Course',
            'code': ' code101 ',
        })
        self.assertEqual(course.code, 'CODE101')
        with self.assertRaises(ValidationError):
            self.Course.create({
                'name': 'Bad Fee',
                'code': 'BADFEE',
                'fee': -1,
            })
        with self.assertRaises(ValidationError):
            self.Course.create({
                'name': 'Bad Duration',
                'code': 'BADDURATION',
                'duration': -1,
            })

    def test_enrollment_unique_constraint(self):
        self.Enrollment.create({
            'student_id': self.student_a.id,
            'course_id': self.course.id,
        })
        with self.assertRaises(Exception):
            self.Enrollment.create({
                'student_id': self.student_a.id,
                'course_id': self.course.id,
            })

    def test_grade_constraint(self):
        enrollment = self.Enrollment.create({
            'student_id': self.student_b.id,
            'course_id': self.course.id,
        })
        with self.assertRaises(ValidationError):
            enrollment.write({'grade': 11})

    def test_compute_result_pass_fail(self):
        enrollment = self.Enrollment.create({
            'student_id': self.student_b.id,
            'course_id': self.course.id,
            'grade': 8,
        })
        self.assertEqual(enrollment.result, 'Pass')
        enrollment.grade = 4
        self.assertEqual(enrollment.result, 'Fail')

    def test_enrollment_display_name(self):
        enrollment = self.Enrollment.create({
            'student_id': self.student_a.id,
            'course_id': self.course.id,
        })
        self.assertEqual(enrollment.name, 'Student A - Test Course')

    def test_enrollment_workflow_requires_grade_to_complete(self):
        enrollment = self.Enrollment.create({
            'student_id': self.student_b.id,
            'course_id': self.course.id,
            'status': 'studying',
        })
        with self.assertRaises(UserError):
            enrollment.action_complete()
        enrollment.grade = 6
        enrollment.action_complete()
        self.assertEqual(enrollment.status, 'completed')

    def test_student_and_course_counts_ignore_cancelled_enrollments(self):
        self.Enrollment.create({
            'student_id': self.student_a.id,
            'course_id': self.course.id,
            'status': 'cancelled',
        })
        self.Enrollment.create({
            'student_id': self.student_b.id,
            'course_id': self.course.id,
            'status': 'studying',
        })
        self.assertEqual(self.student_a.course_count, 0)
        self.assertEqual(self.student_b.course_count, 1)
        self.assertEqual(self.course.student_count, 1)

    def test_classroom_max_students(self):
        with self.assertRaises(ValidationError):
            self.Classroom.create({
                'name': 'Small Class',
                'course_id': self.course.id,
                'max_students': 1,
                'student_ids': [(6, 0, [self.student_a.id, self.student_b.id])],
            })

    def test_classroom_date_range(self):
        with self.assertRaises(ValidationError):
            self.Classroom.create({
                'name': 'Invalid Date Class',
                'course_id': self.course.id,
                'start_date': date(2026, 5, 1),
                'end_date': date(2026, 4, 1),
            })

    def test_wizard_enroll_skips_existing_students(self):
        self.Enrollment.create({
            'student_id': self.student_a.id,
            'course_id': self.course.id,
        })
        wizard = self.EnrollWizard.create({
            'course_id': self.course.id,
            'student_ids': [(6, 0, [self.student_a.id, self.student_b.id])],
        })
        action = wizard.action_enroll()
        enrollments = self.Enrollment.search([
            ('course_id', '=', self.course.id),
            ('student_id', 'in', [self.student_a.id, self.student_b.id]),
        ])
        self.assertEqual(len(enrollments), 2)
        self.assertEqual(action['tag'], 'display_notification')
        self.assertTrue(action['params']['sticky'])

    def test_cron_auto_complete_enrollments(self):
        old_date = date(2020, 1, 1)
        enrollment = self.Enrollment.create({
            'student_id': self.student_a.id,
            'course_id': self.course.id,
            'enrollment_date': old_date,
            'status': 'studying',
            'grade': 7,
        })
        self.Enrollment._cron_auto_complete_enrollments()
        enrollment.invalidate_recordset()
        self.assertEqual(enrollment.status, 'completed')
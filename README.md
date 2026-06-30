# Student Management — Odoo 18 Module

[![Odoo](https://img.shields.io/badge/Odoo-18.0-875A7B?logo=odoo&logoColor=white)](https://www.odoo.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![License](https://img.shields.io/badge/License-LGPL--3-blue.svg)](LICENSE)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Required-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org)

Odoo module for managing students, courses, teachers, classrooms, and enrollments.  
Portfolio project demonstrating full-stack Odoo development: ORM, XML views, security, reports, mail, cron, and unit tests.

**Author:** Nguyen Van Bac

---

## Features

| Area | Details |
|------|---------|
| **Models** | Student, Teacher, Course, Classroom, Enrollment |
| **Views** | List, Form, Search, Kanban, Calendar, Graph, Pivot |
| **Business logic** | Constraints, computed fields, workflow `draft → studying → completed` |
| **Security** | Groups (Teacher / Staff / Administrator), ACL, record rules |
| **Sequence** | Auto student code `STD00001` |
| **Wizard** | Bulk enroll students into a course |
| **Reports** | Student Card, Student List by Course, Class Grade Report (PDF) |
| **Mail** | Email on enrollment start + teacher notification |
| **Cron** | Auto-complete studying enrollments (90+ days with grade) |
| **Dashboard** | Graph & pivot analysis of enrollments |
| **Tests** | 15+ unit tests (`TransactionCase`) |

---

## Screenshots

> Add screenshots after installing the module: **Students → Kanban**, **Enrollments → Graph**, **Reports → Student Card**.

---

## Requirements

- Odoo 18
- Python 3.10+
- PostgreSQL

---

## Installation

```bash
# 1. Clone into your Odoo custom addons path
git clone https://github.com/bacnguyen2004/student_management.git custom_addons/student_management

# 2. Ensure addons_path includes custom_addons in odoo.conf
# addons_path = addons,custom_addons

# 3. Restart Odoo, then in UI:
# Apps → Update Apps List → search "student_management" → Install
# Optional: enable "Load demonstration data" for sample records
```

Upgrade after code changes: **Apps → student_management → Upgrade**

---

## Security groups

| Group | Access |
|-------|--------|
| Teacher | Read students/courses; manage own course enrollments |
| Staff | CRUD all (no delete) |
| Administrator | Full access |

Assign groups: **Settings → Users → Access Rights → Student Management**

Link teacher to user: **Teachers → User field** (required for enrollment record rules).

---

## Run tests

```bash
./odoo-bin -c odoo.conf -d test_db -i student_management --test-enable --stop-after-init
```

---

## Module structure

```
student_management/
├── models/          # ORM models (5 models)
├── views/           # XML views & menus
├── wizard/          # TransientModel wizards
├── report/          # QWeb PDF reports
├── security/        # Groups, ACL, record rules
├── data/            # Sequence, mail templates, cron
├── demo/            # Demo data
├── tests/           # Unit tests
└── static/          # Module icon & description
```

---

## Tech stack (for CV / portfolio)

- **Backend:** Python, Odoo ORM, constraints, computed fields, cron
- **Frontend:** XML views (Kanban, Calendar, Graph, Pivot)
- **Security:** `res.groups`, `ir.model.access`, record rules
- **Reporting:** QWeb PDF templates
- **Integration:** Mail templates (`mail` module)
- **Testing:** `odoo.tests.TransactionCase`

---

## License

[LGPL-3.0](LICENSE) — Odoo Community compatible.

---

## Author

**Nguyen Van Bac** — Odoo Intern / Fresher portfolio project
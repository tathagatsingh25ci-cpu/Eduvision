EduVision AI stores runtime data in the Flask instance SQLite database:

- `instance/eduvision.db`

Primary production-style tables created by `app.py`:

- `students`
- `teachers`
- `admins`
- `marks`
- `predictions`
- `attendance`
- `user`

Legacy tables from the earlier project (`student`, `teacher`) are read once and copied into the new plural tables when the new tables are empty.

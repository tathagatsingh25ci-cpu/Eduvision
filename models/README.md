Model logic currently lives in `app.py` so the existing Flask entry point stays simple for demos.

The active ML pipeline uses:

- Linear Regression for expected percentage
- Decision Tree for category signal
- Random Forest for risk/category stabilization
- A heuristic fallback when fewer than five student records exist

The `predictions` table stores the latest generated prediction snapshot for each student.

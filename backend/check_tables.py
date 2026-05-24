#!/usr/bin/env python3
"""Check database tables."""
import sqlite3

conn = sqlite3.connect('e:\\css\\portal.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("✓ Database Tables Created:")
print("─" * 50)
for table in sorted(tables):
    cursor.execute(f"PRAGMA table_info({table[0]})")
    columns = cursor.fetchall()
    print(f"  {table[0]}: {len(columns)} columns")

print(f"\n✓ Total tables: {len(tables)}")
print("\nExpected tables: User, UserProfile, CourseSelection, SyllabusTracker,")
print("                 SyllabusPlan, MockTestAttempt, UserProgress, PerformanceLog,")
print("                 Essay, AnswerSubmission, ReviewFeedback, AdminLog")
conn.close()

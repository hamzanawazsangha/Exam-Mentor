from main import app, db
from app.models.models import UserProgress, PerformanceLog

def seed_data():
    with app.app_context():
        # Seed some progress
        p1 = UserProgress(topic_id="pa_movement", subject_id="pa", completion_percentage=65.0)
        p2 = UserProgress(topic_id="pa_constitution", subject_id="pa", completion_percentage=30.0)
        p3 = UserProgress(topic_id="essay_governance", subject_id="essay", completion_percentage=80.0)
        
        # Seed some performance (weak topics)
        l1 = PerformanceLog(topic_id="pa_constitution", subject_id="pa", score=0.4, question_type="MCQ")
        l2 = PerformanceLog(topic_id="gsa_math", subject_id="gsa", score=0.3, question_type="MCQ")
        
        db.session.add_all([p1, p2, p3, l1, l2])
        db.session.commit()
        print("Successfully seeded initial data.")

if __name__ == "__main__":
    seed_data()

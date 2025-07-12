from config.database import save_feedback, get_feedback_stats

class FeedbackManager:
    def save_feedback(self, feedback_data):
        save_feedback(feedback_data)

    def get_feedback_stats(self):
        return get_feedback_stats()
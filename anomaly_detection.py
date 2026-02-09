"""
anomaly_detection.py
Anomaly detection using Isolation Forest
"""

from sklearn.ensemble import IsolationForest
import pandas as pd
from database import ExpenseDatabase

class AnomalyDetector:
    def __init__(self, contamination=0.05):
        """
        contamination: Expected proportion of outliers (5% = 5 out of 100)
        """
        self.contamination = contamination
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        self.db = ExpenseDatabase()
    
    def detect_anomalies(self):
        """Find unusual expenses in database"""
        df = self.db.get_all_expenses()
        
        if len(df) < 10:
            print("⚠️ Need at least 10 expenses for anomaly detection")
            return pd.DataFrame()
        
        # Train on amount only
        X = df[['amount']].values
        predictions = self.model.fit_predict(X)
        
        # -1 = anomaly, 1 = normal
        df['is_anomaly'] = predictions
        anomalies = df[df['is_anomaly'] == -1].copy()
        
        # Calculate anomaly score (lower = more abnormal)
        anomalies['anomaly_score'] = self.model.score_samples(anomalies[['amount']].values)
        anomalies = anomalies.sort_values('anomaly_score')
        
        return anomalies[['date', 'amount', 'category', 'description', 'anomaly_score']]
    
    def is_amount_anomalous(self, amount):
        """Check if a single amount is anomalous"""
        df = self.db.get_all_expenses()
        X = df[['amount']].values
        
        self.model.fit(X)
        prediction = self.model.predict([[amount]])
        
        return prediction[0] == -1  # True if anomaly

# Test anomaly detection
if __name__ == "__main__":
    detector = AnomalyDetector(contamination=0.05)
    
    anomalies = detector.detect_anomalies()
    
    print(f"\n⚠️ Found {len(anomalies)} unusual expenses:")
    print(anomalies.to_string())
    
    # Test single amount
    test_amount = 5000
    is_unusual = detector.is_amount_anomalous(test_amount)
    print(f"\nIs ₹{test_amount} unusual? {'Yes ⚠️' if is_unusual else 'No ✅'}")

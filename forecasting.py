"""
forecasting.py - UPDATED VERSION
Time-series forecasting using Facebook Prophet
"""

from prophet import Prophet
import pandas as pd
from database import ExpenseDatabase
import warnings

# Suppress Prophet warnings
warnings.filterwarnings('ignore')
import logging
logging.getLogger('prophet').setLevel(logging.ERROR)

class ExpenseForecaster:
    def __init__(self):
        self.db = ExpenseDatabase()
        self.model = None
    
    def prepare_data(self):
        """Prepare data in Prophet format (ds, y)"""
        df = self.db.get_all_expenses()
        
        if len(df) < 10:
            raise ValueError("Need at least 10 expense records for forecasting")
        
        # Aggregate daily totals
        df['date'] = pd.to_datetime(df['date'])
        daily_total = df.groupby('date')['amount'].sum().reset_index()
        
        # Prophet requires 'ds' and 'y' columns
        daily_total.columns = ['ds', 'y']
        
        return daily_total
    
    def train_model(self):
        """Train Prophet model on historical data"""
        data = self.prepare_data()
        
        # Initialize Prophet with custom settings
        self.model = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=True,
            changepoint_prior_scale=0.05
        )
        
        # Suppress output during training
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.model.fit(data)
        
        return self.model
    
    def predict_future(self, days=30):
        """Predict next N days of expenses"""
        if self.model is None:
            self.train_model()
        
        # Create future dataframe
        future = self.model.make_future_dataframe(periods=days)
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            forecast = self.model.predict(future)
        
        # Return only future predictions
        prediction = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(days)
        prediction.columns = ['Date', 'Predicted', 'Lower_Bound', 'Upper_Bound']
        
        # Ensure non-negative predictions
        prediction['Predicted'] = prediction['Predicted'].clip(lower=0)
        prediction['Lower_Bound'] = prediction['Lower_Bound'].clip(lower=0)
        prediction['Upper_Bound'] = prediction['Upper_Bound'].clip(lower=0)
        
        return prediction
    
    def get_monthly_prediction(self):
        """Get total predicted spending for next month"""
        prediction = self.predict_future(30)
        total = prediction['Predicted'].sum()
        return round(total, 2)

# Test forecasting
if __name__ == "__main__":
    forecaster = ExpenseForecaster()
    
    try:
        forecaster.train_model()
        predictions = forecaster.predict_future(30)
        print("\n📈 Next 30 Days Forecast:")
        print(predictions.head(10))
        print(f"\n💰 Predicted monthly spending: ₹{forecaster.get_monthly_prediction():,.2f}")
    except ValueError as e:
        print(f"Error: {e}")
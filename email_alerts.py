"""
email_alerts.py
Email notification system for budget alerts
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

class EmailAlertSystem:
    def __init__(self, sender_email, sender_password):
        """
        Initialize with Gmail credentials
        sender_password: Use Gmail App Password (not regular password)
        Generate at: https://myaccount.google.com/apppasswords
        """
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.smtp_server = 'smtp.gmail.com'
        self.smtp_port = 465
    
    def send_budget_alert(self, recipient_email, predicted_amount, budget_limit):
        """Send email when predicted spending exceeds budget"""
        
        if predicted_amount <= budget_limit:
            print("✅ Spending within budget. No alert needed.")
            return False
        
        # Calculate overage
        overage = predicted_amount - budget_limit
        overage_percent = (overage / budget_limit) * 100
        
        # Create email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"⚠️ Budget Alert: Exceeding by ₹{overage:,.2f}"
        msg['From'] = self.sender_email
        msg['To'] = recipient_email
        
        # Email body (HTML)
        html = f"""
        <html>
          <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #d9534f;">Budget Alert 🚨</h2>
            <p>Your predicted spending for next month is exceeding your budget!</p>
            
            <table style="border-collapse: collapse; width: 100%; max-width: 400px;">
              <tr style="background-color: #f0f0f0;">
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Budget Limit</strong></td>
                <td style="padding: 10px; border: 1px solid #ddd;">₹{budget_limit:,.2f}</td>
              </tr>
              <tr>
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Predicted Spending</strong></td>
                <td style="padding: 10px; border: 1px solid #ddd; color: #d9534f;">₹{predicted_amount:,.2f}</td>
              </tr>
              <tr style="background-color: #f0f0f0;">
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Overage</strong></td>
                <td style="padding: 10px; border: 1px solid #ddd; color: #d9534f;">₹{overage:,.2f} ({overage_percent:.1f}%)</td>
              </tr>
            </table>
            
            <p style="margin-top: 20px;">
              <strong>Action Required:</strong> Review your upcoming expenses and consider reducing discretionary spending.
            </p>
            
            <p style="color: #777; font-size: 12px; margin-top: 30px;">
              Sent on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br>
              Expense Tracker AI
            </p>
          </body>
        </html>
        """
        
        msg.attach(MIMEText(html, 'html'))
        
        # Send email
        try:
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            print(f"✅ Budget alert sent to {recipient_email}")
            return True
        
        except Exception as e:
            print(f"❌ Failed to send email: {str(e)}")
            return False
    
    def send_anomaly_alert(self, recipient_email, anomaly_amount, category):
        """Send email for detected anomaly"""
        msg = MIMEMultipart()
        msg['Subject'] = "⚠️ Unusual Expense Detected"
        msg['From'] = self.sender_email
        msg['To'] = recipient_email
        
        body = f"""
        Anomaly Alert!
        
        An unusual expense was detected:
        - Amount: ₹{anomaly_amount:,.2f}
        - Category: {category}
        - Time: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
        
        This amount is significantly higher than your typical spending pattern.
        Please verify this transaction.
        
        - Expense Tracker AI
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        try:
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            print(f"✅ Anomaly alert sent to {recipient_email}")
            return True
        
        except Exception as e:
            print(f"❌ Failed to send email: {str(e)}")
            return False

# Test email system (REPLACE WITH YOUR CREDENTIALS)
if __name__ == "__main__":
    # ⚠️ IMPORTANT: Use App Password, not regular Gmail password
    # Generate at: https://myaccount.google.com/apppasswords
    
    sender = "vanshuman206@gmail.com"  # Your Gmail
    password = "nzgb ysnx lxkc taks"    # 16-character app password
    recipient = "recipient@example.com"
    
    alert_system = EmailAlertSystem(sender, password)
    
    # Test budget alert
    alert_system.send_budget_alert(recipient, 28000, 25000)
    
    # Test anomaly alert
    alert_system.send_anomaly_alert(recipient, 15000, "Shopping")
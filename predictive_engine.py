import pandas as pd
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import xgboost as xgb
import warnings
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Hide the annoying warnings related to Pandas
warnings.filterwarnings('ignore', category=FutureWarning)

# ==========================================
# 1. Database Connection Setup
# ==========================================
load_dotenv()
SERVER = os.getenv("DB_SERVER", "localhost")
DATABASE = os.getenv("DB_NAME", "HR_DW")
DRIVER = 'ODBC Driver 17 for SQL Server'

connection_string = f"mssql+pyodbc://@{SERVER}/{DATABASE}?driver={DRIVER}&trusted_connection=yes"
engine = create_engine(connection_string)

def run_ml_pipeline():
    print("🚀 Starting Advanced Predictive Engine (XGBoost)...")

    # ==========================================
    # 2. Extract Data for Machine Learning
    # ==========================================
    query = """
    SELECT 
        e.Age, e.Gender, e.MaritalStatus,
        f.TenureDays, f.PayZone, f.PerformanceScore, 
        f.EngagementScore, f.SatisfactionScore, f.WorkLifeBalanceScore, 
        f.TrainingCost, f.TrainingOutcome,
        f.AttritionFlag, f.EmployeeStatus, e.FullName, e.Email
    FROM Fact_HR f
    JOIN Dim_Employee e ON f.EmployeeKey = e.EmployeeKey
    WHERE f.EmployeeKey != -1
    """
    
    print("📊 Pulling Data from Data Warehouse...")
    df = pd.read_sql(query, engine)

    df.fillna({
        'Age': df['Age'].median(),
        'TenureDays': df['TenureDays'].median(),
        'TrainingCost': 0,
        'EngagementScore': 3,
        'SatisfactionScore': 3,
        'WorkLifeBalanceScore': 3,
        'PayZone': 'Unknown',
        'PerformanceScore': 'Fully Meets',
        'TrainingOutcome': 'None'
    }, inplace=True)

    # ==========================================
    # 3. Advanced Preprocessing (One-Hot Encoding)
    # ==========================================
    print("⚙️ Smart Preprocessing (One-Hot Encoding)...")
    features = ['Age', 'Gender', 'MaritalStatus', 'TenureDays', 'PayZone', 
                'PerformanceScore', 'EngagementScore', 'SatisfactionScore', 
                'WorkLifeBalanceScore', 'TrainingCost', 'TrainingOutcome']
    
    ml_df = df[features].copy()
    
    # One-Hot Encoding: Converts text into numeric columns of zeros and ones (much better than regular encoding)
    ml_df = pd.get_dummies(ml_df, drop_first=True)
    
    # Target variables
    y = df['AttritionFlag']
    X = ml_df

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # ==========================================
    # 4. Train the AI Model (Tuned XGBoost Beast)
    # ==========================================
    print("🧠 Training Tuned XGBoost Classifier...")
    
    stay_count = (y_train == 0).sum()
    leave_count = (y_train == 1).sum()
    
    # The magic tweak: we’ll multiply the weight by 0.6 so the model doesn’t become overly pessimistic
    tuned_weight = (stay_count / leave_count) * 0.6 

    xgb_model = xgb.XGBClassifier(
        n_estimators=150,          # Reducing the number of trees to prevent overfitting
        learning_rate=0.03,        # Slowing down the learning rate to increase accuracy
        max_depth=4,               # Use a smaller tree depth so it doesn’t become too complex
        subsample=0.8,             # The model trains on 80% of the data each time (which improves its performance)
        scale_pos_weight=tuned_weight, 
        random_state=42,
        eval_metric='logloss'
    )
    
    xgb_model.fit(X_train, y_train)

    y_pred = xgb_model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\n🎯 OVERALL ACCURACY: {accuracy:.2%}")
    print("\n📊 DETAILED AI PERFORMANCE REPORT:")
    print(classification_report(y_test, y_pred, target_names=['Stay (0)', 'Leave (1)']))

    # ==========================================
    # 5. Predict Flight Risk for ACTIVE Employees
    # ==========================================
    print("🔮 Scoring Current Active Employees...")
    
    active_mask = df['EmployeeStatus'] == 'Active'
    active_employees = df[active_mask].copy()
    X_active = X[active_mask].copy()

    if len(X_active) > 0:
        risk_probabilities = xgb_model.predict_proba(X_active)[:, 1]
        active_employees['FlightRiskScore'] = (risk_probabilities * 100).round(2)
        
        high_risk_df = active_employees[['FullName', 'Email', 'PayZone', 'SatisfactionScore', 'FlightRiskScore']].sort_values(by='FlightRiskScore', ascending=False)
        
        print("\n🚨 TOP 5 EMPLOYEES AT HIGHEST RISK OF RESIGNING:")
        print(high_risk_df.head(5).to_string(index=False))
        
        return high_risk_df
    else:
        print("No active employees found to score.")
        return None

# ==========================================
# 6. Automated Email Alert System
# ==========================================
def send_hr_alert_email(high_risk_df):
    print("📧 Preparing Automated HR Alert Email...")
    
    # --- EMAIL CREDENTIALS ---
    # NOTE: Do not use your real password! Use an "App Password" (explained below)
    sender_email = "hazemmuhammmeddd1@gmail.com"  # Replace with your email
    sender_password = "vqdsjxvipsclvvzd" # Replace with App Password
    receiver_email = "hazemmuhammedd1@gmail.com" # Send it to yourself for testing!
    
    msg = MIMEMultipart()
    msg['Subject'] = "🚨 URGENT: High Flight Risk Employees Detected"
    msg['From'] = "HR Predictive Engine"
    msg['To'] = receiver_email

    # Convert the Top 5 DataFrame to a clean HTML table
    html_table = high_risk_df.to_html(index=False, border=1, justify='center')

    # Design the Email Body using HTML/CSS
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <div style="background-color: #f8d7da; padding: 15px; border-radius: 5px; border: 1px solid #f5c6cb;">
            <h2 style="color: #721c24; margin: 0;">Automated HR Alert: Flight Risk Prediction</h2>
        </div>
        <p>Dear HR Director,</p>
        <p>Our AI Predictive Engine has just completed its latest analysis. The following active employees have been identified as having a <strong>critical probability of resigning</strong> soon based on historical attrition patterns.</p>
        <p>Please review their profiles and consider proactive retention strategies (e.g., 1-on-1 check-ins, compensation review).</p>
        
        <div style="margin-top: 20px; margin-bottom: 20px;">
            {html_table}
        </div>
        
        <p style="font-size: 12px; color: #777;">
            <em>This is an automated message generated by the HR Intelligent System. Do not reply directly to this email.</em>
        </p>
      </body>
    </html>
    """
    
    msg.attach(MIMEText(html_content, 'html'))

    try:
        # Connect to Gmail's SMTP Server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls() # Secure the connection
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print("✅ Alert Email Sent Successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

if __name__ == "__main__":
    run_ml_pipeline()
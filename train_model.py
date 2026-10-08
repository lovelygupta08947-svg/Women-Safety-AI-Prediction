import os, pandas as pd, joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

os.makedirs("model",exist_ok=True)
data=pd.read_csv("dataset/crime_data.csv")
features=["crime_frequency","night_crime_rate","harassment_cases","assault_cases","police_proximity"]
X=data[features]
y=data["risk_level"]
enc=LabelEncoder()
yy=enc.fit_transform(y)
Xtr,Xte,ytr,yte=train_test_split(X,yy,test_size=.2,random_state=42,stratify=yy)
model=RandomForestClassifier(n_estimators=250,random_state=42)
model.fit(Xtr,ytr)
pred=model.predict(Xte)
print(f"Model Accuracy: {accuracy_score(yte,pred):.2%}")
print(classification_report(yte,pred,target_names=enc.classes_,zero_division=0))
joblib.dump(model,"model/safety_model.pkl")
joblib.dump(enc,"model/label_encoder.pkl")
print("Model files created successfully in model/.")

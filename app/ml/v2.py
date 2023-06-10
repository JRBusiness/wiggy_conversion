import numpy as np
import pandas as pd
from keras.models import Sequential
from keras.layers import LSTM, Dense
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split

n_days = 60
n_features = 8
n_future = 1

def create_dataset(df):
    data = df.values
    x = []
    y = []
    for i in range(n_days, len(data)-n_future+1):
        x.append(data[i-n_days:i])
        y.append(data[i:i+n_future])
    return np.array(x), np.array(y)

def create_model(n_days, n_features):
    model = Sequential()
    model.add(LSTM(50, activation='relu', return_sequences=True, input_shape=(n_days, n_features)))
    model.add(LSTM(50, activation='relu'))
    model.add(Dense(n_future))
    model.compile(optimizer='adam', loss='mse')
    return model

def train_model(model, x, y):
    model.fit(x, y, epochs=200, verbose=0)

def predict_next_n_days(model, last_n_days, n_future):
    last_n_days_scaled = scaler.transform(last_n_days)
    x = np.reshape(last_n_days_scaled, (1, n_days, n_features))
    predictions = model.predict(x)
    predictions = scaler.inverse_transform(predictions)
    return predictions

def get_indicators_and_pattern(df, last_n_days):
    # Get the row in df corresponding to last_n_days
    row = df[df.index.isin(last_n_days.index)]
    indicators = row.drop(columns=['open', 'high', 'low', 'close']).idxmax(axis=1)
    pattern = indicators.mode().iloc[0]
    return indicators.tolist(), pattern

# Use MinMaxScaler to scale the data
scaler = MinMaxScaler()
df_scaled = pd.DataFrame(scaler.fit_transform(df), columns=df.columns)

# Create the dataset
x, y = create_dataset(df_scaled)

# Split the data into training and testing datasets
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)

# Create and train the model
model = create_model(n_days, n_features)
train_model(model, x_train, y_train)

# Make a prediction
last_n_days = df_scaled.tail(n_days)
predictions = predict_next_n_days(model, last_n_days, n_future)

# Determine the indicators and pattern used for the prediction
indicators, pattern = get_indicators_and_pattern(df, last_n_days)

# Output the prediction, indicators, pattern, and confidence level
print('Prediction: ', predictions)
print('Indicators: ', indicators)
print('Pattern: ', pattern)
print('Confidence Level: ', model.evaluate(x_test, y_test, verbose=0))

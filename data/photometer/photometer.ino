const int analogInPin = A7;
const int sensorPin1 = 3;
const int sensorPin2 = 4;

float intensity = 0;   
int sensorState = 0;
unsigned long startTime = 0;

void setup() {
  Serial.begin(9600);
  pinMode(sensorPin1, OUTPUT);
  pinMode(sensorPin2, OUTPUT);
  startTime = millis();
  
}

void loop() {
  digitalWrite(sensorPin1, LOW);
  digitalWrite(sensorPin2, LOW);
  
  int activePin = 0;
  
  if (sensorState == 0) {
    digitalWrite(sensorPin1, HIGH);
    activePin = sensorPin1;
    sensorState = 1;
  } else {
    digitalWrite(sensorPin2, HIGH);
    activePin = sensorPin2;
    sensorState = 0;
  }
  
  intensity = analogRead(analogInPin);
  intensity = (intensity / 1023.0) * 5.0;
  
  // Вывод времени в формате с:мс
  unsigned long currentTime = millis() - startTime;
  unsigned long seconds = currentTime / 1000;
  unsigned long milliseconds = currentTime % 1000;
  
  Serial.print(seconds);
  Serial.print(":");
  Serial.print(milliseconds);
  Serial.print("\t\t");
  Serial.print(activePin);
  Serial.print("\t\t");
  Serial.println(intensity, 3);
  
  delay(300);
}


const int ECG_PIN = D0;

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);
  analogSetPinAttenuation(ECG_PIN, ADC_11db);

  delay(1000);
  Serial.println("Lectura D0");
}

void loop() {
  int lectura = analogRead(ECG_PIN);

  Serial.println(lectura);

  delay(4);
}

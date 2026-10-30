const int ECG_PIN = D0;

const uint32_t SAMPLE_RATE = 250;
const uint32_t SAMPLE_PERIOD_US = 1000000UL / SAMPLE_RATE;

uint32_t nextSample = 0;

void setup() {
  Serial.begin(115200);

  analogReadResolution(12);
  analogSetPinAttenuation(ECG_PIN, ADC_11db);

  delay(1000);
  Serial.println("ECG_START");

  nextSample = micros();
}

void loop() {
  uint32_t now = micros();

  if ((int32_t)(now - nextSample) >= 0) {
    int ecgRaw = analogRead(ECG_PIN);
    Serial.println(ecgRaw);

    nextSample = now + SAMPLE_PERIOD_US;
  }
}

/*
  ECG - AD8232 + Arduino UNO
  Frecuencia de muestreo: 250 Hz
  Salida serial: 115200 baudios
*/

const int ECG_PIN = A0;
const int LO_PLUS = 10;
const int LO_MINUS = 11;

const unsigned long SAMPLE_PERIOD_US = 4000;

unsigned long previousMicros = 0;

void setup() {

  Serial.begin(115200);

  pinMode(LO_PLUS, INPUT);
  pinMode(LO_MINUS, INPUT);

  analogReference(DEFAULT);

  delay(1000);

  Serial.println("ECG_START");
}

void loop() {

  unsigned long currentMicros = micros();

  if (currentMicros - previousMicros >= SAMPLE_PERIOD_US) {

    previousMicros += SAMPLE_PERIOD_US;

    // Verificar desconexion de electrodos
    if (digitalRead(LO_PLUS) == HIGH ||
        digitalRead(LO_MINUS) == HIGH) {

      Serial.println("LEADS_OFF");

    } else {

      int ecgValue = analogRead(ECG_PIN);

      Serial.println(ecgValue);
    }
  }
}

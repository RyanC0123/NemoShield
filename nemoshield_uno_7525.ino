// NemoShield - Arduino 101 firmware
//
// Wiring
//   D8  -> 220R -> Green LED  -> GND
//   D9  -> 220R -> Yellow LED -> GND
//   D10 -> 220R -> Red LED    -> GND
//   D11 -> Buzzer (+), Buzzer (-) -> GND
//   D2  -> Button -> GND   (INPUT_PULLUP, pressed = LOW)
//   Board GND -> breadboard (-) rail
//
// Serial protocol (agreed with backend), 9600 baud, one command per line
//   NORMAL    -> green on                         -> ACK:NORMAL
//   WARNING   -> yellow slow blink                -> ACK:WARNING
//   CRITICAL  -> red fast blink + buzzer alarm    -> ACK:CRITICAL
//   CLEAR     -> alarm off, back to green         -> ACK:CLEAR
//   PING      -> no change                        -> ACK:PING
//   STATUS    -> no change                        -> STATUS:<state>
//   anything else                                 -> ERR:UNKNOWN
// Unsolicited from Arduino
//   READY     after boot
//   BUTTON_ACK  when the physical button is pressed (also mutes the buzzer)

const uint8_t PIN_GREEN  = 8;
const uint8_t PIN_YELLOW = 9;
const uint8_t PIN_RED    = 10;
const uint8_t PIN_BUZZER = 11;
const uint8_t PIN_BUTTON = 2;

const unsigned long DEBOUNCE_MS = 30;

enum State { NORMAL, WARNING, CRITICAL };
State state = NORMAL;
bool muted = false;

char lineBuf[32];
uint8_t lineLen = 0;
bool lineOverflow = false;

bool lastReading = HIGH;
bool stableButton = HIGH;
unsigned long lastBounce = 0;

unsigned int currentTone = 0;

const char* stateName(State s) {
  switch (s) {
    case WARNING:  return "WARNING";
    case CRITICAL: return "CRITICAL";
    default:       return "NORMAL";
  }
}

void setLeds(bool g, bool y, bool r) {
  digitalWrite(PIN_GREEN,  g);
  digitalWrite(PIN_YELLOW, y);
  digitalWrite(PIN_RED,    r);
}

void setTone(unsigned int freq) {
  if (freq == currentTone) return;
  currentTone = freq;
  if (freq == 0) noTone(PIN_BUZZER);
  else tone(PIN_BUZZER, freq);
}

bool blink(unsigned long now, unsigned long periodMs) {
  return (now / periodMs) % 2 == 0;
}

void lampTest() {
  setLeds(1, 0, 0); delay(200);
  setLeds(0, 1, 0); delay(200);
  setLeds(0, 0, 1); delay(200);
  tone(PIN_BUZZER, 2000, 100); delay(150);
  noTone(PIN_BUZZER);
  setLeds(0, 0, 0);
}

// Non-blocking output, called every loop
void render(unsigned long now) {
  switch (state) {
    case NORMAL:
      setLeds(1, 0, 0);
      setTone(0);
      break;
    case WARNING:
      setLeds(0, blink(now, 500), 0);              // slow blink
      setTone(0);
      break;
    case CRITICAL:
      setLeds(0, 0, blink(now, 120));              // fast blink
      setTone(muted ? 0 : (blink(now, 300) ? 1000 : 1500));  // siren
      break;
  }
}

void ack(const char* cmd) {
  Serial.print("ACK:");
  Serial.println(cmd);
}

void handleCommand(char* cmd) {
  for (char* p = cmd; *p; p++) *p = toupper(*p);
  // trim trailing spaces
  int n = strlen(cmd);
  while (n > 0 && cmd[n - 1] == ' ') cmd[--n] = '\0';

  if (strcmp(cmd, "NORMAL") == 0) {
    state = NORMAL; muted = false; ack("NORMAL");
  } else if (strcmp(cmd, "WARNING") == 0) {
    state = WARNING; muted = false; ack("WARNING");
  } else if (strcmp(cmd, "CRITICAL") == 0) {
    state = CRITICAL; muted = false; ack("CRITICAL");
  } else if (strcmp(cmd, "CLEAR") == 0) {
    state = NORMAL; muted = false; ack("CLEAR");
  } else if (strcmp(cmd, "PING") == 0) {
    ack("PING");
  } else if (strcmp(cmd, "STATUS") == 0) {
    Serial.print("STATUS:");
    Serial.println(stateName(state));
  } else if (n > 0) {
    Serial.println("ERR:UNKNOWN");
  }
}

void readSerial() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\r') continue;
    if (c == '\n') {
      lineBuf[lineLen] = '\0';
      if (lineOverflow) Serial.println("ERR:TOO_LONG");
      else handleCommand(lineBuf);
      lineLen = 0;
      lineOverflow = false;
    } else if (lineLen < sizeof(lineBuf) - 1) {
      lineBuf[lineLen++] = c;
    } else {
      lineOverflow = true;
    }
  }
}

void checkButton(unsigned long now) {
  bool reading = digitalRead(PIN_BUTTON);
  if (reading != lastReading) {
    lastBounce = now;
    lastReading = reading;
  }
  if (now - lastBounce > DEBOUNCE_MS && reading != stableButton) {
    stableButton = reading;
    if (stableButton == LOW) {
      Serial.println("BUTTON_ACK");
      if (state == CRITICAL) muted = true;
    }
  }
}

void setup() {
  pinMode(PIN_GREEN, OUTPUT);
  pinMode(PIN_YELLOW, OUTPUT);
  pinMode(PIN_RED, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_BUTTON, INPUT_PULLUP);

  Serial.begin(9600);
  lampTest();
  Serial.println("READY");
}

void loop() {
  unsigned long now = millis();
  readSerial();
  checkButton(now);
  render(now);
}

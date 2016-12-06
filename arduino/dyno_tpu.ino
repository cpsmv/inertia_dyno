#include <TimerOne.h>
#include <avr/wdt.h> //used for restarting the Arduino on command

#define HALL_EFFECT_PIN 2
#define SAMPLE_PERIOD_US 5000 // microseconds (200 Hz sample rate)
#define BAUD_RATE 115200 

// keep track of the last time between flywheel teeth passing the hall effect sensor
uint32_t time_between_teeth = 0;

void setup() {

  // Turn off the watchdog timer
  wdt_disable();
  
  // start serial uart stuff
  Serial.begin(BAUD_RATE);

  // setup a falling edge interrupt on Arduino pin 2 and attach an ISR
  pinMode(HALL_EFFECT_PIN, INPUT);
  attachInterrupt(digitalPinToInterrupt(HALL_EFFECT_PIN), hall_effect_isr, FALLING);

  // Handshake with the python script before sending out data
  bool python_handshake = false;

  // Loop continuously while waiting for Python script initialize and confirm handshake
  while (python_handshake == false) {
    if (Serial.available()){
      Serial.println("here");
      // Read in the handshake bytes
      char ser_in[15] = "0";
      Serial.readBytesUntil('\n', ser_in, 15);
      // Convert the bytes to Arduino's String type
      String ser_in_str = String(ser_in);
      // Check if the python script is requesting the type of Arduino (this script is for the hall effect one)
      if (ser_in_str == "handshake_type") {
        Serial.println("hall_effect");
      }
      // Or see if Python wants to confirm it is done handshaking and for the Arduino to start outputting data
      else if (ser_in_str == "handshake_ok") {
        python_handshake = true;
      }
    }
  }
  // once handshaking is complete, setup a 1kHz timer that samples the teeth timing at a 1KHz rate
  Timer1.initialize(200);
  Timer1.attachInterrupt(sampling_isr);
}

void loop() {
  // Check for the "reboot_now" message, signaling for the Arduino that it is time to reboot
  if (Serial.available()) {
    // Read in any bytes from Python
    char ser_in[15] = "0";
    Serial.readBytesUntil('\n', ser_in, 15);
    // Convert the bytes to Arduino's String type
    String ser_in_str = String(ser_in);
    // Check if the python script has requested that the Arduino reboot
    if (ser_in_str == "reboot_now") {
      // Enable watchdog timer for 250ms expiration. 
      // Since we won't be "kicking the dog", this will restart the Arduino upon expiration
      wdt_enable(WDTO_250MS);
    }
  }
}

// this interrupt service routine executes at the sampling rate
// it sends out the current value in the time_between_teeth variable over Serial to the Python script
void sampling_isr(void) {
  // ensure timing is greater than 0 (only would fail if the timing is greater than 16777216)
  if (time_between_teeth > 0) {
    // only send one byte if timing value can be represented by one byte
    if (time_between_teeth < 256) {
      Serial.write(time_between_teeth);
      Serial.print('\n');
    }
    // send 2 bytes, big-endian, if the timing value can be represented by two bytes
    else if (time_between_teeth < 65536) {
      Serial.write(time_between_teeth>>8);
      Serial.write(time_between_teeth);
      Serial.print('\n');
    }
    // send 3 bytes, big-endian, if the timing value needs 3 bytes
    else if (time_between_teeth < 16777216) {
      Serial.write(time_between_teeth>>16);
      Serial.write(time_between_teeth>>8);
      Serial.write(time_between_teeth);
      Serial.print('\n');
    }
    // don't send timing value if it needs 4 bytes
    // Python will detect this and automatically record a 0 for RPM
  }
}

void hall_effect_isr(void) {
  // remember the last tooth timing
  static uint32_t last_tooth_time = 0;
  // only proceed if one tooth has already passed and time has been recorded
  if (last_tooth_time != 0) {
    // get the current time for a new tooth passing
    uint32_t new_tooth_time = micros();
    // update teeth timing variable
    time_between_teeth = new_tooth_time-last_tooth_time;
    // record this tooth passing time for next time around the ISR
    last_tooth_time = new_tooth_time;
  }
  // no teeth have passed yet, so only save the current time
  else {
    last_tooth_time = micros();
  }
}


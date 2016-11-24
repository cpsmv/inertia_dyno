#include <TimerOne.h>
#include <avr/wdt.h> //used for restarting the Arduino on command

#define HALL_EFFECT_LEFT 2
#define HALL_EFFECT_RIGHT 3
#define SAMPLE_PERIOD_US 5000 // microseconds (200 Hz sample rate)
#define BAUD_RATE 115200 

uint16_t blah = 30020;

void setup() {

  // Turn off the watchdog timer
  wdt_disable();
  
  // start serial uart stuff
  Serial.begin(BAUD_RATE);
  
  /*pinMode(HALL_EFFECT_LEFT, INPUT);
  attachInterrupt(digitalPinToInterrupt(HALL_EFFECT_LEFT), hall_effect_left_isr, FALLING);*/

  // Handshake with the python script before sending out data
  bool python_handshake = false;

  // Loop continuously while waiting for Python script initialize and confirm handshake
  while (python_handshake == false) {
    
    if (Serial.available()){
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

  Timer1.initialize(blah);
  Timer1.attachInterrupt(hall_effect_left_isr);
}

void loop() {

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
    /*else if (ser_in_str == "l") {
      hall_effect_left_isr();
    }*/
  }
}

void hall_effect_left_isr(void) {
  static uint32_t last_time = 0;
  if (last_time != 0) {
    uint32_t new_time = micros();
    uint32_t time_diff = new_time-last_time;
    if (time_diff <= 255) {
      Serial.print((char)time_diff);
      Serial.print('\n');
    }
    else if (time_diff <= 65535) {
      Serial.print((char)(time_diff>>8));
      Serial.print((char)time_diff);
      Serial.print('\n');
    }
    else {
      Serial.print((char)time_diff>>24);
      Serial.print((char)time_diff>>16);
      Serial.print((char)time_diff>>8);
      Serial.print((char)time_diff);
      Serial.print('\n');
    }
    //Serial.println(time_diff);
    last_time = new_time;
  }
  else {
    last_time = micros();
  }
  blah = blah - 40;
  Timer1.setPeriod(blah);
}


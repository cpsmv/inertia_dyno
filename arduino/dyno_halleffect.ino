#include <TimerOne.h>
#include <avr/wdt.h> //for restarting the Arduino on command

#define HALL_EFFECT_LEFT 2
#define HALL_EFFECT_RIGHT 3
#define SAMPLE_PERIOD_US 5000 // microseconds (200 Hz sample rate)
#define BAUD_RATE 115200 

uint8_t num_teeth_left = 0;
uint8_t num_teeth_right = 0;

void setup() {

  // Turn off the watchdog timer
  wdt_disable();
  
  // start serial uart stuff
  Serial.begin(BAUD_RATE);
  
  /*pinMode(HALL_EFFECT_LEFT, INPUT);
  attachInterrupt(digitalPinToInterrupt(HALL_EFFECT_LEFT), hall_effect_left_isr, FALLING);
  pinMode(HALL_EFFECT_RIGHT, INPUT);
  attachInterrupt(digitalPinToInterrupt(HALL_EFFECT_RIGHT), hall_effect_right_isr, FALLING);*/

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

  // Handshake completed successfully
  // Set timer1 to a 200Hz rate and attach an ISR which sends out the speed data to the timer's interrupt
  Timer1.initialize(SAMPLE_PERIOD_US);  // send data every 5000 us (200Hz)
  Timer1.attachInterrupt(data_to_python_isr);
}

void loop() {
  // Make bs speed data (for offline testing)
  static uint16_t skip = 0;
  if (skip == 0) {
    num_teeth_left++;
    num_teeth_right++;
  }
  skip<10000 ? skip++ : skip=0;

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

void data_to_python_isr(void) {
  // Send out speed data
  Serial.print("L");
  Serial.print(num_teeth_left);
  Serial.print(";");
  Serial.print("R");
  Serial.println(num_teeth_left);
  // Reset the number of teeth that have passed
  //num_teeth_left = 0;
  //num_teeth_right = 0;
}


void hall_effect_left_isr(void) {
  num_teeth_left++;
}

void hall_effect_right_isr(void) {
  num_teeth_right++;
}


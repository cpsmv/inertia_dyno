#include <TimerOne.h>
#include <avr/wdt.h>                    //used for restarting the Arduino on command

#define HALL_EFFECT_PIN 2
#define SAMPLE_PERIOD_US 5000           // microseconds (200 Hz sample rate)
#define BAUD_RATE 115200 

uint32_t time_between_teeth = 1048576;  // keep track of the last time between flywheel teeth passing the hall effect sensor (initialize to 2^20 = 0x100000)

void setup() {

  wdt_disable();                                // Turn off the watchdog timer
  Serial.begin(BAUD_RATE);                      // start serial uart stuff

  // setup a falling edge interrupt on Arduino pin 2 and attach an ISR
  /*pinMode(HALL_EFFECT_PIN, INPUT);
  attachInterrupt(digitalPinToInterrupt(HALL_EFFECT_PIN), hall_effect_isr, FALLING);*/

  bool python_handshake = false;                // Handshake with the python script before sending out data

  while (python_handshake == false) {           // Loop continuously while waiting for Python script initialize and confirm handshake
    if (Serial.available()){
      char ser_in[15] = "0";                    // Read in the handshake bytes
      Serial.readBytesUntil('\n', ser_in, 15);
      String ser_in_str = String(ser_in);       // Convert the bytes to Arduino's String type
      
      if (ser_in_str == "handshake_type") {     // Check if the python script is requesting the type of Arduino (this script is for the hall effect one)
        Serial.println("tpu");
      }
      else if (ser_in_str == "handshake_ok") {  // Or see if Python wants to confirm it is done handshaking and for the Arduino to start outputting data
        python_handshake = true;
      }
    }
  }
  Timer1.initialize(1000);                     // once handshaking is complete, setup a 1kHz timer that samples the teeth timing at a 1KHz rate
  Timer1.attachInterrupt(sampling_isr);
}

void loop() {
  
  if (Serial.available()) {                   // Check for the "reboot_now" message, signaling for the Arduino that it is time to reboot
    char ser_in[15] = "0";                    // Read in any bytes from Python
    Serial.readBytesUntil('\n', ser_in, 15);
    String ser_in_str = String(ser_in);       // Convert the bytes to Arduino's String type
    
    if (ser_in_str == "reboot_now") {         // Check if the python script has requested that the Arduino reboot             
      wdt_enable(WDTO_250MS);                 // Enable watchdog timer for 250ms expiration.
                                              // Since we won't be "kicking the dog", this will restart the Arduino upon expiration
    }
  }
  //time_between_teeth > 2000000 ? time_between_teeth = 500 : time_between_teeth++;
}
                                            // this interrupt service routine executes at the sampling rate
void sampling_isr(void) {                   // it sends out the current value in the time_between_teeth variable over Serial to the Python script
                                            
                                            // only send teeth timing if its less than 1.048576 seconds (the hex equivalent of 1048575 is 0xFFFFF)
  if (time_between_teeth < 1048576) {       // this ensures that only a max of 5 bytes + an endline character are transmitted over serial
    Serial.print(time_between_teeth, HEX);  // send teeth timing in HEX form, encoded with ascii characters
    Serial.print('\n');                     // newline character so Python can detect the end of the line (Serial.println() appends '/r/n', which is undesireable) 
  }
}

void hall_effect_isr(void) {
  
  static uint32_t last_tooth_time = 0;                    // remember the last tooth timing
  static uint32_t prev_time_between_teeth = 0;            // remember 
  
  if (last_tooth_time != 0) {                             // only proceed if one tooth has already passed and time has been recorded
    uint32_t new_tooth_time = micros();                   // get the current time for a new tooth passing
    time_between_teeth = new_tooth_time-last_tooth_time;  // update teeth timing variable
    
    /* uint32_t threshold = (prev_time_between_teeth >> 1) + (prev_time_between_teeth >> 4);
    if (time_between_teeth < 66636 && time_between_teeth < threshold) {
      time_between_teeth = prev_time_between_teeth;
    }*/
    
    last_tooth_time = new_tooth_time;                     // record this tooth passing time for next time around the ISR
    prev_time_between_teeth = time_between_teeth;
  }
  else {
    last_tooth_time = micros();                           // no teeth have passed yet, so only save the current time
  }
}


#include <TimerOne.h>

#define HALL_EFFECT_LEFT 2
#define HALL_EFFECT_RIGHT 3

uint8_t num_teeth_left = 0;
uint8_t num_teeth_right = 0;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  
  /*pinMode(HALL_EFFECT_LEFT, INPUT);
  attachInterrupt(digitalPinToInterrupt(HALL_EFFECT_LEFT), hall_effect_left_isr, FALLING);
  pinMode(HALL_EFFECT_RIGHT, INPUT);
  attachInterrupt(digitalPinToInterrupt(HALL_EFFECT_RIGHT), hall_effect_right_isr, FALLING);*/
  
  Timer1.initialize(200000);  // send data every 5000 us (200Hz)
  Timer1.attachInterrupt(data_to_python_isr);
}

void loop() {
  // put your main code here, to run repeatedly:
  num_teeth_left = 2;
  num_teeth_right = 10;
}

void data_to_python_isr(void) {
  Serial.print("L");
  Serial.print(num_teeth_left);
  Serial.print(";");
  Serial.print("R");
  Serial.println(num_teeth_left);
  num_teeth_left = 0;
  num_teeth_right = 0;
}


void hall_effect_left_isr(void) {
  num_teeth_left++;
}

void hall_effect_right_isr(void) {
  num_teeth_right++;
}


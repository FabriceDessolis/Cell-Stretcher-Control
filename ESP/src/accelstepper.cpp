#define pi 3.14159

#include <AccelStepper.h>

const int enPin = 27;
const int stepXPin = 25;
const int dirXPin = 26;
const int stepYPin = 3;
const int dirYPin = 6;

const int microstepping = 16;
const float stepsPerRev = 200*microstepping;

const int radAccel = 200; // rad/s²
const int stepAccel = (stepsPerRev * radAccel) / (2*pi);

const int max_rpm = 283; // tr/mn
long int max_speed = (stepsPerRev * max_rpm) / 60;

const int radTarget = 15; // rad, approximation from 3.375
const int stepTarget = (stepsPerRev * radTarget) / (2*pi);

long int max_speedX = max_speed;


AccelStepper stepperX(AccelStepper::DRIVER, stepXPin, dirXPin);

void setup()
{  
  Serial.begin(9600);
  stepperX.setEnablePin(enPin);
  stepperX.setPinsInverted(false, false, true); //dir, step, enable
  stepperX.enableOutputs();
  
  /*
  // constant speed
  stepperX.moveTo(stepTarget/2);
  stepperX.setMaxSpeed(max_speed);
  stepperX.setSpeed(max_speed);
  */
  
  // implement acceleration
  stepperX.moveTo(stepTarget);
  stepperX.setMaxSpeed(500000);
  stepperX.setAcceleration(stepAccel);  
  

  Serial.println(stepTarget);
  Serial.println(max_speed);
}

void loop()
{ 
  int run_motors = 1;

  if (run_motors == 1)
  {
    
    // If at the end of travel go to the other end
    if (stepperX.distanceToGo() == 0)
    {
      //max_speedX = -max_speedX;
      stepperX.moveTo(-stepperX.currentPosition());
      //stepperX.setSpeed(max_speedX);
    }
    
    
    //stepperX.runSpeed();
    stepperX.run();
  }
}
 
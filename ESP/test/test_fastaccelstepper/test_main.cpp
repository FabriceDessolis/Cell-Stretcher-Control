#define pi 3.14159

#include <FastAccelStepper.h>

const int enPin = 4;
const int stepXPin = 2;
const int dirXPin = 5;
const int stepYPin = 3;
const int dirYPin = 6;

const int microstepping = 16;
const float stepsPerRev = 200*microstepping;

const int radAccel = 59; // rad/s²
const int stepAccel = (stepsPerRev * radAccel) / (2*pi);

const int max_rpm = 283; // tr/mn
long int max_speed = (stepsPerRev * max_rpm) / 60;

const int radTarget = 15; // rad, approximation from 3.375
const int stepTarget = (stepsPerRev * radTarget) / (2*pi);

long int max_speedX = max_speed;


FastAccelStepper engine = FastAccelStepperEngine();
FastAccelStepper *stepper = NULL;

void setup()
{ 
    Serial.begin(115200);
    engine.init();
    stepper = engine.stepperConnectToPin(stepXPin);
    if (stepper)
    {
        stepper->setDirectionPin(dirXPin);
        stepper->setEnablePin(enPin);
        stepper->setAutoEnable(true);
        
        stepper->setSpeedInHz(2*max_speed);
        stepper->setAcceleration(stepAccel);
        stepper->moveTo(stepTarget/2, true);
    }

  Serial.println(stepTarget);
  Serial.println(max_speed);      
}

void loop()
{ 
  int run_motors = 0;

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

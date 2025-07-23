#define pi 3.14159

#include <FastAccelStepper.h>

const int enPin = 4;
const int stepXPin = 2;
const int dirXPin = 5;

const int microstepping = 16;
const float stepsPerRev = 200*microstepping;

const int radAccel = 59; // rad/s²
const int stepAccel = (stepsPerRev * radAccel) / (2*pi);

const int max_rpm = 283; // tr/mn
long int max_speed = (stepsPerRev * max_rpm) / 60;

const int radTarget = 15; // rad, approximation from 3.375
const int stepTarget = (stepsPerRev * radTarget) / (2*pi);

long int max_speedX = max_speed;


FastAccelStepperEngine engine = FastAccelStepperEngine();
FastAccelStepper *stepper = NULL;

void setup()
{ 
  
  engine.init();
  stepper = engine.stepperConnectToPin(stepXPin);

  stepper->setDirectionPin(dirXPin);
  stepper->setEnablePin(enPin);
  stepper->setAutoEnable(true);
  
  stepper->setSpeedInHz(2*max_speed);
  stepper->setAcceleration(stepAccel);
  stepper->moveTo(stepTarget/2, true);
  stepper->moveTo(0, true);
  
  Serial.begin(9600);
  Serial.println(stepTarget);
  Serial.println(max_speed);      
}

void loop()
{ 
  int run_motors = 1;

  if (run_motors == 1)
  {
    // If at the end of travel go to the other end
    if (stepper->getCurrentPosition() == stepper->targetPos())
    {
      //max_speedX = -max_speedX;
      stepper->moveTo(-stepTarget/2);
      //stepperX.setSpeed(max_speedX);
    }

  }
}

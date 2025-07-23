#include <Arduino.h>
#include <AccelStepper.h>
#define pi 3.14159

// arduino pins
const int enPin = 27;
const int stepPin = 25;
const int dirPin = 26;

// Microstepping, screw pitch, gear reduction
const int Microstepping = 16;
const float stepsPerRev = 200*Microstepping;
const int gearRatio = 2;
const float screwPitch = 2.54;
const float l0 = 10; // the initial distance when the stretch is 0%, in mm


// ************************************************************************************************
// --------------------------- HEY ACHYUTH THIS IS THE PART YOU CAN MODIFY ------------------------
                                                                                                 // 
// experiment settings                                                                           //
bool linear = false; // if false its cyclic                                                       //
const float frequency = 0.2;    // desired frequency in Hz                                       //
const float final_stretch = 20; // desired final stretch in %                                   //
namespace Duration                                                                               //     
{                                                                                                //
    const int seconds = 10; // total duration to go from 0% to the final stretch %, in seconds    //
    const int minutes = 0; // in minutes                                                         //         
    const int hours = 0; // in hours                                                             //     
    const int days = 0;                                                                          // 
}                                                                                                // 
// ----------------------------------------- IT ENDS HERE -----------------------------------------
// ************************************************************************************************

// mm to steps conversion
float distanceToGo = (final_stretch / 100) * l0; // total stroke to reach the final stretch, in mm
int totalSteps = (gearRatio * distanceToGo * stepsPerRev) / screwPitch; // totalSteps needed for half period

// find speed
float sps = totalSteps * 2 * frequency; // speed in steps per second

// timers and intervals
unsigned long durationMillis = Duration::seconds * 1e3 + Duration::minutes * 60e3 + Duration::hours * 3600e3 + Duration::days * 86400e3;
unsigned long previousMicros = 0;
float millisBetweenSteps = durationMillis / (1.0 * totalSteps);
int stepPulseMicros = 10;

// accelstepper library
AccelStepper stepper(AccelStepper::DRIVER, stepPin, dirPin);
bool forward = true;

// miscellaneous
bool printed = false;
int i = 0;

void singleStep()
{
    digitalWrite(stepPin, HIGH);
    //delayMicroseconds(stepPulseMicros);
    digitalWrite(stepPin, LOW);
    //delayMicroseconds(stepPulseMicros);
}

void setup()
{
    Serial.begin(115200);
    pinMode(enPin, OUTPUT);
    pinMode(stepPin, OUTPUT);
    pinMode(dirPin, OUTPUT);
    digitalWrite(enPin, LOW);
    digitalWrite(dirPin, HIGH);

    stepper.setEnablePin(enPin);
    stepper.setPinsInverted(false, false, true); //dir, step, enable
    stepper.enableOutputs();

    stepper.setMaxSpeed(sps);
    stepper.setSpeed(sps);    

    Serial.print("Distance to go : ");
    Serial.println(distanceToGo);
    Serial.print("Total steps : ");
    Serial.println(totalSteps);
    Serial.print("Millis between steps : ");
    Serial.println(millisBetweenSteps, 6);
    Serial.print("Duration Millis : ");
    Serial.println(durationMillis);
}

void loop()
{
    if(linear == true)
    {
        if (micros() - previousMicros >= millisBetweenSteps*1000 && i <= totalSteps) 
        {
            previousMicros = micros();
            singleStep();
            i++;
            Serial.print(i);
            Serial.print(" , millis : ");
            Serial.print(micros());
            Serial.print(" , previousMicros : ");
            Serial.println(previousMicros);

        }

        if (i >= totalSteps)
        {
            digitalWrite(enPin, HIGH);
            if (printed == false)
            {
                printed = true;
                Serial.print("Total time taken : ");
                Serial.println(millis());
            }
        }
    }
    else
    {
        if (stepper.distanceToGo() == 0)
        {
            if (forward)
            {
                stepper.moveTo(totalSteps);
                stepper.setSpeed(sps);
            }
            else
            {
                stepper.moveTo(0);
                stepper.setSpeed(-sps);
            }
            forward = !forward;
        }
        stepper.runSpeed();
    }
}
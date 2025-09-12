#include "task_manager.h"
#include <esp_timer.h>
#include <AccelStepper.h>
#include <Arduino.h>

#define pi 3.14159

Task::Task(int stepPin, int dirPin, int enPin)
    : m_stepPin {stepPin}, m_dirPin {dirPin}, m_enPin {enPin}, stepper(AccelStepper::DRIVER, stepPin, dirPin)
{
    Serial1.println("task initialized");
     
    pinMode(m_enPin, OUTPUT);
    pinMode(m_stepPin, OUTPUT);
    pinMode(m_dirPin, OUTPUT);

    stepper.setEnablePin(m_enPin);
    stepper.setPinsInverted(false, false, true); //dir, step, enable
    stepper.enableOutputs(); 

    digitalWrite(m_enPin, HIGH); // HIGH = not enabled
    digitalWrite(m_dirPin, HIGH);

    xTaskCreatePinnedToCore(
        Task::emitPosition,
        "position emitter",
        10000,
        this,
        2,
        &m_positionHandle,
        0
    );
}

void Task::emitPosition(void* param)
{
    Task* self = static_cast<Task*>(param);
    for (;;)
    {
        if (self->stepper.currentPosition() != self->current_position)
        {
            self->current_position = self->stepper.currentPosition();
            Serial1.println('<'+String(self->current_position)+'>');
        }
        vTaskDelay(200);
    }
}

void Task::startTask(int mode, float* params, char* duration)
{
    if (isRunning)
    {
        Serial1.println("Task already running, ignoring start command");
        return;
    }
    Serial1.println("Task started");
    m_mode = mode;
    m_min_stretch = params[0];
    m_max_stretch = params[1];
    m_frequency = params[2];
    m_ramp = params[3];
    m_hold = params[4];
    m_duration = duration;

    min_steps = stretch_to_absolute_steps(m_min_stretch);
    max_steps = stretch_to_absolute_steps(m_max_stretch);
    total_steps = max_steps - min_steps;
    calculate_durationMicros();

    microsBetweenSteps = durationMicros / total_steps;
    set_sps();
    digitalWrite(m_enPin, LOW);
    isRunning = true;
    startRTOS(m_mode);
}

void Task::endTask()
{
    Serial1.println("END TASK");
    digitalWrite(m_enPin, HIGH);
    isRunning = false;
    isPaused = false;
    forward = true;
}

void Task::startRTOS(int mode)
{
    if (m_taskHandle != nullptr)
    {
        vTaskDelete(m_taskHandle);
        m_taskHandle = nullptr;
    }
    TaskParam* param = new TaskParam{this, mode};

    xTaskCreatePinnedToCore(
        Task::taskFunction,
        "TaskMode",
        10000,
        param,
        2,
        &m_taskHandle,
        1);
}

void Task::taskFunction(void* param)
{
    TaskParam* taskParam = static_cast<TaskParam*>(param);
    Task* self = taskParam->instance;
    int mode = taskParam->mode;

    switch (mode)
    {
        case 1: self->run_ramp(); break;
        case 2: self->run_cyclic(); break;
        case 3: self->run_cyclicRamp(); break;
        case 4: self->run_holdUp(); break;
        case 5: self->run_holdDown(); break;
        default: break;
    }
    Serial1.println("DELETE TASK HANDLE");
    self->m_taskHandle = nullptr;
    vTaskDelete(nullptr);
    delete taskParam;
}

void Task::run_ramp()
{
    Serial1.println("min steps :");
    Serial1.println(min_steps);
    Serial1.println("current position :");   
    Serial1.println(stepper.currentPosition());
    int i = 0;
    if (min_steps != stepper.currentPosition())
    {
        stepperGoTo(min_steps);
    }
    digitalWrite(m_dirPin, HIGH);
    for(;;)
    {
        if (isPaused == false)
        {
            if (esp_timer_get_time() - previousMicros >= microsBetweenSteps && i <= total_steps) // si if use ticks instead
                {
                    previousMicros = esp_timer_get_time();
                    singleStep();
                    i++;
                }

            if (i >= total_steps)
            {
                endTask();
                break;
            }
        }
        if (isRunning == false)
        {
            stepperGoTo(0);
            endTask();
            break;
        }
        taskYIELD();
    }
}

void Task::run_cyclic()
{
    int counter;
    taskStartTime = esp_timer_get_time();
    taskEndTime = taskStartTime + durationMicros;
    for(;;)
    {
        if (counter > 100000) // to avoid calling esp timer get time each iteration
        {
            counter = 0;
            if (esp_timer_get_time() >= taskEndTime)
            {
                Serial1.println(">taskendtime");
                stepperGoTo(0);
                endTask();
                break;
            }
        }
        counter++;
        if (isPaused == false)
        {    
            if (stepper.distanceToGo() == 0)
            {
                if (forward)
                {
                    stepper.moveTo(max_steps);
                    stepper.setSpeed(sps);
                }
                else
                {
                    stepper.moveTo(min_steps);
                    stepper.setSpeed(-sps);
                }
                forward = !forward;
            }
            stepper.runSpeed();
        }
        if (isRunning == false)
        {
            stepperGoTo(0);
            endTask();
            break;
        }
        taskYIELD();
    }
}

void Task::run_cyclicRamp()
{

}

void Task::run_holdUp()
{

}

void Task::run_holdDown()
{
    
}

void Task::singleStep()
{
    digitalWrite(m_stepPin, HIGH);
    digitalWrite(m_stepPin, LOW);
    stepper.setCurrentPosition(stepper.currentPosition() + 1);
}

void Task::stepperGoTo(int step)
{
    Serial1.println(stepper.currentPosition());
    stepper.moveTo(step);
    if (stepper.currentPosition() - step > 0)
    {
        stepper.setSpeed(-sps);
    }
    else
    {
        stepper.setSpeed(sps);
    }
    while(stepper.distanceToGo() != 0)
    {
        stepper.runSpeed();
        taskYIELD();
    }
}


void Task::pause()
{
    if (isPaused == false && isRunning == true)
    {
        isPaused = true;
        taskPauseTime = esp_timer_get_time();
    }
}

void Task::resume()
{
    if (isPaused == true && isRunning == true)
    {
        isPaused = false;
        taskEndTime += esp_timer_get_time() - taskPauseTime;
    }
}

void Task::abort()
{
    isRunning = false;
}

void Task::debug()
{
    Serial1.println("is running :");
    Serial1.println(isRunning);
    Serial1.println("is paused :");
    Serial1.println(isPaused);
}

void Task::set_sps()
{
    sps = total_steps * 2 * m_frequency; // speed in steps per second
    if (sps == 0)
    {
        sps = 2000; // in case we are in linear motion
    }
    stepper.setMaxSpeed(sps);
    stepper.setSpeed(sps);   
}

int Task::stretch_to_absolute_steps(float stretch)
{
    return (gearRatio * (stretch / 100) * l0 * stepsPerRev) / screwPitch; // totalSteps needed for half period
}

void Task::calculate_durationMicros()
// Extracts the float format of the duration "DDHHMN" to convert it in total microseconds
{
    int days = (m_duration[0] - '0') * 10 + m_duration[1] - '0';
    int hours = (m_duration[2] - '0') * 10 + m_duration[3] - '0';
    int minutes = (m_duration[4] - '0') * 10 + m_duration[5] - '0';

    durationMicros = minutes * 60ULL * 1000000ULL 
                   + hours * 3600ULL * 1000000ULL  
                   + days * 86400ULL * 1000000ULL ;
}


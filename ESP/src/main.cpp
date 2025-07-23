#include <Arduino.h>
#include "task_manager.h"
#include <iostream>

#define RX_PIN 1
#define TX_PIN 3

// esp pins
const int enPin = 27;
const int stepPin = 25;
const int dirPin = 26;

struct RcvdTask
{
    int mode {};
    float params[5];
    char duration[6];
};

RcvdTask rcvdtask;
Task task(stepPin, dirPin, enPin);

// for Serial read
const byte numChars = 32;
char receivedChars[numChars];
char tempChars[numChars];

bool newData = false;

uint32_t previousMicros = 0;
uint32_t now;
uint32_t interval = 1000000;

void rcvMessage()
{
    static bool rcvInProgress = false;
    static byte ndx = 0;
    char startMarker = '<';
    char endMarker = '>';
    char rc;

    while (Serial1.available() > 0 && newData == false)
    {
        rc = Serial1.read();
        if (rcvInProgress == true)
        {
            if (rc != endMarker)
            {
                receivedChars[ndx] = rc;
                ndx += 1;
                if (ndx >= numChars)
                {
                    ndx = numChars - 1;
                }
            }
            else
            {
                receivedChars[ndx] = '\0';
                ndx = 0;
                rcvInProgress = false;
                newData = true;
            }
        }
        else if (rc == startMarker)
        {
            rcvInProgress = true;
        } 
    }
}

void parseData() 
{
    char * strtokIndx;

    strtokIndx = strtok(tempChars, ",");
    rcvdtask.mode = atoi(strtokIndx);

    for (byte i = 0; i < 5; i++)
    {
        strtokIndx = strtok(NULL, ",");
        rcvdtask.params[i] = atof(strtokIndx);
    }

    strtokIndx = strtok(NULL, ",");
    strcpy(rcvdtask.duration, strtokIndx);
}

void sendData()
{
    // send data received to the task manager 
    char instruction = receivedChars[0];
    Serial1.println(instruction);
    if (isalpha(instruction))
    {
        switch(instruction)
        {
            case 'p':
                task.pause();
                break;
            case 'r':
                task.resume();
                break;
            case 'a':
                task.abort();
                break;
            case 'd':
                task.debug();
                break;
        }
    }
    else
    {
        Serial1.println("data sent, start task");
        task.startTask(rcvdtask.mode, rcvdtask.params, rcvdtask.duration);
    }
}

void TaskLoop(void * parameters) 
{
    for(;;)
    {
        /*
        now = esp_timer_get_time();
        if (now - previousMicros > interval)
        {
            previousMicros = now;
            Serial1.println("TaskLoop Listening");
        }
        */
        rcvMessage();
        if (newData == true)
        {
            strcpy(tempChars, receivedChars);
            if (isdigit(receivedChars[0]))
            {
                parseData();
            }
            sendData();
            newData = false;
        }
        vTaskDelay(10);     
    }
}

void setup() {
    // put your setup code here, to run once:

    Serial.begin(115200);
    Serial1.begin(115200, SERIAL_8N1, RX_PIN, TX_PIN);
    xTaskCreatePinnedToCore(
        TaskLoop,
        "loop",
        10000,
        NULL,
        2,
        NULL,
        0
    );

    // TESTS ----------------
    //task.startTask(rcvdtask.mode, rcvdtask.params, rcvdtask.duration);
}

void loop()
{
}

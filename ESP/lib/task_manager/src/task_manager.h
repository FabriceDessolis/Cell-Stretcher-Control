#ifndef TASK_MANAGER_H
#define TASK_MANAGER_H
#include <AccelStepper.h>

class Task 
{
    public:
        Task(int stepPin, int dirPin, int enPin);
        void startTask(int mode, float* params, char* duration);
        void endTask();
        void pause();
        void resume();
        void debug();
        void abort();
        
    private:
        // pins
        const int m_stepPin;
        const int m_dirPin;
        const int m_enPin;
        
        // stepper
        AccelStepper stepper;

        // settings
        int m_mode {};
        float m_params[6];
        float m_min_stretch {};
        float m_max_stretch {};
        float m_frequency {};
        float m_ramp {};
        float m_hold {};
        char* m_duration;

        //constants
        static constexpr int microstepping {16};
        static constexpr int stepsPerRev {200 * microstepping};
        static constexpr int gearRatio {2};
        static constexpr float screwPitch {2.54f};
        static constexpr float l0 {10.0f}; // the initial distance when the stretch is 0%, in mm
        
        static constexpr int checkInterval {1000000}; // check interval to call esp_timer_get_time() to stop a task

        long current_position {0};
        int min_steps;
        int max_steps;
        int total_steps;
        float sps;

        //timer
        uint64_t durationMicros;
        uint64_t previousMicros;
        uint64_t microsBetweenSteps;
        uint64_t taskStartTime;
        uint64_t taskEndTime;
        uint64_t taskPauseTime;

        bool forward = true;
        bool isPaused = false;
        bool isRunning = false;

        void set_sps();
        int stretch_to_absolute_steps(float stretch);
        void calculate_durationMicros();

        void run_ramp();
        void run_cyclic();
        void run_cyclicRamp();
        void run_holdUp();
        void run_holdDown();
        void singleStep();
        void stepperGoTo(int position);

        // RTOS
        void startRTOS(int mode);
        static void emitPosition(void* param);
        static void taskFunction(void* param);
        TaskHandle_t m_taskHandle = nullptr;
        TaskHandle_t m_positionHandle = nullptr;

        struct TaskParam
        {
            Task* instance;
            int mode;
        };

};

#endif
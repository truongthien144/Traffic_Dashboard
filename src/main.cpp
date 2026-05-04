#include <Arduino.h>
#include <TM1637Display.h>

// ================= CONFIG =================
#define UART_BAUD 115200

// ================= TM1637 =================
#define CLK1 18
#define DIO1 19
#define CLK2 21
#define DIO2 22

TM1637Display displayMain(CLK1, DIO1);
TM1637Display displayCross(CLK2, DIO2);

// ================= LED =================
#define LED_MAIN_GREEN   2
#define LED_MAIN_YELLOW  4
#define LED_MAIN_RED     5

#define LED_CROSS_GREEN  12
#define LED_CROSS_YELLOW 13
#define LED_CROSS_RED    14

// ================= DATA =================
typedef struct {
    int M;
    int C;
    int Y;
} TrafficData_t;

QueueHandle_t xQueue;

// ================= STATE =================
typedef enum {
    PHASE_MAIN_RED_GREEN,
    PHASE_MAIN_RED_YELLOW,
    PHASE_MAIN_GREEN,
    PHASE_MAIN_YELLOW
} TrafficState_t;

// ================= DISPLAY =================
void showMain(int num) {
    displayMain.showNumberDec(constrain(num, 1, 99), true);
}
void showCross(int num) {
    displayCross.showNumberDec(constrain(num, 1, 99), true);
}

// ================= LED =================
void setMainLight(int r, int y, int g) {
    digitalWrite(LED_MAIN_RED, r);
    digitalWrite(LED_MAIN_YELLOW, y);
    digitalWrite(LED_MAIN_GREEN, g);
}
void setCrossLight(int r, int y, int g) {
    digitalWrite(LED_CROSS_RED, r);
    digitalWrite(LED_CROSS_YELLOW, y);
    digitalWrite(LED_CROSS_GREEN, g);
}

// ================= UART =================
void TaskUART(void *pvParameters) {
    static char buffer[64];
    int index = 0;

    static TrafficData_t lastSent = {0,0,0};

    while (1) {
        while (Serial.available()) {
            char c = Serial.read();

            if (c == '\n') {
                buffer[index] = '\0';

                int M=0, C=0;
                if (sscanf(buffer, "M:%d|C:%d", &M, &C) == 2) {

                    if (M > C && C > 0 && (M - C) > 1) {

                        TrafficData_t data;
                        data.M = M;
                        data.C = C;
                        data.Y = M - C;

                        if (data.M == lastSent.M && data.C == lastSent.C) {
                            Serial.println("[SKIP - SAME DATA]");
                        } else {
                            xQueueSend(xQueue, &data, portMAX_DELAY);
                            lastSent = data;
                            Serial.println("[OK - NEW DATA]");
                        }

                    } else {
                        Serial.println("[INVALID LOGIC]");
                    }

                } else {
                    Serial.println("[PARSE FAIL]");
                }

                index = 0;
            } else {
                if (index < sizeof(buffer)-1) buffer[index++] = c;
                else index = 0;
            }
        }
        vTaskDelay(10 / portTICK_PERIOD_MS);
    }
}

// ================= TRAFFIC =================
void TaskTraffic(void *pvParameters) {

    TrafficState_t state = PHASE_MAIN_RED_GREEN;

    TrafficData_t current = {15, 10, 5};
    TrafficData_t pending;

    bool hasPending = false;
    bool firstUpdateDone = false;

    unsigned long lastTick = millis();
    unsigned long idealTime = lastTick;

    int counter = current.M;
    bool justChanged = true;

    while (1) {

        // ===== NHẬN DATA =====
        TrafficData_t recv;
        if (xQueueReceive(xQueue, &recv, 0) == pdPASS) {
            pending = recv;
            hasPending = true;
            Serial.println("[NEW DATA RECEIVED]");
        }

        // ===== TICK 1s =====
        if (millis() - lastTick >= 1000) {

            lastTick += 1000;
            idealTime += 1000;

            unsigned long now = millis();
            long drift = now - idealTime;

            if (millis() % 2000 < 50) {
                Serial.print("REAL: ");
                Serial.print(now);
                Serial.print(" | IDEAL: ");
                Serial.print(idealTime);
                Serial.print(" | DRIFT: ");
                Serial.println(drift);
            }

            // ===== APPLY DATA (FIX FIRST UPDATE) =====
            if (hasPending && !firstUpdateDone) {
                current = pending;
                hasPending = false;
                firstUpdateDone = true;

                Serial.println("[FIRST UPDATE - SYNC COUNTER]");

                // 🔥 đồng bộ counter theo state hiện tại
                switch (state) {
                    case PHASE_MAIN_RED_GREEN: counter = current.M; break;
                    case PHASE_MAIN_RED_YELLOW: counter = current.Y; break;
                    case PHASE_MAIN_GREEN: counter = current.C; break;
                    case PHASE_MAIN_YELLOW: counter = current.Y; break;
                }
            }

            // ===== STATE MACHINE =====
            switch (state) {

            case PHASE_MAIN_RED_GREEN:
                setMainLight(1,0,0);
                setCrossLight(0,0,1);

                showMain(counter);
                showCross(max(counter - current.Y, 1));

                if (counter == current.Y + 1) {
                    if (hasPending) {
                        current = pending;
                        hasPending = false;
                        Serial.println("[UPDATED BEFORE NEXT PHASE]");
                    }
                    state = PHASE_MAIN_RED_YELLOW;
                    counter = current.Y;
                    justChanged = true;
                }
                break;

            case PHASE_MAIN_RED_YELLOW:
                setMainLight(1,0,0);
                setCrossLight(0,1,0);

                showMain(counter);
                showCross(counter);

                if (counter == 1) {
                    if (hasPending) {
                        current = pending;
                        hasPending = false;
                        Serial.println("[UPDATED BEFORE NEXT PHASE]");
                    }
                    state = PHASE_MAIN_GREEN;
                    counter = current.C;
                    justChanged = true;
                }
                break;

            case PHASE_MAIN_GREEN:
                setMainLight(0,0,1);
                setCrossLight(1,0,0);

                showMain(counter);
                showCross(counter + current.Y);

                if (counter == 1) {
                    if (hasPending) {
                        current = pending;
                        hasPending = false;
                        Serial.println("[UPDATED BEFORE NEXT PHASE]");
                    }
                    state = PHASE_MAIN_YELLOW;
                    counter = current.Y;
                    justChanged = true;
                }
                break;

            case PHASE_MAIN_YELLOW:
                setMainLight(0,1,0);
                setCrossLight(1,0,0);

                showMain(counter);
                showCross(counter);

                if (counter == 1) {
                    if (hasPending) {
                        current = pending;
                        hasPending = false;
                        Serial.println("[UPDATED BEFORE NEXT PHASE]");
                    }
                    state = PHASE_MAIN_RED_GREEN;
                    counter = current.M;
                    justChanged = true;
                }
                break;
            }

            // ===== GIẢM COUNTER =====
            if (!justChanged) {
                if (counter > 1) counter--;
            } else {
                justChanged = false;
            }
        }

        vTaskDelay(10 / portTICK_PERIOD_MS);
    }
}

// ================= SETUP =================
void setup() {
    Serial.begin(UART_BAUD);

    pinMode(LED_MAIN_GREEN, OUTPUT);
    pinMode(LED_MAIN_YELLOW, OUTPUT);
    pinMode(LED_MAIN_RED, OUTPUT);

    pinMode(LED_CROSS_GREEN, OUTPUT);
    pinMode(LED_CROSS_YELLOW, OUTPUT);
    pinMode(LED_CROSS_RED, OUTPUT);

    displayMain.setBrightness(0x0f);
    displayCross.setBrightness(0x0f);

    xQueue = xQueueCreate(5, sizeof(TrafficData_t));

    xTaskCreate(TaskUART, "UART", 4096, NULL, 2, NULL);
    xTaskCreate(TaskTraffic, "TRAFFIC", 4096, NULL, 1, NULL);
}

void loop() {}
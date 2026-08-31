#include <Arduino.h>
#include <TM1637Display.h>
// ========= DHT20 =========
#include <Wire.h>
#include "DHT20.h"
DHT20 dht;
#define DHT_SDA 25
#define DHT_SCL 26

#define ENV_SEND_INTERVAL_MS  10000UL   // gửi mỗi 10 giây
// ================= CONFIG =================
#define UART_BAUD           115200
#define YELLOW_TIME         3

#define TIMEOUT_MS          120000UL     // 2 phút không nhận gói tin hợp lệ → Fallback
#define DEFAULT_M           30
#define DEFAULT_C           30

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
    int M; // Main GREEN time
    int C; // Cross GREEN time
} TrafficData_t;

QueueHandle_t xQueue;

// ================= STATE =================
typedef enum {
    PHASE_MAIN_GREEN_CROSS_RED,
    PHASE_MAIN_YELLOW_CROSS_RED,
    PHASE_MAIN_RED_CROSS_GREEN,
    PHASE_MAIN_RED_CROSS_YELLOW
} TrafficState_t;

// ================= TIMEOUT =================
volatile uint32_t lastValidTick = 0;
volatile bool isFixedMode = true;
portMUX_TYPE muxTimeout = portMUX_INITIALIZER_UNLOCKED;

// ================= DISPLAY =================
void showMain(int num) {
    displayMain.showNumberDec(constrain(num, 1, 9999), true);
}
void showCross(int num) {
    displayCross.showNumberDec(constrain(num, 1, 9999), true);
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

// ================= UART TASK =================
void TaskUART(void *pvParameters) {
    static char buffer[64];
    int index = 0;

    while (1) {
        while (Serial.available()) {
            char c = Serial.read();

            if (c == '\n') {
                buffer[index] = '\0';

                int M = 0, C = 0;
                if (sscanf(buffer, "M:%d|C:%d", &M, &C) == 2) {

                    if (M > 0 && C > 0) {
                        TrafficData_t data = {M, C};
                        xQueueOverwrite(xQueue, &data);  // Keeping New Data

                        // Cập nhật thời điểm nhận hợp lệ
                        portENTER_CRITICAL(&muxTimeout);
                        lastValidTick = xTaskGetTickCount();
                        isFixedMode = false;
                        portEXIT_CRITICAL(&muxTimeout);

                        Serial.println("[NEW DATA OVERWRITE]");
                        Serial.println("[ACK] OK");
                    } else {
                        Serial.println("[INVALID]");
                    }

                } else {
                    Serial.println("[PARSE FAIL]");
                }

                index = 0;
            } else {
                if (index < sizeof(buffer) - 1) buffer[index++] = c;
                else index = 0;
            }
        }
        vTaskDelay(10 / portTICK_PERIOD_MS);
    }
}

// ================= TRAFFIC TASK =================
void TaskTraffic(void *pvParameters) {

    TrafficState_t state = PHASE_MAIN_GREEN_CROSS_RED;

    TrafficData_t current = {30, 30};     // Giống code gốc của bạn
    TrafficData_t pending = current;    // AlwaysKeeping New Data

    int counter = current.M;
    bool justChanged = true;

    unsigned long lastTick = millis();
    unsigned long idealTime = lastTick;

    while (1) {

        // ===== ALWAYS KEEPING NEW DATA (DONT LOSE DATA) =====
        TrafficData_t recv;
        if (xQueueReceive(xQueue, &recv, 0) == pdPASS) {
            pending = recv;
            Serial.println("[SYNC NEW DATA]");
        }

        

        // ===== TIMER 1s =====
        if (millis() - lastTick >= 1000) {
            lastTick += 1000;
            idealTime += 1000;

            unsigned long now = millis();
            long drift = now - idealTime;

            // Console Output to test drift
            // Serial.print("REAL: ");
            // Serial.print(now);
            // Serial.print(" | IDEAL: ");
            // Serial.print(idealTime);
            // Serial.print(" | DRIFT: ");
            // Serial.println(drift);
                // ===== TIMEOUT FALLBACK =====
            portENTER_CRITICAL(&muxTimeout);
            uint32_t nowTick = xTaskGetTickCount();
            bool needFallback = (!isFixedMode) &&
                                ((nowTick - lastValidTick) > pdMS_TO_TICKS(TIMEOUT_MS));
            portEXIT_CRITICAL(&muxTimeout);

            if (needFallback) {
                pending.M = DEFAULT_M;
                pending.C = DEFAULT_C;

                portENTER_CRITICAL(&muxTimeout);
                isFixedMode = true;
                portEXIT_CRITICAL(&muxTimeout);

                Serial.println("[FALLBACK] FIXED-TIME");
            }
            
            switch (state) {

            // ================= MAIN GREEN =================
            case PHASE_MAIN_GREEN_CROSS_RED:
                setMainLight(0, 0, 1);
                setCrossLight(1, 0, 0);

                showMain(counter);
                showCross(counter + YELLOW_TIME);

                if (counter == 1) {
                    state = PHASE_MAIN_YELLOW_CROSS_RED;
                    counter = YELLOW_TIME;
                    justChanged = true;
                }
                break;

            // ================= MAIN YELLOW =================
            case PHASE_MAIN_YELLOW_CROSS_RED:
                setMainLight(0, 1, 0);
                setCrossLight(1, 0, 0);

                showMain(counter);
                showCross(counter);

                if (counter == 1) {
                    state = PHASE_MAIN_RED_CROSS_GREEN;

                    // UPDATE EXACTLY AT GREEN
                    current.C = pending.C;
                    counter = current.C;
                    justChanged = true;
                }
                break;

            // ================= CROSS GREEN =================
            case PHASE_MAIN_RED_CROSS_GREEN:
                setMainLight(1, 0, 0);
                setCrossLight(0, 0, 1);

                showMain(counter + YELLOW_TIME);
                showCross(counter);

                if (counter == 1) {
                    state = PHASE_MAIN_RED_CROSS_YELLOW;
                    counter = YELLOW_TIME;
                    justChanged = true;
                }
                break;

            // ================= CROSS YELLOW =================
            case PHASE_MAIN_RED_CROSS_YELLOW:
                setMainLight(1, 0, 0);
                setCrossLight(0, 1, 0);

                showMain(counter);
                showCross(counter);

                if (counter == 1) {
                    state = PHASE_MAIN_GREEN_CROSS_RED;

                    // UPDATE EXACTLY AT GREEN
                    current.M = pending.M;
                    counter = current.M;
                    justChanged = true;
                }
                break;
            }

            // ===== COUNTDOWN =====
            if (!justChanged) {
                if (counter > 1) counter--;
            } else {
                justChanged = false;
            }
        }

        vTaskDelay(10 / portTICK_PERIOD_MS);
    }
}
// ================= DHT20 TASH =================
void TaskDHT20(void *pvParameters) {
    Wire.begin(DHT_SDA, DHT_SCL);
    dht.begin();
    if (dht.begin() == 0) {
        Serial.println("[DHT] Khởi tạo thất bại!");
    } else {
        Serial.println("[DHT] Khởi tạo thành công");
    }

    while (1) {
        dht.read();
        float temp = dht.getTemperature();
        float humi = dht.getHumidity();
        if (!isnan(temp) && !isnan(humi)) {
            // Gửi về Raspberry Pi
            Serial.print("ENV:T:");
            Serial.print(temp, 1);
            Serial.print("|H:");
            Serial.println(humi, 1);
        } else {
            Serial.println("[DHT] Đọc lỗi");
        }

        vTaskDelay(pdMS_TO_TICKS(ENV_SEND_INTERVAL_MS));
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

    // Queue size = 1 → overwrite realtime
    xQueue = xQueueCreate(1, sizeof(TrafficData_t));

    lastValidTick = xTaskGetTickCount();

    xTaskCreate(TaskUART, "UART", 4096, NULL, 2, NULL);
    xTaskCreate(TaskTraffic, "TRAFFIC", 4096, NULL, 1, NULL);
    xTaskCreate(TaskDHT20, "DHT20", 3072, NULL, 1, NULL);
}

void loop() {}
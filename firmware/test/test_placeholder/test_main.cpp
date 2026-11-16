// Placeholder test so CI has something to run: pio test -e native
// Real tests for src/logic/ (watering rule, failsafes, calibration maths) replace it.

#include <unity.h>

void setUp() {}

void tearDown() {}

void test_placeholder_runs() {
    TEST_ASSERT_EQUAL(2, 1 + 1);
}

int main() {
    UNITY_BEGIN();
    RUN_TEST(test_placeholder_runs);
    return UNITY_END();
}

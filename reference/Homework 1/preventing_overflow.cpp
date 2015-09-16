#include <iostream>
#include <limits>

int main() {
    // Part a
    short boss_health = 32000;
    short heal_amt = 400;
    std::cout << "Healing for " << heal_amt << "\n";
    if (std::numeric_limits<short>::max() - boss_health >= heal_amt) {
        boss_health += heal_amt;
    }
    else {
        std::cout << "No healing the boss to kill it!\n";
    }
    std::cout << "Boss health is " << boss_health << "\n";

    std::cout << "Healing for " << heal_amt << "\n";
    if (std::numeric_limits<short>::max() - boss_health >= heal_amt) {
        boss_health += heal_amt;
    }
    else {
        std::cout << "No healing the boss to kill it!\n";
    }
    std::cout << "Boss health is " << boss_health << "\n";

    // Part b
    double d = 2e5;
    if (d > std::numeric_limits<float>::max()) {
        std::cout << d << " will overflow a float\n";
    }
    else {
        std::cout << d << " won't overflow a float\n";
    }

    d = 1e39;
    if (d > std::numeric_limits<float>::max()) {
        std::cout << d << " will overflow a float\n";
    }
    else {
        float f = static_cast<float>(d);
        std::cout << d << " won't overflow a float, f = " << f << "\n";
    }
    return 0;
}


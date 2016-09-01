#include <iostream>
#include <limits>

int main() {
    int ntests = 0;
    std::cin >> ntests;
    for (int t = 0; t < ntests; ++t) {
        short boss_health = 32000;
        short attack_amt = 0;
        std::cin >> attack_amt;
        std::cout << "Case " << t << ":\n";
        if (attack_amt >= 0) { // heal
            if ((std::numeric_limits<short>::max() - boss_health) >= attack_amt) {
                boss_health += attack_amt;
            }
            else { // overflow
                boss_health = std::numeric_limits<short>::max();
                std::cout << "no healing the boss to kill it!\n";
            }
            std::cout << "boss health is " << boss_health << "\n";
        }
        else if (attack_amt < 0) { // attack
            if (boss_health > -attack_amt) {
                boss_health += attack_amt;
            }
            else {
                boss_health = 0;
            }
            std::cout << "boss health is " << boss_health << "\n";
            if (boss_health == 0) {
                std::cout << "the boss is dead!\n";
            }
        }
    }

    return 0;
}

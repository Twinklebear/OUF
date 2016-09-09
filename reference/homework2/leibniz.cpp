#include <cmath>
#include <iostream>
#include <iomanip>

int main() {
    int ntests;
    std::cin >> ntests;
    for (int t = 0; t < ntests; ++t) {
        int niters;
        std::cin >> niters;
        double pi_over_4 = 0;
        double sign = 1;
        for (int i = 0; i < niters; ++i) {
            pi_over_4 += sign / (2.0 * i + 1.0);
            sign = -sign;
        }
        std::cout << "Case " << t << ":\n";
        std::cout << "Pi estimated as: " << std::fixed << std::setprecision(8)
            << (pi_over_4 * 4) << "\n";
    }

    return 0;
}

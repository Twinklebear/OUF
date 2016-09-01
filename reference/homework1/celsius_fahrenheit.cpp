#include <iostream>

int main() {
    int ntests = 0;
    std::cin >> ntests;
    for (int t = 0; t < ntests; ++t) {
        int fah = 0;
        std::cin >> fah;
        int cel_int = (fah - 32) * 5 / 9;
        double cel_double = (fah - 32.0) * 5.0 / 9.0;
        std::cout << "Case " << t << ":\n";
        std::cout << fah << "F = " << cel_int << "C\n";
        std::cout << fah << "F = " << cel_double << "C\n";
    }

    return 0;
}

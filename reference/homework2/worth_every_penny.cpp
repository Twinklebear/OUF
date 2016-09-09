#include <iostream>
#include <iomanip>

int main() {
    int ntests;
    std::cin >> ntests;
    for (int t = 0; t < ntests; ++t) {
        int nrings;
        std::cin >> nrings;
        double x = 0.25;
        double sum = 0;
        long long xx = 25;
        long long sumsum = 0;

        for (int i = 0; i < nrings; ++i) {
            sum += x + 10 * i;
            sumsum += xx;
            xx += 1000;
        }

        std::cout << "Case " << t << ":\n";
        std::cout << nrings << " rings were sold\n";
        std::cout << std::fixed << std::setprecision(2);
        std::cout << "Bill's program outputs " << sum << "\n";
        std::cout << "The exact profit is    " << (sumsum / 100.0) << "\n";
    }

    return 0;
}

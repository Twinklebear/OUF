#include <iostream>
#include <limits>

int main() {
    int ntests = 0;
    std::cin >> ntests;
    for (int t = 0; t < ntests; ++t) {
        double input = 0;
        std::cin >> input;
        std::cout << "Case " << t << ":\n";
        if (input>std::numeric_limits<float>::max() ||
            input<std::numeric_limits<float>::lowest())
        {
            std::cout << input << " will overflow a float\n";
        }
        else
        {
            std::cout << input << " won't overflow a float, float = "
                      << static_cast<float>(input) << "\n";
        }
    }

    return 0;
}

#include <iostream>

int main() {
	int num_cases = 0;
	std::cin >> num_cases;
	for (int i = 0; i < num_cases; ++i) {
		std::cout << "Case " << i << ":\n";
		int start = 0;
		int total_time = 0;
		int flip_time = 0;
		int flop_time = 0;
		std::cin >> start >> total_time >> flip_time >> flop_time;
		for (int i = start; i < start + total_time; ++i) {
			if (i % flip_time == 0 && i % flop_time == 0)
				std::cout << "flipflop\n";
			else if (i % flip_time == 0)
				std::cout << "flip\n";
			else if (i % flop_time == 0)
				std::cout << "flop\n";
			else
				std::cout << i << "\n";
		}
	}
	return 0;
}


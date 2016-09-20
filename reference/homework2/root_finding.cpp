#include <iostream>
#include <cmath>

double f(const double x){
	return std::pow(x, 5.0) + 6.0 * std::pow(x, 4.0)
		+ 3.0 * std::pow(x, 3.0) - x - 50.0;
}

double f_prime(const double x){
	return -1.0 + 9.0 * std::pow(x, 2.0) + 24.0 * std::pow(x, 3.0) + 5.0 * std::pow(x, 4.0);
}
double relative_error(const double x, const double x_prev) {
	return std::abs((x - x_prev) / x);
}

int main(){
	int num_cases = 0;
	std::cin >> num_cases;
	for (int c = 0; c < num_cases; ++c) {
		std::cout << "Case " << c << ":\n";
		double prev = -1;
		size_t max_iters = 0;
		double epsilon = 0;
		std::cin >> prev >> max_iters >> epsilon;

		double current = prev;
		size_t i = 0;
		double error = epsilon + 1;
		while (error > epsilon && i < max_iters) {
			prev = current;
			current = prev - f(prev) / f_prime(prev);
			++i;
			error = relative_error(current, prev);
		}
		std::cout << "root at x = " << current << " with error "
			<< relative_error(current, prev) << " after " << i << " iterations\n";
	}
	return 0;
}


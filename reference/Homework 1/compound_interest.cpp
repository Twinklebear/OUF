#include <cmath>
#include <iomanip>
#include <iostream>

int main(){
	const double principal = 5e4;
	const double interest_rate = 0.05;
	const double years = 4;
	std::cout << std::fixed << std::setprecision(2)
		<< "Loan value = "
		<< principal * std::pow(1.0 + interest_rate, years) << "\n";
	return 0;
}


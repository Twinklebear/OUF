#include <iostream>
#include <string>

int main(){
	int num_cases = 0;
	std::cin >> num_cases;
	for (int i = 0; i < num_cases; ++i){
		std::cout << "Case " << i << ":\n";
		std::string input;
		std::cin >> input;
		std::cout << "Echo: " << input << "\n";
	}
	return 0;
}


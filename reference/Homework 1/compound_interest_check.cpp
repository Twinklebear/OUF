#include <iostream>
#include <regex>

using namespace std;

int main(int argc, char** argv) {
    string line;
    getline(cin, line);    
    regex reg("Loan value = 60775\\.31");
    smatch match;
    if (regex_match(line, match, reg)) {
        cout << "Case Failed: 0\n";
        cout << "Total Cases: 1\n";
    } else {
        cout << "Case Failed: 1\n";
        cout << "Total Cases: 1\n";
    }
    return 0;
}
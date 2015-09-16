#include <iostream>
#include <regex>
#include <string>
#include <limits>

using namespace std;

void check_line(const string& line, const string& ref_line) {

}

int main() {    
    bool case_1_failed = false;
    string line;
    getline(cin, line);
    if (line != "Healing for 400")  case_1_failed = true;
    getline(cin, line);
    if (line != "Boss health is 32400") case_1_failed = true;
    
    bool case_2_failed = false;
    getline(cin, line);
    if (line != "Healing for 400") case_2_failed = true;
    getline(cin, line);
    if (line != "No healing the boss to kill it!") case_2_failed = true;
    getline(cin, line);
    if (line != "Boss health is 32400") case_2_failed = true;

    bool case_3_failed = false;
    bool case_4_failed = false;
    getline(cin, line);
    regex reg("(.+) (will|won't) overflow a float");
    smatch match;
    if (!regex_match(line, match, reg)) {
        case_3_failed = true;
        case_4_failed = true;
    } else {
        double num = stod(match[0]);
        if (match[1] == "will" && num <= std::numeric_limits<float>::max())
            case_3_failed = true;
        if (match[1] == "won't" && num > std::numeric_limits<float>::max())
            case_4_failed = true;
    }

    int total_failed_cases = 0;
    total_failed_cases += case_1_failed ? 1 : 0;
    total_failed_cases += case_2_failed ? 1 : 0;
    total_failed_cases += case_3_failed ? 1 : 0;
    total_failed_cases += case_4_failed ? 1 : 0;

    cout << "Case Failed: " << total_failed_cases << "\n";
    cout << "Total Cases: 4\n";

    return 0;
}
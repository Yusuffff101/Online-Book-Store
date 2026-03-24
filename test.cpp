#include <iostream> 
#include <cmath> 
#include <vector> 
#include <algorithm> 
#include <numeric> 
#include <sstream> 
#include <limits> 
#include <iomanip> 
 
using namespace std; 
 
// Function to convert 32-bit integer back to dotted-decimal IP 
string int_to_ip_vlsm(unsigned int ip_int) { 
    stringstream ss; 
    ss << ((ip_int >> 24) & 0xFF) << "." 
       << ((ip_int >> 16) & 0xFF) << "." 
       << ((ip_int >> 8) & 0xFF) << "." 
       << (ip_int & 0xFF); 
    return ss.str(); 
} 
 
// Function to find the smallest power of 2 greater than or equal to n 
unsigned int get_next_power_of_2(int n) { 
    if (n <= 0) return 1; 
    unsigned int p = 1; 
    // Check if n is already a power of 2, if so, return n. 
    if ((n > 0) && ((n & (n - 1)) == 0)) return n;  
    while (p < n) p <<= 1; 
    return p; 
} 
 
int main() { 
    // VLSM - Variable Length Subnet Masking 
    cout << "--- VLSM Subnetting with Full Address Details ---\n"; 
    int num_subnets; 
    cout << "Enter the number of subnets to create: "; 
    cin >> num_subnets; 
 
    vector<pair<int, string>> host_requirements(num_subnets); 
    for (int i = 0; i < num_subnets; ++i) { 
        cout << "Enter hosts required for Subnet " << i + 1 << ": "; 
        cin >> host_requirements[i].first; 
        host_requirements[i].second = "Subnet " + to_string(i + 1); 
        // Add 2 for network and broadcast addresses 
        host_requirements[i].first += 2;  
    } 
 
    // Sort in descending order based on the total block size (hosts+2) 
    sort(host_requirements.begin(), host_requirements.end(), [](const auto& a, const auto& b) { 
        return get_next_power_of_2(a.first) > get_next_power_of_2(b.first); 
    }); 
 
    // Start with a large private address space (e.g., 172.16.0.0) 
    unsigned int current_addr = 0xAC100000;  
 
    cout << "\n--- VLSM Address Allocation Results (Starting from 172.16.0.0) ---\n"; 
    cout << left << setw(15) << "Subnet ID"  
         << setw(10) << "Prefix"  
         << setw(20) << "Network Address"  
         << setw(20) << "First Host"  
         << setw(20) << "Last Host"  
         << setw(20) << "Broadcast Address" << endl; 
    cout << setfill('-') << setw(105) << "" << setfill(' ') << endl; 
 
    for (const auto& subnet : host_requirements) { 
        int req_total = subnet.first; 
        unsigned int block_size = get_next_power_of_2(req_total); 
        int prefix = 32 - log2(block_size); 
 
        unsigned int network_addr = current_addr; 
        unsigned int first_host = network_addr + 1; 
        unsigned int broadcast_addr = network_addr + block_size - 1; 
        unsigned int last_host = broadcast_addr - 1; 
 
        cout << left << setw(15) << subnet.second  
             << setw(10) << ("/" + to_string(prefix)) 
             << setw(20) << int_to_ip_vlsm(network_addr)  
             << setw(20) << int_to_ip_vlsm(first_host)  
             << setw(20) << int_to_ip_vlsm(last_host)  
             << setw(20) << int_to_ip_vlsm(broadcast_addr) << endl; 
 
        // Update the starting address for the next subnet 
        current_addr = network_addr + block_size; 
    } 
 
    return 0; 
}

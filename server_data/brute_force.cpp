#include <iostream>
#include <vector>
#include <algorithm>
#include <unordered_set>

#define MOVIE_COUNT 15
#define SERVICE_COUNT 6
#define BUDGET 50

// Name: count_unique_movies
// Param1: subset - the list of subsets for each  service
// Param2: service_movies - the table of movies
// Return: (int) the amount of unique movies
// Desc: Returns the amount of unique movies in subsets of services
int count_unique_movies(const std::vector<int>& subset, int service_movies[SERVICE_COUNT][MOVIE_COUNT]) {
    std::unordered_set<int> unique_movies;
    for (int service : subset) {
        for (int movie = 0; movie < MOVIE_COUNT; ++movie) {
            if (service_movies[service][movie] == 1) {
                unique_movies.insert(movie);
            }
        }
    }
    return unique_movies.size();
}

// Name: get_max_u_movies_brute_force
// Param1: service_movies - The movies in the services
// Param2: service_prices - The price of each services
// Param3: budget - The user's budget
// Return: (int) - The amount of unique movies
// Desc: Returns the amount of unique movies in the list of services using brute force
int get_max_u_movies_brute_force(int service_movies[SERVICE_COUNT][MOVIE_COUNT], int service_prices[SERVICE_COUNT], int budget) {
    int max_unique_movies = 0;

    // Generate all subsets of services
    for (int mask = 0; mask < (1 << SERVICE_COUNT); ++mask) {
        int current_cost = 0;
        std::vector<int> subset;

        // Create the subset for the current mask
        for (int i = 0; i < SERVICE_COUNT; ++i) {
            if (mask & (1 << i)) { // Check if the i-th service is included in this subset
                current_cost += service_prices[i];
                subset.push_back(i);
            }
        }

        // If the subset is within budget, calculate unique movies
        if (current_cost <= budget) {
            int unique_movies = count_unique_movies(subset, service_movies);
            max_unique_movies = std::max(max_unique_movies, unique_movies);
        }
    }
    return max_unique_movies;
}

int main() {
    int service_movies[SERVICE_COUNT][MOVIE_COUNT] = {
        {1, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0},
        {1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 1, 0, 1, 1, 0},
        {1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0},
        {0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 1},
        {1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0},
        {1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 1, 0, 1, 1, 0}
    };
    int service_prices[SERVICE_COUNT] = {11, 14, 6, 3, 10, 7};
    
    int budget = 50;
    int max_movies = get_max_u_movies_brute_force(service_movies, service_prices, budget);
    std::cout << "BRUTE FORCE\nThe maximum number of unique movies within budget (" << budget << ") is: " << max_movies << std::endl;

    return 0;
}

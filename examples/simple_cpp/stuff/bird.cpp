#include <string>
#include <cstdlib>

static std::string birds[] = {
    "Crow",
    "Pigeon",
    "Chicken",
    "Turkey"
};

std::string bird()
{
    return birds[rand() % 4];
}

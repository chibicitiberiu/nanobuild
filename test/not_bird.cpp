#include <string>
#include <cstdlib>

static std::string not_birds[] = {
    "Donkey",
    "Cow",
    "Lion",
    "Guitar"
};

std::string not_bird()
{
    return not_birds[rand() % 4];
}

#include <iostream>
#include "not_bird.hpp"
#include "stuff/bird.hpp"

int main()
{
    std::cout << "Hello world!\n";
    std::cout << "Bird: " << bird() << "\n";
    std::cout << "Not a bird: " << not_bird() << "\n";
    return 0;
}

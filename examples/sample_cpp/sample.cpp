#include <iostream>
#include <vector>
#include <string>
#include <memory>

namespace math {
    class Calculator {
    private:
        std::string name;
        int precision;

    public:
        Calculator(const std::string& n, int p = 2) : name(n), precision(p) {}
        
        virtual ~Calculator() = default;
        
        // Pure virtual function
        virtual double calculate(double a, double b) const = 0;
        
        // Getter methods
        const std::string& getName() const { return name; }
        int getPrecision() const { return precision; }
        
        // Static method
        static void printInfo() {
            std::cout << "Calculator utility class" << std::endl;
        }
    };

    class BasicCalculator : public Calculator {
    public:
        BasicCalculator(const std::string& name) : Calculator(name) {}
        
        double calculate(double a, double b) const override {
            return a + b;
        }
        
        // Method with default parameter
        double multiply(double a, double b = 1.0) const {
            return a * b;
        }
    };
}

// Template function
template<typename T>
T findMax(const std::vector<T>& vec) {
    if (vec.empty()) {
        throw std::runtime_error("Empty vector");
    }
    
    T max_val = vec[0];
    for (const auto& item : vec) {
        if (item > max_val) {
            max_val = item;
        }
    }
    return max_val;
}

// Enum class
enum class Status {
    PENDING,
    PROCESSING,
    COMPLETED,
    ERROR
};

// Struct with methods
struct Point {
    double x, y;
    
    Point(double x_val = 0.0, double y_val = 0.0) : x(x_val), y(y_val) {}
    
    double distance() const {
        return std::sqrt(x * x + y * y);
    }
};

int main() {
    // Smart pointer usage
    auto calc = std::make_unique<math::BasicCalculator>("MyCalc");
    
    std::vector<int> numbers = {1, 5, 3, 9, 2};
    
    try {
        int max_num = findMax(numbers);
        std::cout << "Max: " << max_num << std::endl;
        
        double result = calc->calculate(10.5, 5.2);
        std::cout << "Result: " << result << std::endl;
        
        Point p(3.0, 4.0);
        std::cout << "Distance: " << p.distance() << std::endl;
        
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
    
    return 0;
}
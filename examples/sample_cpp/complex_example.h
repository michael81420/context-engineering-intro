#ifndef COMPLEX_EXAMPLE_H
#define COMPLEX_EXAMPLE_H

#include <memory>
#include <functional>
#include <vector>
#include <string>
#include <unordered_map>
#include <chrono>
#include <any>

// Forward declarations
class DatabaseConnection;
template<typename T> class Repository;

// Abstract base class
class Service {
protected:
    std::shared_ptr<DatabaseConnection> db_conn;
    
public:
    explicit Service(std::shared_ptr<DatabaseConnection> conn);
    virtual ~Service() = default;
    
    // Pure virtual methods
    virtual bool initialize() = 0;
    virtual void cleanup() = 0;
    
    // Template method pattern
    bool start() {
        if (!initialize()) {
            return false;
        }
        return performStartup();
    }
    
private:
    virtual bool performStartup() { return true; }
};

// Template class with specialization
template<typename T>
class DataProcessor {
private:
    std::function<bool(const T&)> validator;
    Repository<T>* repository;
    
public:
    DataProcessor(Repository<T>* repo, std::function<bool(const T&)> val)
        : repository(repo), validator(val) {}
    
    // Template method
    template<typename Predicate>
    std::vector<T> filter(Predicate pred) const;
    
    // Operator overloading
    DataProcessor& operator+=(const T& item);
    
    // Static template method
    template<typename U>
    static std::unique_ptr<DataProcessor<U>> create(Repository<U>* repo);
};

// Template specialization for strings
template<>
class DataProcessor<std::string> {
public:
    bool validateString(const std::string& str) const;
    std::string normalize(const std::string& str) const;
};

// Namespace with nested classes
namespace data {
    namespace storage {
        class Cache {
        public:
            // Nested enum
            enum class CachePolicy {
                LRU,
                FIFO,
                RANDOM
            };
            
            // Nested struct
            struct CacheEntry {
                std::string key;
                std::any value;
                std::chrono::time_point<std::chrono::steady_clock> timestamp;
                
                // Constructor with member initializer list
                CacheEntry(std::string k, std::any v) 
                    : key(std::move(k)), value(std::move(v)), 
                      timestamp(std::chrono::steady_clock::now()) {}
            };
            
        private:
            CachePolicy policy;
            size_t max_size;
            std::unordered_map<std::string, CacheEntry> entries;
            
        public:
            explicit Cache(CachePolicy p = CachePolicy::LRU, size_t size = 1000);
            
            // Const and non-const overloads
            const CacheEntry* get(const std::string& key) const;
            CacheEntry* get(const std::string& key);
            
            // Method with default arguments
            bool put(const std::string& key, std::any value, bool overwrite = true);
            
            // Friend function declaration
            friend std::ostream& operator<<(std::ostream& os, const Cache& cache);
        };
    }
}

// Function pointer typedef
typedef bool (*ValidationFunction)(const void* data, size_t size);

// Modern alias template
template<typename T>
using ProcessorPtr = std::unique_ptr<DataProcessor<T>>;

// Constexpr function
constexpr size_t calculateBufferSize(size_t elements, size_t element_size) {
    return elements * element_size + sizeof(size_t);
}

// Variadic template function
template<typename... Args>
void logMessage(const std::string& format, Args&&... args);

#endif // COMPLEX_EXAMPLE_H
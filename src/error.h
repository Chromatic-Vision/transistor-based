#ifndef ERROR_H_
#define ERROR_H_

#include <stdlib.h>

typedef struct {
	enum {
		RESULT_SUCCESS,
		RESULT_FAILURE
	} result;

	char* error;
} result_t;

// char* result__format(const char* fmt, ...);
char* result__format(const char *file_name, int line_number, const char* fmt, ...);

// #define RESULT(result_, ...) ((result_t){.result = result_, __VA_ARGS__})

#define RESULT(result_, ...) \
	((result_ == RESULT_SUCCESS) ? \
		((result_t){.result = RESULT_SUCCESS}) \
	: \
		((result_t){.result = result_, .error = result__format(__FILE__, __LINE__, __VA_ARGS__)}) \
	)

#define UNWRAP(result_) do {if (result_.result == RESULT_FAILURE) {fprintf(stderr, "result.result == RESULT_FAILURE\nerror:\n%s\n", result_.error); exit(1);}} while (0)

#define RESULT_PRINT(result_) do {fprintf(stderr, "result.result == %s\nerror:\n%s\n", (result_).result == RESULT_FAILURE ? "RESULT_FAILURE" : "RESULT_SUCCESS", (result_).error);} while (0)

#endif // ERROR_H_

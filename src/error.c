#include <stdlib.h>
#include <stdarg.h>
#include <stdio.h>

#include "error.h"

#define BUFFER_SIZE 2048
static char first_buffer[BUFFER_SIZE];
static char second_buffer[BUFFER_SIZE + 128];

char* result__format(const char *file_name, int line_number, const char* fmt, ...) {
	// TODO: you cannot call this more than once

	if (fmt == NULL) {
		fprintf(stderr, "fmt NULL\n");
		return NULL;
	}

	va_list ap;
	va_start(ap, fmt);
	vsnprintf(first_buffer, BUFFER_SIZE, fmt, ap);
	va_end(ap);

	snprintf(second_buffer, sizeof(second_buffer), "%s:%d: %s", file_name, line_number, first_buffer);

	return second_buffer;
}

#include <stdio.h>
#include <errno.h>
#include <stdlib.h>

#include "error.h"

result_t readall(const char *filename, char **result) {
	FILE* fp = fopen(filename, "r");
	if (fp == NULL) {
		return RESULT(RESULT_FAILURE, "error opening file %s", filename);
	}

	size_t buffer_size = 128;
	size_t buffer_idx = 0;
	char *buffer = malloc(buffer_size * sizeof(char));
	if (buffer == NULL) {
		fclose(fp);
		return RESULT(RESULT_FAILURE, "malloc failed");
	}

	size_t amount_read = 0;
	size_t amount_read_total = 0;
	while ((amount_read = fread(&buffer[buffer_idx], sizeof(*buffer), buffer_size - buffer_idx, fp))) {
		amount_read_total += amount_read;
		buffer_idx += amount_read;
		if (buffer_idx+ 1/*for zero termination*/ >= buffer_size) {
			buffer_size <<= 1;
			buffer = realloc(buffer, buffer_size * sizeof(*buffer));
			if (buffer == NULL) {
				return RESULT(RESULT_FAILURE, "realloc failed");
			}
		}
	}

	buffer[amount_read_total] = 0;
	amount_read_total++;

	buffer = realloc(buffer, amount_read_total);
	if (buffer == NULL) {
		fclose(fp);
		return RESULT(RESULT_FAILURE, "realloc failec");
	}

	if (ferror(fp) != 0) {
		free(buffer);
		fclose(fp);
		return RESULT(RESULT_FAILURE, "reading file failed");
	}

	fclose(fp);

	*result = buffer;
	// fprintf(stderr, "read file '%s'\n", *result);

	return RESULT(RESULT_SUCCESS, NULL);
}


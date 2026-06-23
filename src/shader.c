#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#include "glad.h"

#include "error.h"
#include "readall.h"

static const char *shader_folder = "assets/shaders/";

static result_t load_shader(const char *name, const char *extension /* e.g. .vert */, GLenum shader_type, unsigned int *shader_out) {
	char *data = NULL;
	{
		const size_t buffer_size = 1024;
		char *path_buffer = malloc(buffer_size);  // filename buffer
		if (path_buffer == NULL) {
			return RESULT(RESULT_FAILURE, "malloc failed");
		}

		strcpy(path_buffer, shader_folder);
		strcat(path_buffer, name);
		strcat(path_buffer, extension);

		{
			result_t result = readall(path_buffer, &data);
			free(path_buffer);
			if (result.result == RESULT_FAILURE) {
				return result;
			}
		}
	}

	unsigned int shader;
	shader = glCreateShader(shader_type);

	glShaderSource(shader, 1, (const char * const*)&data, NULL);
	glCompileShader(shader);

	{
		int succes;
		glGetShaderiv(shader, GL_COMPILE_STATUS, &succes);

		if (succes == 0) {
			const size_t shader_log_size = 2048;
			char *shader_log = malloc(shader_log_size);
			if (shader_log == NULL) {
				free(data);
				return RESULT(RESULT_FAILURE, "error allocating shader log after shader %s%s failed compiling", name, extension);
			}

			glGetShaderInfoLog(shader, shader_log_size, NULL, shader_log);
			fprintf(stderr, "Compiling shader (%s%s) failed:\n%s\n", name, extension, shader_log);
			return RESULT(RESULT_FAILURE, "Compiling shader failed for shader %s%s:\n%s\n", name, extension, shader_log);
		}
	}

	*shader_out = shader;
	return RESULT(RESULT_SUCCESS, NULL);
}

result_t load_vertex_shader(const char *name, unsigned int *shader) {
	return load_shader(name, ".vert", GL_VERTEX_SHADER, shader);
}
result_t load_fragment_shader(const char *name, unsigned int *shader) {
	return load_shader(name, ".frag", GL_FRAGMENT_SHADER, shader);
}

result_t load_shader_program(const char *vertex_shader_name, const char *fragment_shader_name, GLuint *shader_program) {
	result_t result;

	unsigned int vertex_shader;
	result = load_vertex_shader(vertex_shader_name, &vertex_shader);
	if (result.result == RESULT_FAILURE) {
		return result;
	}

	unsigned int fragment_shader;
	result = load_fragment_shader(fragment_shader_name, &fragment_shader);
	if (result.result == RESULT_FAILURE) {
		return result;
	}

	*shader_program = glCreateProgram();

	glAttachShader(*shader_program, vertex_shader);
	glAttachShader(*shader_program, fragment_shader);
	glLinkProgram(*shader_program);

	{
		int success;
		glGetProgramiv(*shader_program, GL_LINK_STATUS, &success);
		if (success == 0) {
			// TODO: glGetProgram with GL_INFO_LOG_LENGTH
			GLint length;
			glGetProgramiv(*shader_program, GL_INFO_LOG_LENGTH, &length);
			char *log = malloc(length);
			if (log == NULL) {
				return RESULT(RESULT_FAILURE, "allocating buffer failed trying to log error, error size: %d", length);
			}

			glGetProgramInfoLog(*shader_program, length, NULL, log);
			fprintf(stderr, "error linking shaders:\n%s\n", log);

			return RESULT(RESULT_FAILURE, "error linking shaders, output on stderr");
		}
	}

	// we do not need these anymore
	glDeleteShader(vertex_shader);
	glDeleteShader(fragment_shader);

	return RESULT(RESULT_SUCCESS, NULL);
}


#ifndef SHADER_H_
#define SHADER_H_

#include "glad.h"

#include "error.h"

result_t load_vertex_shader(const char *name, GLuint *shader);
result_t load_fragment_shader(const char *name, GLuint *shader);

/* Load vertex shader, fragment shader and link them into a shader object, prints linking errors to stderr */
result_t load_shader_program(const char *vertex_shader_name, const char *fragment_shader_name, GLuint *shader_program);

#endif  // SHADER_H_

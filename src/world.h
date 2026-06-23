#ifndef WORLD_H_
#define WORLD_H_

#include "glad.h"

#include "camera.h"

typedef unsigned int block_pos_t;

typedef unsigned int block_type_t;
typedef unsigned int item_type_t;

struct World {
	// Exponent of 2  e.g. 1024
	block_pos_t size;

	GLuint front_buffer;
	GLuint front_texture;
	GLuint back_buffer;
	GLuint back_texture;

	GLuint render_shader_program;
	GLuint update_shader_program;
	GLuint color_shader_program;

	GLuint vao, vbo;

	int gates_size;
	GLuint gates_texture;
};

/* Returns NULL on failure, binds a different framebuffer. */
struct World *world__new(block_pos_t size, const char *update_fragment_shader_name, const char *render_fragment_shader_name);
void world__free(struct World *);

/* Binds a different framebuffer. Sets *block_type, if mouse_press == 1. Mouse pos is relative to center of screen. */
void world__update(struct World *, struct Camera, int mouse_x, int mouse_y, block_type_t *block_type, int mouse_press);
void world__render(struct World *, struct Camera);

#endif // WORLD_H_

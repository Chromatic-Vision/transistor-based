#include <stdlib.h>
#include <string.h>
#include <stdio.h>

#include "glad.h"

#include "world.h"
#include "shader.h"

static const float plane[] = {
	-1.0, -1.0, 0.0,  0.0, 0.0,
	1.0, -1.0, 0.0,  1.0, 0.0,
	1.0, 1.0, 0.0,  1.0, 1.0,

	-1.0, -1.0, 0.0,  0.0, 0.0,
	-1.0, 1.0, 0.0,  0.0, 1.0,
	1.0, 1.0, 0.0,  1.0, 1.0,
};

struct World *world__new(block_pos_t size, const char *update_fragment_shader_name, const char *render_fragment_shader_name) {
	struct World *world = NULL;
	world = malloc(sizeof(*world));
	if (world == NULL) {
		goto fail;
	}
	memset(world, 0, sizeof(*world));

	world->size = size;

	for (unsigned int i = 0; i < 2; i++) {
		GLuint *buffer = i == 0 ? &world->front_buffer : &world->back_buffer;
		GLuint *texture = i == 0 ? &world->front_texture : &world->back_texture;

		glGenFramebuffers(1, buffer);
		glBindFramebuffer(GL_FRAMEBUFFER, *buffer);

		glGenTextures(1, texture);
		glBindTexture(GL_TEXTURE_2D, *texture);
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8UI, world->size, world->size, 0, GL_RGBA_INTEGER, GL_UNSIGNED_INT, NULL);
		// glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, world->size, world->size, 0, GL_RGB, GL_UNSIGNED_BYTE, NULL);
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER);
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER);
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
		glTexParameterIuiv(GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, (GLuint[]){0.0, 0.0, 0.0});
		// glTexParameterfv(GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, (GLfloat[]){0.0, 0.0, 0.0});
		glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, *texture, 0);
		{
			GLenum status;
			if ((status = glCheckFramebufferStatus(GL_FRAMEBUFFER)) != GL_FRAMEBUFFER_COMPLETE) {
				const char *string;
#define STR_CASE(E) case (E): string = #E; break
				switch (status) {
					STR_CASE(GL_FRAMEBUFFER_UNDEFINED);
					STR_CASE(GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT);
					STR_CASE(GL_FRAMEBUFFER_INCOMPLETE_MISSING_ATTACHMENT);
					STR_CASE(GL_FRAMEBUFFER_INCOMPLETE_DRAW_BUFFER);
					STR_CASE(GL_FRAMEBUFFER_INCOMPLETE_READ_BUFFER);
					STR_CASE(GL_FRAMEBUFFER_UNSUPPORTED);
					STR_CASE(GL_FRAMEBUFFER_INCOMPLETE_MULTISAMPLE);
					STR_CASE(GL_FRAMEBUFFER_INCOMPLETE_LAYER_TARGETS);

					default: string = "Unknown error";
				}
#undef STR_CASE
				// https://registry.khronos.org/OpenGL-Refpages/gl4/html/glCheckFramebufferStatus.xhtml
				fprintf(stderr, "Framebuffer not complete, error: %s, for buffer: %s\n", string, i == 0 ? "front_buffer" : "back_buffer");
				goto fail;
			}
		}

		glViewport(0, 0, world->size, world->size);

		// glClearColor(i == 0 ? 1.0f : 0.0f, 0.0f, 0.0f, 0.0f);
		glClearColor(0.0, 0.0f, 0.0f, 0.0f);
		glClear(GL_COLOR_BUFFER_BIT);
	}

	result_t result;

	GLuint update_shader_program;
	result = load_shader_program("ident", update_fragment_shader_name, &update_shader_program);
	if (result.result == RESULT_FAILURE) {
		RESULT_PRINT(result);
		goto fail;
	}
	world->update_shader_program = update_shader_program;

	GLuint render_shader_program;
	result = load_shader_program("object", render_fragment_shader_name, &render_shader_program);
	if (result.result == RESULT_FAILURE) {
		RESULT_PRINT(result);
		goto fail;
	}
	world->render_shader_program = render_shader_program;

	result = load_shader_program("object", "color", &world->color_shader_program);
	if (result.result == RESULT_FAILURE) {
		RESULT_PRINT(result);
		goto fail;
	}

	glGenVertexArrays(1, &world->vao);
	glBindVertexArray(world->vao);

	glGenBuffers(1, &world->vbo);
	glBindBuffer(GL_ARRAY_BUFFER, world->vbo);
	glBufferData(GL_ARRAY_BUFFER, sizeof(plane), plane, GL_STATIC_DRAW);

	glEnableVertexAttribArray(0);
	glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, sizeof(float) * 5, NULL);
	glEnableVertexAttribArray(1);
	glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, sizeof(float) * 5, (void*)(sizeof(float) * 3));

	return world;

fail:
	if (world != NULL) {
		free(world);
	}
	return NULL;
}

void world__free(struct World *world) {
	glDeleteProgram(world->render_shader_program);
	glDeleteProgram(world->update_shader_program);

	glDeleteFramebuffers(1, &world->front_buffer);
	glDeleteTextures(1, &world->front_texture);
	glDeleteFramebuffers(1, &world->back_buffer);
	glDeleteTextures(1, &world->back_texture);

	glDeleteBuffers(1, &world->vbo);
	glDeleteVertexArrays(1, &world->vao);

	free(world);
}

void world__update(struct World *world, struct Camera camera, int mouse_x, int mouse_y, block_type_t *block_type, int mouse_press) {
	// TODO: allow user to place machines (Draw single point)

	glBindFramebuffer(GL_FRAMEBUFFER, world->back_buffer);
	glViewport(0, 0, world->size, world->size);
	glDisable(GL_DEPTH_TEST);

	// TODO: textures??


	glActiveTexture(GL_TEXTURE0);
	glBindTexture(GL_TEXTURE_2D, world->front_texture);
	glUseProgram(world->update_shader_program);
	glBindVertexArray(world->vao);
	GLuint transform_loc = glGetUniformLocation(world->update_shader_program, "ourTexture");
	if (transform_loc == -1) {
		fprintf(stderr, "could not get our_texture uniform location\n");
	} else {
		glUniform1i(transform_loc, 0);
	}
	transform_loc = glGetUniformLocation(world->update_shader_program, "size");
	if (transform_loc == -1) {
		fprintf(stderr, "could not get our_texture uniform location\n");
	} else {
		glUniform1ui(transform_loc, world->size);
	}
	glDrawArrays(GL_TRIANGLES, 0, 6 * 3);


	if (mouse_press == 1 || mouse_press == 3) {
		block_type_t place = mouse_press == 0 ? *block_type : 0;

		float x = ((float)mouse_x + camera.pos.x) / (float)world->size;
		float y = ((float)mouse_y * -1.0 + camera.pos.y) / (float)world->size;

		glUseProgram(world->color_shader_program);
		struct Matrix matrix = matrix_ident;
		matrix__mult(&matrix, matrix__gen_scale(1.0 / world->size, 1.0 / world->size, 1.0));
		matrix__mult(&matrix, matrix__gen_translate(x, y, 0.0));

		transform_loc = glGetUniformLocation(world->color_shader_program, "transform");
		if (transform_loc == -1) {
			fprintf(stderr, "could not get transform uniform location\n");
		} else {
			glUniformMatrix4fv(transform_loc, 1, GL_TRUE, matrix.matrix);
		}

		transform_loc = glGetUniformLocation(world->color_shader_program, "color");
		if (transform_loc == -1) {
			fprintf(stderr, "could not get color uniform location\n");
		} else {
			glUniform4ui(transform_loc, place, 0, 0, 0);
		}

		printf("Rendering pixel x: %d, y: %d, type: %u\n", mouse_x, mouse_y, *block_type);
		glDrawArrays(GL_TRIANGLES, 0, 6 * 3);
	}


	GLuint buffer_temp = world->back_buffer;
	world->back_buffer = world->front_buffer;
	world->front_buffer = buffer_temp;

	GLuint texture_temp = world->back_texture;
	world->back_texture = world->front_texture;
	world->front_texture = texture_temp;
}
void world__render(struct World *world, struct Camera camera) {
	// TODO: render world
	// printf("world size: %d, front_texture: %u\n", world->size, world->front_texture);

	glActiveTexture(GL_TEXTURE0);
	glBindTexture(GL_TEXTURE_2D, world->front_texture);
	glUseProgram(world->render_shader_program);
	glBindVertexArray(world->vao);
	GLuint transform_loc = glGetUniformLocation(world->render_shader_program, "ourTexture");
	if (transform_loc == -1) {
		fprintf(stderr, "could not get our_texture uniform location\n");
	} else {
		glUniform1i(transform_loc, 0);
	}

	struct Matrix matrix = matrix_ident;
	// object to world
	unsigned int scale = world->size / 2;
	 matrix__mult(&matrix, matrix__gen_scale(scale, scale, scale));

	camera__world_to_clip(camera, &matrix);

	transform_loc = glGetUniformLocation(world->render_shader_program, "transform");
	if (transform_loc == -1) {
		fprintf(stderr, "could not set transform uniform\n");
	} else {
		glUniformMatrix4fv(transform_loc, 1, GL_TRUE, matrix.matrix);
	}
	// camera__set_shader_transform(camera, world->render_shader_program, (struct Vector){0.1, 0.1, 0.0}, (struct Vector){0.0}, 0.0);
	// glDrawArrays(GL_TRIANGLES, 0, 8 * 3);
	glDrawArrays(GL_TRIANGLES, 0, 6 * 3);
}


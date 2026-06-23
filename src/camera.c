#include <stdio.h>
#include <math.h>

#include "glad.h"

#include "matrix.h"
#include "camera.h"

int viewport_width, viewport_height;

static void vector__print(const char *msg, struct Vector v) {
	printf("%s: %f %f %f\n", msg, v.x, v.y, v.z);
}

void camera__move(struct Camera *camera, float x, float y, float z) {
	// TODO: roll
	struct Vector unit_dir = {
		sinf(camera->dir.y) * cosf(camera->dir.x),
		-sinf(camera->dir.x),
		cosf(camera->dir.y) * cosf(camera->dir.x)
	};

	// vector__print("VECTOR_UP", VECTOR_UP);
	// vector__print("camera_dir", camera->dir);
	// vector__print("cross", vector__cross(VECTOR_UP, camera->dir));
	struct Vector x_axis = vector__normalise(vector__cross(VECTOR_UP, unit_dir));
	// vector__print("x_axis", x_axis);
	// vector__print("x_axis", vector__mult(x_axis, x));
	camera->pos = vector__add(camera->pos, vector__mult(x_axis, x));

	struct Vector y_axis = vector__cross(unit_dir, x_axis);
	// vector__print("y_axis", y_axis);
	camera->pos = vector__add(camera->pos, vector__mult(y_axis, y));

	// vector__print("z_axis", camera->dir);
	camera->pos = vector__add(camera->pos, vector__mult(unit_dir, z));
}

void camera__world_to_clip(struct Camera camera, struct Matrix *matrix) {
	// world to view
	matrix__mult(matrix, matrix__gen_translate(-camera.pos.x, -camera.pos.y, -camera.pos.z));
	matrix__mult(matrix, matrix__gen_rotate(0.0, 1.0, 0.0, -camera.dir.y));
	matrix__mult(matrix, matrix__gen_rotate(1.0, 0.0, 0.0, -camera.dir.x));
	matrix__mult(matrix, matrix__gen_rotate(0.0, 0.0, 1.0, -camera.dir.z)); // TODO: proper rotation

	// view to clip
	matrix__mult(matrix, matrix__gen_perspective(3.141 / 4, (double)viewport_width / (double)viewport_height, 0.9f, 2000.0f));
}

// Calculate world pos and set it as the uniform "transform" for shader_program.
void camera__set_shader_transform(struct Camera camera, GLuint shader_program, struct Vector world_pos, struct Vector world_rotation, float world_rotation_amount) {
	struct Matrix matrix = matrix_ident;
	// object to world
	// matrix__mult(&matrix, matrix__gen_scale(1.0 + sin((float)frame / 40.0) / 3.0, 1.0, 1.0));
	// matrix__mult(&matrix, matrix__gen_scale(1.0 + sin((float)frame / 10.0) * 10, 1.0, 1.0));
	matrix__mult(&matrix, matrix__gen_rotate(world_rotation.x, world_rotation.y, world_rotation.z, world_rotation_amount));
	matrix__mult(&matrix, matrix__gen_translate(world_pos.x, world_pos.y, world_pos.z));

	camera__world_to_clip(camera, &matrix);

	unsigned int transform_loc = glGetUniformLocation(shader_program, "transform");
	if (transform_loc == -1) {
		fprintf(stderr, "could not set transform uniform\n");
	} else {
		glUniformMatrix4fv(transform_loc, 1, GL_TRUE, matrix.matrix);
	}
}


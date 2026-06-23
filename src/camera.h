#ifndef CAMERA_H_
#define CAMERA_H_

#include "glad.h"

#include "matrix.h"

extern int viewport_width, viewport_height;

struct Camera {
	struct Vector pos;
	// the camera direction in euler angles
	struct Vector dir;
};

void camera__move(struct Camera *, float x, float y, float z);
void camera__world_to_clip(struct Camera, struct Matrix *);
// Calculate world pos and set it as the uniform "transform" for shader_program.
void camera__set_shader_transform(struct Camera, GLuint shader_program, struct Vector world_pos, struct Vector world_rotation, float world_rotation_amount);

#endif // CAMERA_H_

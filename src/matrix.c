#include <math.h>
#include <stdio.h>

#include "matrix.h"

const struct Matrix matrix_ident = {{
	1.0, 0.0, 0.0, 0.0,
	0.0, 1.0, 0.0, 0.0,
	0.0, 0.0, 1.0, 0.0,
	0.0, 0.0, 0.0, 1.0
}};

struct Matrix matrix__gen_perspective(double fovy, double aspect, double near_plane, double far_plane) {
	double f = 1.0f / tan(fovy / 2);  // cot(a) = 1 / tan(a)

	return (struct Matrix){
		.matrix = {
				f / aspect,	0,	0,	0,
				0,	f,	0,	0,
				0,	0,	(far_plane + near_plane) / (near_plane - far_plane), 2 * far_plane * near_plane / (near_plane - far_plane),
				0,	0,	-1,	0
		}
	};
}

struct Matrix matrix__gen_rotate(double x, double y, double z, double angle) {
	return (struct Matrix){
		.matrix = {
			cos(angle) + (x*x) * (1.0f - cos(angle)), x * y * (1.0f - cos(angle)) - z * sin(angle), x * z * (1.0f - cos(angle)) + y * sin(angle), 0.0,
			y * x * (1.0f - cos(angle)) + z * sin(angle), cos(angle) + (y*y) * (1.0f - cos(angle)), y * z * (1.0f - cos(angle)) - x * sin(angle), 0.0,
			z * x * (1.0f - cos(angle)) - y * sin(angle), z * y * (1.0f - cos(angle)) + x * sin(angle), cos(angle) + (z*z) * (1.0f - cos(angle)), 0.0,
			0.0, 0.0, 0.0, 1.0
		}
	};
}
struct Matrix matrix__gen_translate(double x, double y, double z) {
	return (struct Matrix){
		.matrix = {
			1, 0, 0, x,
			0, 1, 0, y,
			0, 0, 1, z,
			0, 0, 0, 1
		}
	};
}
struct Matrix matrix__gen_scale(double x, double y, double z) {
	return (struct Matrix){
		.matrix = {
			x, 0, 0, 0,
			0, y, 0, 0,
			0, 0, z, 0,
			0, 0, 0, 1
		}
	};
}

void matrix__mult(struct Matrix *ap, struct Matrix b) {
	struct Matrix a = *ap;

	for (unsigned i = 0; i < 4*4; i++) {
		ap->matrix[i] = 0;
	}

	for (unsigned int i = 0; i < 4; i++) {
		for (unsigned int j = 0; j < 4; j++) {
			for (unsigned k = 0; k < 4; k++) {
				ap->matrix[j*4 + i] += a.matrix[k*4 + i] * b.matrix[j*4 + k];
			}
		}
	}
}

void matrix__print(struct Matrix m) {
	for (unsigned int y = 0; y < 4; y++) {
		for (unsigned int x = 0; x < 4; x++) {
			printf("\t%f, ", m.matrix[x + y*4]);
		}
		putchar('\n');
	}
}

const struct Vector VECTOR_UP = {0.0, 1.0, 0.0};
const struct Vector VECTOR_FORWARD = {0.0, 0.0, -1.0};

float vector__length(struct Vector v) {
	return sqrtf(v.x*v.x + v.y*v.y + v.z*v.z);
}
struct Vector vector__normalise(struct Vector v) {
	return vector__div(v, vector__length(v));
}
struct Vector vector__cross(struct Vector a, struct Vector b) {
	return (struct Vector){
		.x = a.y * b.z - a.z * b.y,
		.y = a.z * b.x - a.x * b.z,
		.z = a.x * b.y - a.y * b.x
	};
}
struct Vector vector__mult(struct Vector v, float x) {
	return (struct Vector){
		.x = v.x * x,
		.y = v.y * x,
		.z = v.z * x
	};
}
struct Vector vector__div(struct Vector v, float x) {
	return (struct Vector){
		.x = v.x / x,
		.y = v.y / x,
		.z = v.z / x
	};
}
struct Vector vector__add(struct Vector a, struct Vector b) {
	return (struct Vector){
		.x = a.x + b.x,
		.y = a.y + b.y,
		.z = a.z + b.z,
	};
}


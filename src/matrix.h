#ifndef MATRIX_H_
#define MATRIX_H_

struct Matrix {
	float matrix[16];
};

extern const struct Matrix matrix_ident;

// inspired by https://registry.khronos.org/OpenGL-Refpages/gl2.1/xhtml/gluPerspective.xml
struct Matrix matrix__gen_perspective(double fovy, double aspect, double near_plane, double far_plane);
struct Matrix matrix__gen_rotate(double x, double y, double z, double angle);
struct Matrix matrix__gen_translate(double x, double y, double z);
struct Matrix matrix__gen_scale(double x, double y, double z);

void matrix__mult(struct Matrix *a, struct Matrix b);
void matrix__print(struct Matrix);

struct Vector {
	float x, y, z;
};
extern const struct Vector VECTOR_UP;
extern const struct Vector VECTOR_FORWARD;

struct Vector matrix__apply(struct Matrix, struct Vector);

float vector__length(struct Vector);
struct Vector vector__normalise(struct Vector);
struct Vector vector__cross(struct Vector, struct Vector);
struct Vector vector__mult(struct Vector, float);
struct Vector vector__div(struct Vector v, float x);
struct Vector vector__add(struct Vector, struct Vector);

#endif // MATRIX_H_


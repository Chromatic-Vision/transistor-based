#version 330 core
out vec4 FragColor;

in vec3 world_coord;

uniform uint age;

void main() {
	// if (age < 100u) {
	// 	FragColor = vec4(1.0, 0.0, 0.0, 1.0);
	// } else {
		FragColor = vec4(mod(world_coord.y, 10.0) / 10.0, 0.5f, 0.2f + sin(6.283185 * world_coord.x), 1.0f);
	// }
}


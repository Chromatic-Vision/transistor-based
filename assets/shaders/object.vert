#version 330 core
layout (location = 0) in vec3 aPos;
layout (location = 1) in vec2 aTexCoord;

uniform mat4 transform;

out vec3 world_coord;
out vec2 tex_coord;

void main () {
	world_coord = aPos;
	tex_coord = aTexCoord;
	gl_Position = transform * vec4(aPos, 1.0);
	// gl_Position = vec4(aPos, 1.0);
}


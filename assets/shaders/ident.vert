#version 330 core
layout (location = 0) in vec3 aPos;
layout (location = 1) in vec2 aTexCoord;

out vec2 tex_coord;

void main () {
	tex_coord = aTexCoord;
	gl_Position = vec4(aPos.x, aPos.y, aPos.z, 1.0);
}

#version 330 core
out vec4 FragColor;

in vec3 world_coord;
in vec2 tex_coord;

uniform usampler2D ourTexture;

void main() {
	// FragColor = vec4(mod(tex_coord.x, 0.01) * 100.0, 0.5f, 0.2f, 1.0f);
	// FragColor = texture(ourTexture, tex_coord) + vec4(mod(tex_coord.x, 0.01) * 50.0, 0.0, 0.0, 0.0);
	FragColor = vec4(texture(ourTexture, tex_coord)) / vec4(255.0);
}

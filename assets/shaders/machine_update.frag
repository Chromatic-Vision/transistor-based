#version 330 core
out uvec4 FragColor;

in vec2 tex_coord;

uniform usampler2D ourTexture;
uniform uint size;

void main() {
	// FragColor = texture(ourTexture, tex_coord) + vec4(1.0f, 0.5f, 0.2f, 1.0f);
	// FragColor = mod(texture(ourTexture, tex_coord) + vec4(tex_coord.x * 0.02, tex_coord.y * 0.02, 0.0, 0.0), vec4(1.0));
	// FragColor = texture(ourTexture, tex_coord) + ivec4(tex_coord.x * 10.0, tex_coord.y * 11.0, 0.0, 0.0);

	ivec2 pos = ivec2(tex_coord * float(size));
	uvec4 c = (texelFetch(ourTexture, pos, 0) + uvec4(pos.x / 100, 2, 0, 0));
	FragColor = uvec4(c.rg, uint(pos.y * 255) / size, c.a) % uvec4(255);
	// FragColor = uvec4(0, 0, uint(pos.y * 255) / size, 0) % uvec4(255);
	// FragColor = texelFetch(ourTexture, pos, 0);
}

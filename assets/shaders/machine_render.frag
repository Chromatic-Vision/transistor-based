#version 330 core
out vec4 FragColor;

in vec3 world_coord;
in vec2 tex_coord;

uniform usampler2D ourTexture;
uniform sampler2D gates_texture;

// TODO: Be aware of the border and render multiple gates there

// TODO: Make these uniforms
const uint border_size = 4u;
const uint gate_size = 120u + border_size * 2u;
const uint world_size = 1024u;
const uint gates_amount = 6u;

const float gate_scale = float(gate_size - border_size * 2u) / float(gate_size);

void main() {
	// FragColor = vec4(mod(tex_coord.x, 0.01) * 100.0, 0.5f, 0.2f, 1.0f);
	// FragColor = texture(ourTexture, tex_coord) + vec4(mod(tex_coord.x, 0.01) * 50.0, 0.0, 0.0, 0.0);
	// FragColor = vec4(texture(ourTexture, tex_coord)) / vec4(255.0);

	// TODO: Use texelFetch instead of texture here
	uvec4 machine = texture(ourTexture, tex_coord);
	uint t = (machine.x < 127u) ? 0u : 1u;
	// uint t = 0u;
	vec4 machine_frag = vec4(texture(
				gates_texture,
				(fract(tex_coord * vec2(world_size)) * gate_scale + (float(border_size) / float(gate_size))  // Coordinate within gate texture
				+ vec2(float(t), 0.0))  // Pick the gate texture
				/ vec2(gates_amount, 1.0)
	));

	// FragColor = vec4(machine_frag.r, (vec4(texture(ourTexture, tex_coord)) / vec4(255.0) * vec4(0.0, 1.0, 1.0, 0.0)).yzw);
	FragColor = machine_frag;
	// FragColor = vec4(texture(gates_texture, fract(tex_coord)));
}

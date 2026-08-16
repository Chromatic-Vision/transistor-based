#include <stdio.h>
#include <pthread.h>

#include "glad.h"

#include <SDL2/SDL.h>
#include <SDL2/SDL_opengl.h>

#include "error.h"
#include "shader.h"
#include "matrix.h"
#include "camera.h"
#include "world.h"

long unsigned int frame = 0;
static const float min_zoom = 1.0;
struct Camera camera = {
	.dir = {0.0},
	.pos = {0.0, 0.0, min_zoom}
};

float vertices[] = {
	 0.0f,  0.0f, 0.0f,
	 1.0f,  0.0f, 0.0f,
	 0.0f,  1.0f, 0.0f,

	 1.0f,  0.0f, 0.0f,
	 1.0f,  1.0f, 0.0f,
	 0.0f,  1.0f, 0.0f
};

void log_callback(GLenum source,
                     GLenum type,
                     GLuint id,
                     GLenum severity,
                     GLsizei length,
                     const GLchar* message,
                     const void* userParam)
{
	(void) source;
	(void) id;
	(void) length;
	(void) userParam;
	fprintf(stderr, "GL CALLBACK: %s type = 0x%x, severity = 0x%x, message = %s\n",
	        (type == GL_DEBUG_TYPE_ERROR ? "** GL ERROR **" : ""),
	        type, severity, message);
}

int main() {
	// struct Matrix matrix = matrix__gen_rotate(1.0 / 14.0, 2.0 / 14.0, 3.0 / 14.0, 1.0);
	// matrix__mult(&matrix, matrix__gen_translate(1.0, 2.0, 3.0));
	// matrix__mult(&matrix, matrix__gen_perspective(1.2, 2.0, 2.0, 100.0));

	// printf("Matrix:\n");
	// matrix__print(matrix);

	// struct Matrix inverse = matrix__inverse(matrix, 1e-4);
	// printf("\nInverse:\n");
	// matrix__print(inverse);

	// printf("\nMatrix * inverse:\n");
	// struct Matrix a = matrix;
	// matrix__mult(&a, inverse);
	// matrix__print(a);

	// printf("\nInverse * matrix:\n");
	// a = inverse;
	// matrix__mult(&a, matrix);
	// matrix__print(a);

	// struct Matrix matrix = matrix_ident;
	// unsigned int scale = 500;
	// matrix__mult(&matrix, matrix__gen_scale(scale, scale, scale));
	// camera__world_to_clip(camera, &matrix);
	// matrix = matrix__inverse(matrix, 1e-4);

	// matrix__apply(matrix, (struct Vector){.x = 300.0, .y = 300.0})

	// return 0;

	if (SDL_Init(SDL_INIT_VIDEO) != 0) {
		fprintf(stderr, "failed to initialize SDL2: %s\n", SDL_GetError());
		return EXIT_FAILURE;
	}

	printf("Platform:        %s\n", SDL_GetPlatform());
	printf("CPU Count:       %d\n", SDL_GetCPUCount());
	printf("System RAM:      %d MB\n", SDL_GetSystemRAM());
	printf("Supports SSE:    %s\n", SDL_HasSSE() ? "true" : "false");
	printf("Supports SSE2:   %s\n", SDL_HasSSE2() ? "true" : "false");
	printf("Supports SSE3:   %s\n", SDL_HasSSE3() ? "true" : "false");
	printf("Supports SSE4.1: %s\n", SDL_HasSSE41() ? "true" : "false");
	printf("Supports SSE4.2: %s\n", SDL_HasSSE42() ? "true" : "false");

	SDL_GL_SetAttribute(SDL_GL_RED_SIZE, 8);
	SDL_GL_SetAttribute(SDL_GL_GREEN_SIZE, 8);
	SDL_GL_SetAttribute(SDL_GL_GREEN_SIZE, 8);
	SDL_GL_SetAttribute(SDL_GL_BLUE_SIZE, 8);

	SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 3);
	SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, 3);
	SDL_GL_SetAttribute(SDL_GL_CONTEXT_PROFILE_MASK, SDL_GL_CONTEXT_PROFILE_CORE);

	SDL_Window* window = SDL_CreateWindow(
			"ogl...",
			SDL_WINDOWPOS_CENTERED,
			SDL_WINDOWPOS_CENTERED,
			800,
			800,
			SDL_WINDOW_OPENGL | SDL_WINDOW_RESIZABLE
	);
	if (window == NULL) {
		fprintf(stderr, "failed to create SDL2 window: %s\n", SDL_GetError());
		SDL_Quit();
		return EXIT_FAILURE;
	}

	SDL_GLContext context = SDL_GL_CreateContext(window);
	if (context == NULL) {
		fprintf(stderr, "failed to create OpenGL context: %s\n", SDL_GetError());
		SDL_DestroyWindow(window);
		SDL_Quit();
		return EXIT_FAILURE;
	}

	{
		int version = gladLoadGLLoader(SDL_GL_GetProcAddress);
		if (version == 0) {
			fprintf(stderr, "error initializing glad\n");
			SDL_GL_DeleteContext(context);
			SDL_DestroyWindow(window);
			SDL_Quit();
			return EXIT_FAILURE;
		}
	}

	printf("OpenGL Vendor:   %s\n", glGetString(GL_VENDOR));
	printf("OpenGL Renderer: %s\n", glGetString(GL_RENDERER));
	printf("OpenGL Version:  %s\n", glGetString(GL_VERSION));
	printf("GLSL Version:    %s\n", glGetString(GL_SHADING_LANGUAGE_VERSION));

	SDL_GL_SetSwapInterval(1 /* vsync */);

	{
		int width, height;
		SDL_GetWindowSizeInPixels(window, &width, &height);
		glViewport(0, 0, width, height);
	}


	unsigned int VAO;
	glGenVertexArrays(1, &VAO);
	glBindVertexArray(VAO);

	unsigned int VBO;
	glGenBuffers(1, &VBO);
	glBindBuffer(GL_ARRAY_BUFFER, VBO);	
	glBufferData(GL_ARRAY_BUFFER, sizeof(vertices), vertices, GL_STATIC_DRAW);

	glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, sizeof(float) * 3, NULL);
	glEnableVertexAttribArray(0);

	unsigned int shader_program; {
		unsigned int vertex_shader;
		UNWRAP(load_vertex_shader("object", &vertex_shader));
		unsigned int fragment_shader;
		UNWRAP(load_fragment_shader("orange", &fragment_shader));

		shader_program = glCreateProgram();

		glAttachShader(shader_program, vertex_shader);
		glAttachShader(shader_program, fragment_shader);
		glLinkProgram(shader_program);

		{
			int success;
			glGetProgramiv(shader_program, GL_LINK_STATUS, &success);
			if (success == 0) {
				char log[2048];
				glGetProgramInfoLog(shader_program, sizeof(log), NULL, log);
				fprintf(stderr, "error linking shaders:\n%s\n", log);

				SDL_GL_DeleteContext(context);
				SDL_DestroyWindow(window);
				SDL_Quit();
				return EXIT_FAILURE;
			}
		}

		// we do not need these anymore
		glDeleteShader(vertex_shader);
		glDeleteShader(fragment_shader);
	}

	struct World *world = world__new(1024, "machine_update", "machine_render");

#define REBIND_FRAMEBUFFER glBindFramebuffer(GL_FRAMEBUFFER, 0); glViewport(0, 0, viewport_width, viewport_height)
	REBIND_FRAMEBUFFER;

	// glPolygonMode(GL_FRONT_AND_BACK, GL_LINE);
	// glEnable(GL_DEPTH_TEST);
	if (GLAD_GL_KHR_debug) {
		glEnable(GL_DEBUG_OUTPUT);
		glDebugMessageCallback(log_callback, 0);
	} else {
		fprintf(stderr, "WARNING: logging not available\n");
	}

	int run = 1;
	const uint8_t *keys = SDL_GetKeyboardState(NULL);
	SDL_GetWindowSizeInPixels(window, &viewport_width, &viewport_height);
	while (run) {
		// SDL_Delay(1000/60); // TODO

		// unsigned long start_ticks = SDL_GetPerformanceCounter();

		SDL_Event event;
		while (SDL_PollEvent(&event)) {
			switch (event.type) {
				case (SDL_QUIT): {
					run = 0;
				} break;
				case (SDL_WINDOWEVENT): {
					if (event.window.event == SDL_WINDOWEVENT_SIZE_CHANGED) {
						viewport_width = event.window.data1, viewport_height = event.window.data2;
						printf("resize to %d %d\n", viewport_width, viewport_height);
						glViewport(0, 0, viewport_width, viewport_height);
					}
				} break;
			}
		}

		// static float camera_speed = 0.2;
		float camera_speed = camera.pos.z / 50.0;
		if (keys[SDL_SCANCODE_S]) {
			camera__move(&camera, 0, -camera_speed, 0);
		}
		if (keys[SDL_SCANCODE_W]) {
			camera__move(&camera, 0, camera_speed, 0);
		}

		if (keys[SDL_SCANCODE_D]) {
			camera__move(&camera, camera_speed, 0, 0);
		}
		if (keys[SDL_SCANCODE_A]) {
			camera__move(&camera, -camera_speed, 0, 0);
		}

		static float zoom_speed = 1.0;  // 0.3
		if (keys[SDL_SCANCODE_F]) {
			camera__move(&camera, 0, 0, zoom_speed);
		}
		if (keys[SDL_SCANCODE_R]) {
			camera__move(&camera, 0, 0, -zoom_speed);
			if (camera.pos.z < min_zoom) {
				camera.pos.z = min_zoom;
			}
		}

		// printf("camera position: %f %f %f\n", camera.pos.x, camera.pos.y, camera.pos.z);

		glClearColor(0.2f, 0.3f, 0.3f, 1.0f);
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

		glUseProgram(shader_program);
		camera__set_shader_transform(camera, shader_program, (struct Vector){0.0, 0.0, 0.0}, (struct Vector){0.0, 0.0, 1.0}, (float)frame / 60.0);

		glBindVertexArray(VAO);
		glDrawArrays(GL_TRIANGLES, 0, sizeof(vertices) / sizeof(*vertices));

		{
			int mouse_x, mouse_y;
			unsigned int mouse_press = SDL_GetMouseState(&mouse_x, &mouse_y);
			int press = 0;
			for (unsigned int i = 1; i <= 3; i++) {
				if (mouse_press & SDL_BUTTON(i)) {
					press = i;
					break;
				}
			}
			block_type_t machine_type = 1;
			// world__update(world, camera, mouse_x - viewport_width / 2, mouse_y - viewport_height / 2, &machine_type/*TODO: block selection*/, press);
			world__update(world, camera, ((float)mouse_x / viewport_width - 0.5) * 2.0, ((float)mouse_y / viewport_height - 0.5) * 2.0, &machine_type/*TODO: block selection*/, press);
		}
		REBIND_FRAMEBUFFER;
		glEnable(GL_DEPTH_TEST);
		world__render(world, camera);

		// TODO: text rendering
		// printf("time took: %lu\n", SDL_GetPerformanceCounter() - start_ticks);

		SDL_GL_SwapWindow(window);
		frame += 1;
	}

	world__free(world);

	SDL_GL_DeleteContext(context);
	SDL_DestroyWindow(window);
	SDL_Quit();

	return 0;
}

TARGET=platform# platform or web

CFLAGS = -Wall -pedantic -std=c99 -pthread
LDFLAGS = -lm -lGL -pthread

BUILD_MARKER = build/$(TARGET).build
DEP = build/
DEPFLAGS = -MT $@ -MMD -MP -MF $(DEP)$*.d

PROJECT = ogl

ifeq (platform, $(TARGET))
	CC = gcc
	EXE ?= $(PROJECT)

	CFLAGS += -ggdb -pipe
	LDFLAGS += -lSDL2 -ggdb
else ifeq (web, $(TARGET))
	CC = emcc
	EXE ?= $(PROJECT).html

	CFLAGS += -s USE_SDL=2 -O2 # -s USE_PTHREADS=1
	LDFLAGS += -s USE_SDL=2 --preload-file mod -s TOTAL_MEMORY=65536000
else
	CC ?= false
	EXE ?= $(PROJECT)
endif

SRCFILES = main.c glad.c shader.c error.c readall.c matrix.c camera.c world.c stb_image.c

OBJFILES = $(addprefix build/, $(patsubst %.c, %.o, $(SRCFILES))) build/gates.png.o
# SHOBJFILES := $(OBJFILES:%.o=%.so)

$(EXE): $(OBJFILES)
	$(CC) $^ -o $@ $(LDFLAGS)

build/glad.o: CFLAGS += -Wno-pedantic
build/%.o: src/%.c Makefile $(BUILD_MARKER) | build
	$(CC) $(DEPFLAGS) $(CFLAGS) -c $< -o $@
# build/glad.o: src/glad.c Makefile $(BUILD_MARKER) | build
# 	$(CC) -MT $@ -MMD -MP -MF build/glad.d $(CFLAGS) -Wno-pedantic -c $< -o $@

build:
	mkdir build

# 120 is the resolution because it is (2 * lcm(2, 3, 6, 10, 12)), all the numbers used in the gate vector graphics
assets/gates.png: assets/gates/ assets/render.py
	cd assets/ && python3 render.py gates.png 120 3
build/gates.png.o: assets/gates.png
	ld -r -b binary -o $@ $<

$(BUILD_MARKER): | build
	rm -fv build/*.build
	touch $(BUILD_MARKER)

.PHONY: full
full: clean $(EXE)

.PHONY: clean
clean:
	rm -fv $(OBJFILES)
	rm -fv assets/gates.png
	rm -frv build
	rm -fv $(EXE)*

DEPFILES := $(OBJFILES:%.o=%.d)
include $(wildcard $(DEPFILES))


#version 330 core
out uvec4 FragColor;

uniform uvec4 color;

void main() {
    FragColor = color;
}

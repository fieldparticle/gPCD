#version 450
#extension GL_ARB_separate_shader_objects : enable
#extension GL_ARB_shading_language_420pack : enable

layout(location = 0) in vec4 fragColor;
layout(location = 0) out vec4 outColor;

void main()
{
    if (fragColor.a <= 0.0)
    {
        discard;
    }

    vec2 point = gl_PointCoord * 2.0 - 1.0;
    float r2 = dot(point, point);
    if (r2 > 1.0)
    {
        discard;
    }

    float alpha = fragColor.a * smoothstep(1.0, 0.0, r2);
    if (alpha <= 0.0)
    {
        discard;
    }

    outColor = vec4(fragColor.rgb, alpha);
}

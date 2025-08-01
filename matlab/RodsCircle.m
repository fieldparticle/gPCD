clc
clear all
close all
num_parts = 8
radius = 0.2
dia = 2*radius
min_C = 8*dia
min_R = (min_C/(2*pi()))*.93
del_theta = min_C/dia
theta = linspace(0, 2*pi(),del_theta)
x = min_R * cos(theta)
y = min_R * sin(theta)
axis('square');
hold on
    
for ii = 1:8
    fprintf("%0.2f:%0.2f\n",x(ii),y(ii))

    PlotParticleCircle(x(ii),y(ii),radius)
end
	ylabel('y (m)');
    xlabel('x (m)');
	hold off
    box on
	grid on
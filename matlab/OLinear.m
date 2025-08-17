% Check linearity of PQB Random

clc
clear all
A = 3.645E-11;
B = 1.401E-4;
for ii = 0:10 
    n = ii*0.25;
    C = A+B;
    if B <= (C+A)*n
        fprintf("B=%6.6e, Upper = %6.6e, Diff = %6.6e, Linear at %d\n",B,(C+A),B-(C+A),n)
        break
    else
        fprintf("B=%6.6e, Upper = %6.6e, Diff = %6.6e, Not Linear at %d\n",B,(C+A),B-(C+A),n)
    end
end


function R = GetDevalleRadius(X)

sec24slp = 0.1;

secx1_beg = 1;
secx1_end = 5;
secz1     = 10;

secx2_beg = 5;
secx2_end = 25;
secz2     = 10;

secx3_beg = 25;
secx3_end = 30;
secz3     = 8.1;


secx4_beg = 30;
secx4_end = 50;
secz4     = 10.0;

secx5_beg = 50;
secz5     = 10.0;

sec2 = (0:1:(secx2_end-secx2_beg))*(-sec24slp);
sec4 = (0:1:(secx4_end-secx4_beg))*(sec24slp);


if(X >= secx1_beg && X < secx1_end)
    R = secz1;
    return;
elseif (X >= secx2_beg && X < secx2_end)
    R = secz2+(X-secx2_beg)*(-sec24slp);
    return;
elseif(X >= secx3_beg && X < secx3_end)
    R = secz3;
    return;
elseif(X >= secx4_beg && X < secx4_end)
    R = secz3+(X-secx3_end)*(sec24slp);
    return;
elseif(X >= secx5_beg)
    R = secz5;
    return;
end

R = 0;

end
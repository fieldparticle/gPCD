clc
clear all
close all
clf
[pfxdrv,pfxdir] = addPathCD('matlab/MPS/main');

plot_type = 1;
do_plot = true;

ary=1;
mcols = 0;
R = 0.20;
mp      = mps();
mp.SetTimeStep(0.001);
mp.SetSystemTemp(250);
% Set the range over which particle properties
% will be calxualted
mp.SetTempRangeLow(1);        % Base temerature low
mp.SetTempRangeHigh(400);        % Base temerature high
% Add the substances.
mp.AddSubstance("He",4.0026022,28,8.3145,-268.9+273.15);
mp.AddSubstance("He2",2*4.0026022,28,8.3145,-268.9+273.15);

pipe_L = 64;
pipe_W = 20;
pipe_H = 20;
Center = 11.0;
Radius = pipe_W/2.0;

st = [];
ct = [];
cz = [];
close all
H = figure(1);
clf
hold on
old_col = 0;
old_row = 0;
for z = 1:1:pipe_L
    old_col = round((pipe_W/2.0)*cos(0)+10);
    old_row = round((pipe_H/2.0)*sin(0)+10);
    Radius = GetDevalleRadius(z);
    for t = 0:pi/100:2*pi-pi/100
        colx = Radius*cos(t)+Center;
        rowy = Radius*sin(t)+Center;
        layer = z;
        if(z == 1)
            st(end+1) = rowy;
            ct(end+1) = colx;
            cz(end+1) = z;
        end
        col = round(colx);
        row = round(rowy);
        
        if(col ~= old_col || row ~= old_row)
            mp.AddParticleBoundary(col,row,layer,...
                                   R,...
                                   round(col),round(row),round(layer));
            old_col = col;
            old_row = row;
        end
    end
    if(z == 1)
        plot3(ct,st,cz,'LineWidth',2,'Color',[0.0,1.0,0.0]);
    end
    ct=[];
    st=[];
    cz=[];
end
mp.ClearBoundaryDups();

totbparts = mp.ptot-1;
%#####################################################
%########################################################################


%run("run_Delavelle001.m")
%run("run_Delavelle002.m")
%run("run_Delavelle003.m")
run("run_Delavelle004.m")

%#########################################################################
%mp.VPLType = mp.VPLTXY;

%mp.VViewAngle = [0,90]; %XY
%mp.VPLType = mp.VPLTXZ;
%mp.VPLType = mp.VPLTYZ;
if 1 %view angle for simple demo
mp.VViewAngle = [-9.6488,-56.1409]
mp.VPLType = mp.VPLTCUSTOM;
end
%mp.VViewAngle = [-39.997172236503850,19.636503856041131]; %ANGLE
pfrm =1;%[876,940];
pto = 6585; %mp.ptot-1;
if do_plot == true
    mp.plotVoxelSideFTOBoundary(  true,... % As points
                                    false,... % number particles
                                                [pipe_W+1,pipe_H+1,pipe_L],... % Cell array boundary
                                                [0.5,0.5,0.5],... %orign
                                                [pipe_W+1,pipe_H+1,0.0,],... %individual cells to draw    
                                                pfrm,...     % array of particles to drae 
                                                pto); % number of paeticle to draw
    hold off
end
fprintf('Total All particles:%d, Total Boundary parts %d, Total non boundary %d,Sidelength %d\r\n',...
mp.ptot-1,totbparts,mp.ptot-1-totbparts,64)

dirFile = sprintf("%s/%s/%s",pfxdrv,"RCCDData","perfdataM");
flnm = "CDNozBoundaryTest";
mp.SaveDataWTSTV2(dirFile,... % directory
                flnm,... % file name without suffix
                pipe_W,...
                pipe_H,...
                pipe_L,...
                Center,...
                Radius,...
                8,...
                128,...
                mp.ptot-1); 

fclose all;
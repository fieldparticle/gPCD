

import struct
import ctypes
import math
from particle import *
class collision:


    def __init__(self):
        self.psource = 0
        self.trg = -1
        self.col_num = 0
        self.col_iter = 0
        self.accel_attract = 0.0
        self.col_flag = False
        self.active = False
        self.vel_mag_in = 0.0
        self.prev_vel_ang = 0.0
        self.vel_ang_acc = 0.0
        self.vel_ang_diff = 0.0
        
        self.orient_ang_in = 0.0
        self.orient_vec_print = []
        self.orient_vec = []
        self.orient_ang = 0.0
        self.orient_ang_area = 0.0
        self.orient_ang_diff = 0.0
        self.prev_orient_ang = 0.0

        self.left_over_mag = 0.0


        self.pred_mom_xout = 0.0
        self.pred_mom_yout = 0.0
        self.col_phase = 0 # 0 no collsion, 1 in collsions, 2 out of collsion
        self.col_pointA = []
        self.col_pointB = []
        self.isec_vect = []
       
        self.prox_len = 0.0
        self.prox_vec = []

        self.cur_area = 0.0
        self.prev_area = 0.0
        self.tot_area = 0.0
        self.area_diff = 0.0
        self.tot_area_diff_out = 0.0
        self.tot_area_diff_in = 0.0
        self.tot_area_diff = 0.0
        

        self.pred_mom_xout = 0.0
        self.pred_mom_yout = 0.0
        self.pred_mom_mag = 0.0
        self.remain_mom = 0.0
        self.internal_mom = 0.0
        self.internal_momx = 0.0
        self.internal_momy = 0.0
        self.stor_tot_area = []
        self.stor_vel_mag_per_area = []
        self.vel_mag_per_area = []

        self.pen_factor =0.0
        self.prev_pf = 0.0
        self.pf_diff = 0.0
        self.tot_pf_in = 0.0
        self.tot_pf_out = 0.0
        self.tot_pf_diff = 0.0
        self.prev_dpf = 0.0
        self.prev_ddpf = 0.0

        self.step = 0
        self.v_coll = 0
        self.v_coll_sum = 0
        self.v_rel = 0.0
        self.tot_collision_y_acc = 0.0
        self.tot_collision_x_acc = 0.0    
        self.tot_collision_acc = 0.0
        self.vx_rel = 0.0
        self.vy_rel = 0.0
        self.line_text = []
        

        self.stor_t     = []
        self.stor_vx    = []
        self.stor_vy    = []
        self.stor_v_mag = []
        self.stor_v_ang = []
        self.stor_v_coll = []
        self.stor_internal_mom = []
        self.stor_internal_momx = []
        self.stor_internal_momy = []
        self.stor_pen_factor = []
        self.stor_tot_collision_x_acc = []
        self.stor_tot_collision_y_acc = []
        self.stor_tot_collision_acc = []
        self.num_cols = 0

        self.stor_vel_mag_in = []
        self.stor_pnum = []
        self.stor_pred_mom_mag = []
        self.stor_pred_mom_xout = []
        self.stor_pred_mom_yout = []
        self.stor_col_count = []
        self.stor_attr = []
        self.stor_cur_area = []
        self.stor_area_diff = []
        self.stor_v_rel = []
        self.stor_vx_rel = []
        self.stor_vy_rel = []
        self.stor_iter = []
        self.stor_col_num = []
        self.stor_prev_vel_ang = []
        self.stor_vel_ang_acc = []
        self.stor_vel_ang_diff = []
        
    def clear_collision(self):
        self.psource = 0       
        self.trg = -1
        self.col_num = 0
        self.accel_attract = 0.0
        self.col_flag = False
        self.active = False
        self.vel_mag_in = 0.0
        self.prev_vel_ang = 0.0
        self.vel_ang_acc = 0.0
        self.vel_ang_diff = 0.0
        self.orient_ang_in = 0.0
        self.pred_mom_xout = 0.0
        self.pred_mom_yout = 0.0
        self.col_phase = 0 # 0 no collsion, 1 in collsions, 2 out of collsion
        self.col_pointA = []
        self.col_pointB = []
        self.isec_vect = []
        self.orient_vec_print = []
        self.orient_vec = []
        self.orient_ang = 0.0
        self.prox_len = 0.0
        self.prox_vec = []
        self.cur_area = 0.0
        self.prev_area = 0.0
        self.tot_area = 0.0
        self.pred_mom_xout = 0.0
        self.pred_mom_yout = 0.0
        self.pred_mom_mag = 0.0
        self.remain_mom = 0.0
        self.internal_mom = 0.0
        self.internal_momx = 0.0
        self.internal_momy = 0.0
        self.stor_tot_area = []
        self.stor_vel_mag_per_area = []
        self.vel_mag_per_area = []
        self.area_diff = 0.0
        self.pen_factor =0.0
        self.prev_pf = 0.0
        self.pf_diff = 0.0
        self.tot_pf_in = 0.0
        self.tot_pf_out = 0.0
        self.tot_pf_diff = 0.0
        self.prev_dpf = 0.0
        self.prev_ddpf = 0.0
        self.step = 0
        self.v_coll = 0
        self.v_coll_sum = 0
        self.v_rel = 0.0
        self.tot_collision_y_acc = 0.0
        self.tot_collision_x_acc = 0.0    
        self.tot_collision_acc = 0.0
        self.vx_rel = 0.0
        self.vy_rel = 0.0
        self.line_text = []
        

        self.stor_t     = []
        self.stor_vx    = []
        self.stor_vy    = []
        self.stor_v_mag = []
        self.stor_v_ang = []
        self.stor_v_coll = []
        self.stor_internal_mom = []
        self.stor_internal_momx = []
        self.stor_internal_momy = []
        self.stor_pen_factor = []
        self.stor_tot_collision_x_acc = []
        self.stor_tot_collision_y_acc = []
        self.stor_tot_collision_acc = []
        self.num_cols = 0

        self.stor_vel_mag_in = []
        self.stor_pnum = []
        self.stor_pred_mom_mag = []
        self.stor_pred_mom_xout = []
        self.stor_pred_mom_yout = []
        self.stor_col_count = []
        self.stor_attr = []
        self.stor_cur_area = []
        self.stor_area_diff = []
        self.stor_v_rel = []
        self.stor_vx_rel = []
        self.stor_vy_rel = []
        self.stor_iter = []
        self.stor_col_num = []
        self.stor_prev_vel_ang = []
        self.stor_vel_ang_acc = []
        self.stor_vel_ang_diff = []